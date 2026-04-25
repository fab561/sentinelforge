"""Threat score aggregation + verdict thresholds + tag dedup."""

from app.enrichment.providers.base import ProviderResult
from app.enrichment.scoring import (
    VERDICT_MALICIOUS,
    VERDICT_SUSPICIOUS,
    collect_tags,
    compute_threat_score,
    compute_verdict,
)


def _r(provider: str, score: int, *, tags: list[str] | None = None,
       observable: str = "1.2.3.4") -> ProviderResult:
    return ProviderResult(
        provider=provider,
        observable=observable,
        observable_type="ip",
        score=score,
        malicious=score >= 70,
        tags=tags or [],
    )


def test_score_zero_when_no_results():
    assert compute_threat_score([]) == 0


def test_score_zero_when_all_unavailable():
    """A provider that errored out (score=-1) must not drag the average down."""
    results = [
        ProviderResult(provider="virustotal", observable="x",
                       observable_type="ip", score=-1, error="no key"),
    ]
    assert compute_threat_score(results) == 0


def test_score_takes_max_per_provider_across_observables():
    """Two observables hitting VT differently → only the worse one counts."""
    results = [_r("virustotal", 30, observable="a"), _r("virustotal", 90, observable="b")]
    # VT alone, weight 1.0 in available set, score = 90
    assert compute_threat_score(results) == 90


def test_score_excludes_missing_providers_from_denominator():
    """One provider available with score 80 → result ~80 (not deflated by missing GreyNoise)."""
    results = [_r("virustotal", 80)]
    assert compute_threat_score(results) == 80


def test_verdict_thresholds_inclusive_at_boundary():
    assert compute_verdict(VERDICT_MALICIOUS) == "malicious"
    assert compute_verdict(VERDICT_MALICIOUS - 1) == "suspicious"
    assert compute_verdict(VERDICT_SUSPICIOUS) == "suspicious"
    assert compute_verdict(VERDICT_SUSPICIOUS - 1) == "benign"
    assert compute_verdict(0) == "benign"


def test_collect_tags_dedups_preserves_order():
    results = [
        _r("virustotal", 50, tags=["tor", "scanner"]),
        _r("abuseipdb",  60, tags=["scanner", "bruteforce"]),  # scanner duplicate
    ]
    tags = collect_tags(results)
    assert tags == ["tor", "scanner", "bruteforce"]


def test_collect_tags_skips_unavailable_providers():
    """A provider that failed must not contribute tags."""
    results = [
        ProviderResult(provider="virustotal", observable="x",
                       observable_type="ip", score=-1, tags=["junk"], error="no key"),
        _r("abuseipdb", 50, tags=["legit"]),
    ]
    assert collect_tags(results) == ["legit"]
