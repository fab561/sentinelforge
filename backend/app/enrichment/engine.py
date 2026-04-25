"""Enrichment engine — orchestrates providers, caches results, builds enrichment dict.

Observable routing:
  ip      → VirusTotal, AbuseIPDB, GreyNoise, OTX
  domain  → VirusTotal, OTX
  hash    → VirusTotal, OTX
  url     → VirusTotal, OTX
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.enrichment.cache import get_cached, set_cached
from app.enrichment.providers.abuseipdb import AbuseIPDBProvider
from app.enrichment.providers.base import BaseProvider, ProviderResult
from app.enrichment.providers.greynoise import GreyNoiseProvider
from app.enrichment.providers.otx import OTXProvider
from app.enrichment.providers.virustotal import VirusTotalProvider
from app.enrichment.scoring import collect_tags, compute_threat_score, compute_verdict

logger = logging.getLogger(__name__)

# Providers per observable type
_PROVIDER_MAP: dict[str, list[str]] = {
    "ip": ["virustotal", "abuseipdb", "greynoise", "otx"],
    "domain": ["virustotal", "otx"],
    "hash": ["virustotal", "otx"],
    "url": ["virustotal", "otx"],
}

# Private IP ranges — skip external lookups
_PRIVATE_PREFIXES = (
    "10.", "172.16.", "172.17.", "172.18.", "172.19.",
    "172.20.", "172.21.", "172.22.", "172.23.", "172.24.",
    "172.25.", "172.26.", "172.27.", "172.28.", "172.29.",
    "172.30.", "172.31.", "192.168.", "127.", "169.254.",
    "::1", "fc00:", "fd", "fe80:",
)


def _is_private_ip(ip: str) -> bool:
    return any(ip.startswith(p) for p in _PRIVATE_PREFIXES)


async def _watchlist_lookup(observables: list[tuple[str, str]]) -> list[dict]:
    """Group observables by type and ask the IOC service for matches."""
    by_type: dict[str, list[str]] = {"ip": [], "domain": [], "hash": [], "url": []}
    for obs_type, value in observables:
        if obs_type in by_type:
            by_type[obs_type].append(value)
    from app.services.ioc_service import lookup_matches
    try:
        return await lookup_matches(by_type)
    except Exception as exc:
        # Watchlist hits are bonus signal — never let a DB hiccup break
        # the rest of the enrichment pipeline.
        logger.warning("watchlist lookup failed: %s", exc)
        return []


def _extract_observables(alert_data: dict) -> list[tuple[str, str]]:
    """Return list of (observable_type, value) pairs from alert observables."""
    obs: dict = alert_data.get("observables") or {}
    pairs: list[tuple[str, str]] = []

    for field, obs_type in (
        ("source_ip", "ip"),
        ("destination_ip", "ip"),
    ):
        val = obs.get(field)
        if val and isinstance(val, str) and val.strip():
            if obs_type == "ip" and _is_private_ip(val.strip()):
                logger.debug("Skipping private IP: %s", val)
                continue
            pairs.append((obs_type, val.strip()))

    for field, obs_type in (
        ("domain", "domain"),
        ("file_hash", "hash"),
        ("url", "url"),
    ):
        val = obs.get(field)
        if val and isinstance(val, str) and val.strip():
            pairs.append((obs_type, val.strip()))

    # Deduplicate preserving order
    seen: set[tuple[str, str]] = set()
    unique: list[tuple[str, str]] = []
    for pair in pairs:
        if pair not in seen:
            seen.add(pair)
            unique.append(pair)
    return unique


class EnrichmentEngine:
    def __init__(self) -> None:
        self._providers: dict[str, BaseProvider] = {
            "virustotal": VirusTotalProvider(),
            "abuseipdb": AbuseIPDBProvider(),
            "greynoise": GreyNoiseProvider(),
            "otx": OTXProvider(),
        }

    async def _lookup_one(
        self,
        provider: BaseProvider,
        obs_type: str,
        value: str,
    ) -> ProviderResult:
        """Run a single provider lookup with cache check."""
        cached = await get_cached(provider.name, obs_type, value)
        if cached is not None:
            logger.debug("Cache hit: %s/%s/%s", provider.name, obs_type, value)
            return ProviderResult(**cached)

        dispatch = {
            "ip": provider.lookup_ip,
            "domain": provider.lookup_domain,
            "hash": provider.lookup_hash,
            "url": provider.lookup_url,
        }
        lookup_fn = dispatch.get(obs_type)
        if lookup_fn is None:
            return provider._skipped(value, obs_type, f"unknown type: {obs_type}")

        result = await lookup_fn(value)

        # Cache available results only
        if result.available:
            from dataclasses import asdict
            await set_cached(provider.name, obs_type, value, asdict(result))

        return result

    async def enrich(self, alert_data: dict) -> dict[str, Any]:
        """Enrich an alert and return the enrichment payload dict.

        Returns a dict ready to be stored in alert.enrichment + computed
        threat_score and verdict.
        """
        observables = _extract_observables(alert_data)
        alert_id = alert_data.get("alert_id", "unknown")

        if not observables:
            logger.info("[%s] No enrichable observables found", alert_id)
            return _empty_enrichment(alert_id)

        # Build tasks: (obs_type, value, provider_name, awaitable) per combo
        tasks: list[tuple[str, str, str, Any]] = []
        for obs_type, value in observables:
            provider_names = _PROVIDER_MAP.get(obs_type, [])
            for pname in provider_names:
                provider = self._providers.get(pname)
                if provider:
                    tasks.append((obs_type, value, pname, self._lookup_one(provider, obs_type, value)))

        # Run all concurrently (bounded by semaphore via settings)
        from app.core.config import settings
        sem = asyncio.Semaphore(settings.ENRICHMENT_CONCURRENT_LIMIT)

        async def bounded(coro: Any) -> ProviderResult:
            async with sem:
                return await coro

        raw_results: list[ProviderResult | BaseException] = await asyncio.gather(
            *[bounded(t[3]) for t in tasks],
            return_exceptions=True,
        )

        all_results: list[ProviderResult] = []
        for i, res in enumerate(raw_results):
            obs_type, value, pname, _ = tasks[i]
            if isinstance(res, BaseException):
                logger.error("[%s] Provider %s/%s/%s raised: %s", alert_id, pname, obs_type, value, res)
                all_results.append(ProviderResult(
                    provider=pname, observable=value, observable_type=obs_type,
                    score=-1, error=str(res),
                ))
            else:
                all_results.append(res)
                if res.error:
                    logger.warning("[%s] %s/%s/%s → error: %s", alert_id, pname, obs_type, value, res.error)

        # IOC watchlist — analyst-curated indicators take precedence over
        # external feeds. A hit injects a synthetic provider result so the
        # existing scoring/tag machinery picks it up; severity drives the
        # score so a "critical" watchlist match alone can fire a playbook.
        watchlist_hits = await _watchlist_lookup(observables)
        for hit in watchlist_hits:
            sev = hit["severity"]
            score = {"critical": 100, "high": 90, "medium": 70, "low": 40}.get(sev, 60)
            tag_set = [f"watchlist:{sev}", f"watchlist:src:{hit['source']}"]
            if hit.get("description"):
                tag_set.append(f"watchlist:note:{hit['description'][:40]}")
            all_results.append(ProviderResult(
                provider="watchlist",
                observable=hit["value"],
                observable_type=hit["ioc_type"],
                score=score,
                malicious=True,
                tags=tag_set,
                raw={"source": hit["source"], "severity": sev},
            ))
            logger.info(
                "[%s] watchlist hit: %s/%s severity=%s",
                alert_id, hit["ioc_type"], hit["value"], sev,
            )

        # Build per-observable breakdown
        obs_breakdown: dict[str, dict] = {}
        for res in all_results:
            key = res.observable
            if key not in obs_breakdown:
                obs_breakdown[key] = {"type": res.observable_type, "providers": {}}
            obs_breakdown[key]["providers"][res.provider] = {
                "score": res.score,
                "malicious": res.malicious,
                "tags": res.tags,
                "error": res.error,
                "raw": res.raw,
            }

        threat_score = compute_threat_score(all_results)
        verdict = compute_verdict(threat_score)
        tags = collect_tags(all_results)

        enrichment = {
            "summary": {
                "threat_score": threat_score,
                "verdict": verdict,
                "tags": tags,
                "observable_count": len(observables),
                "provider_results": len([r for r in all_results if r.available]),
                "enriched_at": datetime.now(timezone.utc).isoformat(),
                "alert_id": alert_id,
            },
            "observables": obs_breakdown,
        }

        logger.info(
            "[%s] Enrichment complete: score=%d verdict=%s observables=%d",
            alert_id, threat_score, verdict, len(observables),
        )
        return {
            "enrichment": enrichment,
            "threat_score": threat_score,
            "verdict": verdict,
        }


def _empty_enrichment(alert_id: str) -> dict[str, Any]:
    return {
        "enrichment": {
            "summary": {
                "threat_score": 0,
                "verdict": "benign",
                "tags": [],
                "observable_count": 0,
                "provider_results": 0,
                "enriched_at": datetime.now(timezone.utc).isoformat(),
                "alert_id": alert_id,
            },
            "observables": {},
        },
        "threat_score": 0,
        "verdict": "benign",
    }
