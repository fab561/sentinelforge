"""AbuseIPDB API v2 provider.

Supports: IP only.
Requires: ABUSEIPDB_API_KEY
Free tier: 1000 checks/day.
"""

import logging

import httpx

from app.core.config import settings
from app.enrichment.providers.base import BaseProvider, ProviderResult

logger = logging.getLogger(__name__)

_BASE = "https://api.abuseipdb.com/api/v2"
_TIMEOUT = 10.0


class AbuseIPDBProvider(BaseProvider):
    name = "abuseipdb"

    def __init__(self) -> None:
        self._api_key = settings.ABUSEIPDB_API_KEY
        self._enabled = bool(self._api_key)
        if not self._enabled:
            logger.info("AbuseIPDB: no API key — provider disabled")

    def _headers(self) -> dict:
        return {"Key": self._api_key, "Accept": "application/json"}

    async def lookup_ip(self, ip: str) -> ProviderResult:
        if not self._enabled:
            return self._skipped(ip, "ip", "no api key")
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{_BASE}/check",
                    headers=self._headers(),
                    params={"ipAddress": ip, "maxAgeInDays": 90, "verbose": ""},
                    timeout=_TIMEOUT,
                )
                resp.raise_for_status()
            body = resp.json().get("data", {})
            score = body.get("abuseConfidenceScore", 0)
            malicious = score >= 50
            tags: list[str] = []
            if body.get("isWhitelisted"):
                tags.append("whitelisted")
                score = 0
                malicious = False
            if body.get("isTor"):
                tags.append("tor")
            country = body.get("countryCode")
            if country:
                tags.append(f"country:{country}")
            isp = body.get("isp")
            if isp:
                tags.append(f"isp:{isp[:30]}")
            return ProviderResult(
                provider=self.name,
                observable=ip,
                observable_type="ip",
                score=score,
                malicious=malicious,
                tags=tags,
                raw={
                    "abuse_confidence_score": score,
                    "total_reports": body.get("totalReports"),
                    "num_distinct_users": body.get("numDistinctUsers"),
                    "last_reported_at": body.get("lastReportedAt"),
                    "isp": isp,
                    "country_code": country,
                    "is_whitelisted": body.get("isWhitelisted"),
                    "usage_type": body.get("usageType"),
                },
            )
        except Exception as exc:
            return self._error(ip, "ip", exc)

    async def lookup_domain(self, domain: str) -> ProviderResult:
        return self._skipped(domain, "domain", "abuseipdb: ip only")

    async def lookup_hash(self, file_hash: str) -> ProviderResult:
        return self._skipped(file_hash, "hash", "abuseipdb: ip only")

    async def lookup_url(self, url: str) -> ProviderResult:
        return self._skipped(url, "url", "abuseipdb: ip only")
