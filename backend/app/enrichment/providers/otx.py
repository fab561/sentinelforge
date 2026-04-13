"""AlienVault OTX (Open Threat Exchange) provider.

Supports: IP, domain, file hash, URL.
Requires: OTX_API_KEY (free registration at otx.alienvault.com)
Free tier: generous — no strict rate limit documented.

Score: min(pulse_count * 15, 100)
  — 1 pulse  → 15  (low confidence)
  — 5 pulses → 75  (suspicious/malicious)
  — 7+       → 100 (capped)
"""

import logging
import urllib.parse

import httpx

from app.core.config import settings
from app.enrichment.providers.base import BaseProvider, ProviderResult

logger = logging.getLogger(__name__)

_BASE = "https://otx.alienvault.com/api/v1/indicators"
_TIMEOUT = 15.0


class OTXProvider(BaseProvider):
    name = "otx"

    def __init__(self) -> None:
        self._api_key = settings.OTX_API_KEY
        self._enabled = bool(self._api_key)
        if not self._enabled:
            logger.info("OTX: no API key — provider disabled")

    def _headers(self) -> dict:
        return {"X-OTX-API-KEY": self._api_key, "Accept": "application/json"}

    async def _get(self, url: str, params: dict | None = None) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers(), params=params, timeout=_TIMEOUT)
            resp.raise_for_status()
            return resp.json()

    def _build_result(self, observable: str, observable_type: str, body: dict) -> ProviderResult:
        pulse_info = body.get("pulse_info", {})
        pulse_count = pulse_info.get("count", 0)
        score = min(pulse_count * 15, 100)
        malicious = score >= 40

        tags: list[str] = []
        # Collect tags from related pulses (first 5)
        for pulse in pulse_info.get("pulses", [])[:5]:
            for tag in pulse.get("tags", [])[:3]:
                t = tag.strip().lower()
                if t and t not in tags:
                    tags.append(f"otx:{t}")
        if pulse_count > 0:
            tags.append(f"otx:{pulse_count}_pulses")

        return ProviderResult(
            provider=self.name,
            observable=observable,
            observable_type=observable_type,
            score=score,
            malicious=malicious,
            tags=tags,
            raw={
                "pulse_count": pulse_count,
                "pulses_preview": [
                    {"name": p.get("name"), "created": p.get("created")}
                    for p in pulse_info.get("pulses", [])[:5]
                ],
            },
        )

    async def lookup_ip(self, ip: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(ip, "ip", "no api key")
        try:
            body = await self._get(f"{_BASE}/IPv4/{ip}/general")
            return self._build_result(ip, "ip", body)
        except Exception as exc:
            return self._error(ip, "ip", exc)

    async def lookup_domain(self, domain: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(domain, "domain", "no api key")
        try:
            body = await self._get(f"{_BASE}/domain/{domain}/general")
            return self._build_result(domain, "domain", body)
        except Exception as exc:
            return self._error(domain, "domain", exc)

    async def lookup_hash(self, file_hash: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(file_hash, "hash", "no api key")
        try:
            body = await self._get(f"{_BASE}/file/{file_hash}/general")
            return self._build_result(file_hash, "hash", body)
        except Exception as exc:
            return self._error(file_hash, "hash", exc)

    async def lookup_url(self, url: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(url, "url", "no api key")
        try:
            encoded = urllib.parse.quote(url, safe="")
            body = await self._get(f"{_BASE}/url/{encoded}/general")
            return self._build_result(url, "url", body)
        except Exception as exc:
            return self._error(url, "url", exc)
