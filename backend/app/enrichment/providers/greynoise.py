"""GreyNoise Community API v3 provider.

Supports: IP only.
Requires: GREYNOISE_API_KEY
Free community tier: 100 lookups/day.

Classification mapping:
  malicious  → score 80
  unknown    → score 30
  benign     → score 5
  riot       → score 5  (known benign internet infrastructure)
"""

import logging

import httpx

from app.core.config import settings
from app.enrichment.providers.base import BaseProvider, ProviderResult

logger = logging.getLogger(__name__)

_BASE = "https://api.greynoise.io/v3/community"
_TIMEOUT = 10.0

_CLASSIFICATION_SCORE: dict[str, int] = {
    "malicious": 80,
    "unknown": 30,
    "benign": 5,
}


class GreyNoiseProvider(BaseProvider):
    name = "greynoise"

    def __init__(self) -> None:
        self._api_key = settings.GREYNOISE_API_KEY
        self._enabled = bool(self._api_key)
        if not self._enabled:
            logger.info("GreyNoise: no API key — provider disabled")

    def _headers(self) -> dict:
        return {"key": self._api_key, "Accept": "application/json"}

    async def lookup_ip(self, ip: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(ip, "ip", "no api key")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{_BASE}/{ip}", headers=self._headers(), timeout=_TIMEOUT)

            if resp.status_code == 404:
                # Not in GreyNoise dataset — unknown
                return ProviderResult(
                    provider=self.name,
                    observable=ip,
                    observable_type="ip",
                    score=30,
                    malicious=False,
                    tags=["gn:not_seen"],
                    raw={"status": "not_seen"},
                )
            resp.raise_for_status()
            body = resp.json()

            # RIOT = known benign service (Google, Cloudflare, etc.)
            if body.get("riot"):
                return ProviderResult(
                    provider=self.name,
                    observable=ip,
                    observable_type="ip",
                    score=5,
                    malicious=False,
                    tags=["gn:riot", f"gn:{body.get('name', 'known_service')}"],
                    raw={"riot": True, "name": body.get("name"), "link": body.get("link")},
                )

            classification = body.get("classification", "unknown").lower()
            score = _CLASSIFICATION_SCORE.get(classification, 30)
            malicious = classification == "malicious"
            tags = [f"gn:{classification}"]
            noise = body.get("noise", False)
            if noise:
                tags.append("gn:noise")  # Known internet scanner
            name = body.get("name")
            if name:
                tags.append(f"gn:{name[:30]}")

            return ProviderResult(
                provider=self.name,
                observable=ip,
                observable_type="ip",
                score=score,
                malicious=malicious,
                tags=tags,
                raw={
                    "classification": classification,
                    "noise": noise,
                    "riot": False,
                    "name": name,
                    "link": body.get("link"),
                    "last_seen": body.get("last_seen"),
                },
            )
        except Exception as exc:
            return self._error(ip, "ip", exc)

    async def lookup_domain(self, domain: str) -> ProviderResult:
        return self._skipped(domain, "domain", "greynoise: ip only")

    async def lookup_hash(self, file_hash: str) -> ProviderResult:
        return self._skipped(file_hash, "hash", "greynoise: ip only")

    async def lookup_url(self, url: str) -> ProviderResult:
        return self._skipped(url, "url", "greynoise: ip only")
