"""VirusTotal API v3 provider.

Supports: IP, domain, file hash, URL.
Requires: VIRUSTOTAL_API_KEY
Free tier: 4 req/min, 500 req/day.
"""

import base64
import logging

import httpx

from app.core.config import settings
from app.enrichment.providers.base import BaseProvider, ProviderResult

logger = logging.getLogger(__name__)

_BASE = "https://www.virustotal.com/api/v3"
_TIMEOUT = 15.0


def _score_from_stats(stats: dict) -> tuple[int, bool, list[str]]:
    """Compute 0-100 score from VT analysis_stats dict."""
    malicious = stats.get("malicious", 0)
    suspicious = stats.get("suspicious", 0)
    harmless = stats.get("harmless", 0)
    undetected = stats.get("undetected", 0)
    total = malicious + suspicious + harmless + undetected
    if total == 0:
        return 0, False, []
    # Malicious counts full weight, suspicious half
    weighted = malicious + (suspicious * 0.5)
    score = int(min((weighted / total) * 100, 100))
    tags: list[str] = []
    if malicious > 0:
        tags.append("vt:malicious")
    if suspicious > 0:
        tags.append("vt:suspicious")
    return score, malicious > 0, tags


class VirusTotalProvider(BaseProvider):
    name = "virustotal"

    def __init__(self) -> None:
        self._api_key = settings.VIRUSTOTAL_API_KEY
        self._enabled = bool(self._api_key)
        if not self._enabled:
            logger.info("VirusTotal: no API key — provider disabled")

    def _headers(self) -> dict:
        return {"x-apikey": self._api_key, "Accept": "application/json"}

    async def _get(self, client: httpx.AsyncClient, url: str) -> dict:
        resp = await client.get(url, headers=self._headers(), timeout=_TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    async def _lookup(self, observable: str, observable_type: str, endpoint: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(observable, observable_type, "no api key")
        try:
            async with httpx.AsyncClient() as client:
                data = await self._get(client, f"{_BASE}/{endpoint}")
            attrs = data.get("data", {}).get("attributes", {})
            stats = attrs.get("last_analysis_stats", {})
            score, malicious, tags = _score_from_stats(stats)
            # Enrich tags with categories / engines if present
            categories = attrs.get("categories", {})
            if categories:
                cat_values = list(set(categories.values()))[:5]
                tags.extend(f"cat:{c}" for c in cat_values)
            return ProviderResult(
                provider=self.name,
                observable=observable,
                observable_type=observable_type,
                score=score,
                malicious=malicious,
                tags=tags,
                raw={
                    "analysis_stats": stats,
                    "reputation": attrs.get("reputation"),
                    "last_analysis_date": attrs.get("last_analysis_date"),
                },
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                return ProviderResult(
                    provider=self.name,
                    observable=observable,
                    observable_type=observable_type,
                    score=0,
                    raw={"status": "not_found"},
                )
            return self._error(observable, observable_type, exc)
        except Exception as exc:
            return self._error(observable, observable_type, exc)

    async def lookup_ip(self, ip: str) -> ProviderResult:
        return await self._lookup(ip, "ip", f"ip_addresses/{ip}")

    async def lookup_domain(self, domain: str) -> ProviderResult:
        return await self._lookup(domain, "domain", f"domains/{domain}")

    async def lookup_hash(self, file_hash: str) -> ProviderResult:
        return await self._lookup(file_hash, "hash", f"files/{file_hash}")

    async def lookup_url(self, url: str) -> ProviderResult:
        url_id = base64.urlsafe_b64encode(url.encode()).rstrip(b"=").decode()
        return await self._lookup(url, "url", f"urls/{url_id}")
