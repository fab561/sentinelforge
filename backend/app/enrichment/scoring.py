"""Threat score aggregation and verdict computation.

Provider weights (must sum to 1.0):
  VirusTotal  40%  — broadest engine coverage, highest signal
  AbuseIPDB   25%  — community-reported abuse, IP-specific
  GreyNoise   20%  — internet scanner/botnet classification
  OTX         15%  — pulse-based IOC correlation

Per-observable strategy: take MAX score across all results for each
provider (worst-case observable wins within a provider).

Final score: weighted average of available providers (missing providers
are excluded from both numerator and denominator — no penalty for
lacking an API key).

Verdict thresholds:
  ≥ 70  → malicious
  ≥ 40  → suspicious
  <  40  → benign
"""

from __future__ import annotations

from app.enrichment.providers.base import ProviderResult

WEIGHTS: dict[str, float] = {
    "virustotal": 0.40,
    "abuseipdb": 0.25,
    "greynoise": 0.20,
    "otx": 0.15,
}

VERDICT_MALICIOUS = 70
VERDICT_SUSPICIOUS = 40


def compute_threat_score(results: list[ProviderResult]) -> int:
    """Weighted average score across available providers.

    Returns 0 if no provider produced a valid result.
    """
    if not results:
        return 0

    # Per-provider max score (across multiple observables)
    provider_max: dict[str, int] = {}
    for r in results:
        if r.available:
            prev = provider_max.get(r.provider, -1)
            if r.score > prev:
                provider_max[r.provider] = r.score

    if not provider_max:
        return 0

    total_weight = sum(WEIGHTS.get(p, 0.0) for p in provider_max)
    if total_weight == 0:
        return 0

    weighted_sum = sum(
        score * WEIGHTS.get(provider, 0.0)
        for provider, score in provider_max.items()
    )
    return int(round(weighted_sum / total_weight))


def compute_verdict(score: int) -> str:
    if score >= VERDICT_MALICIOUS:
        return "malicious"
    if score >= VERDICT_SUSPICIOUS:
        return "suspicious"
    return "benign"


def collect_tags(results: list[ProviderResult]) -> list[str]:
    """Deduplicated union of all tags from available results."""
    seen: set[str] = set()
    tags: list[str] = []
    for r in results:
        if r.available:
            for tag in r.tags:
                if tag not in seen:
                    seen.add(tag)
                    tags.append(tag)
    return tags
