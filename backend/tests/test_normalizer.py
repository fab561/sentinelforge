"""Wazuh alert → internal schema normalisation."""

from app.ingestion.normalizer import normalize_wazuh_alert


_DEFAULT_DATA = {"srcip": "1.2.3.4"}
_SENTINEL = object()


def _base(rule_overrides: dict | None = None, data=_SENTINEL) -> dict:
    # `data or default` would coerce an empty dict back to the default —
    # use a sentinel so callers can intentionally pass {}.
    return {
        "id": "abc",
        "timestamp": "2026-04-25T00:00:00Z",
        "rule": {
            "id": "5710",
            "level": 5,
            "description": "ssh fail",
            "groups": ["ssh"],
            **(rule_overrides or {}),
        },
        "agent": {"id": "001", "name": "host"},
        "data": _DEFAULT_DATA if data is _SENTINEL else data,
        "full_log": "log line",
        "location": "/var/log/auth.log",
    }


def test_mitre_subtechnique_split():
    """T1110.003 should normalise to technique=T1110, sub=T1110.003."""
    raw = _base(rule_overrides={"mitre": {"tactic": ["Credential Access"], "id": ["T1110.003"]}})
    out = normalize_wazuh_alert(raw)
    assert out["mitre"]["technique"] == "T1110"
    assert out["mitre"]["subtechnique"] == "T1110.003"
    assert out["mitre"]["tactic"] == "Credential Access"


def test_mitre_parent_technique_no_subtechnique():
    """A bare T1078 has no sub-technique — subtechnique stays None."""
    raw = _base(rule_overrides={"mitre": {"tactic": ["Initial Access"], "id": ["T1078"]}})
    out = normalize_wazuh_alert(raw)
    assert out["mitre"]["technique"] == "T1078"
    assert out["mitre"]["subtechnique"] is None


def test_src_ip_fallback_to_underscore_form():
    """data.src_ip should be honoured when data.srcip is missing."""
    raw = _base(data={"src_ip": "9.9.9.9"})
    out = normalize_wazuh_alert(raw)
    assert out["observables"]["source_ip"] == "9.9.9.9"


def test_observables_dropped_when_none():
    """Empty observables shouldn't pollute the output dict."""
    raw = _base(data={})
    out = normalize_wazuh_alert(raw)
    assert "source_ip" not in out["observables"]


def test_alert_id_prefixed():
    """alert_id should carry the configured prefix."""
    raw = _base()
    out = normalize_wazuh_alert(raw)
    assert out["alert_id"].startswith("sf-")
