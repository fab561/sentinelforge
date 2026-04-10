"""Normalizes raw Wazuh alerts into the SentinelForge unified alert schema."""

import hashlib
from datetime import datetime, timezone


# Wazuh rule.level -> severity mapping
def _map_severity(level: int) -> str:
    if level >= 12:
        return "critical"
    if level >= 8:
        return "high"
    if level >= 4:
        return "medium"
    return "low"


# Wazuh rule.groups -> category mapping
_CATEGORY_MAP = {
    "authentication_failed": "brute_force",
    "authentication_failures": "brute_force",
    "sshd": "brute_force",
    "invalid_login": "brute_force",
    "web": "web_attack",
    "exploit": "intrusion",
    "rootcheck": "malware",
    "syscheck": "file_integrity",
    "policy": "policy",
    "ids": "intrusion",
    "firewall": "network",
    "ossec": "system",
}


def _map_category(groups: list[str]) -> str:
    for group in groups:
        group_lower = group.lower()
        for key, category in _CATEGORY_MAP.items():
            if key in group_lower:
                return category
    return "uncategorized"


def _generate_alert_id(wazuh_id: str) -> str:
    """Generate a short deterministic alert ID from Wazuh _id."""
    short_hash = hashlib.sha256(wazuh_id.encode()).hexdigest()[:8]
    return f"sf-{short_hash}"


def normalize_wazuh_alert(raw: dict) -> dict:
    """Convert a raw Wazuh alert (from Indexer) to unified schema fields.

    Returns a dict suitable for creating an Alert model instance.
    """
    wazuh_id = raw.get("_id", "")
    rule = raw.get("rule", {})
    data = raw.get("data", {})
    agent = raw.get("agent", {})
    mitre = rule.get("mitre", {})

    # Parse timestamp
    ts_str = raw.get("timestamp", "")
    try:
        timestamp = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        timestamp = datetime.now(timezone.utc)

    # Build observables
    observables = {
        "source_ip": data.get("srcip") or raw.get("data", {}).get("src_ip"),
        "destination_ip": data.get("dstip") or data.get("dst_ip"),
        "source_port": data.get("srcport"),
        "destination_port": data.get("dstport"),
        "username": data.get("srcuser") or data.get("dstuser"),
        "hostname": agent.get("name"),
        "file_hash": data.get("md5") or data.get("sha256"),
        "domain": data.get("hostname"),
        "url": data.get("url"),
        "process_name": data.get("program_name"),
    }
    # Remove None values
    observables = {k: v for k, v in observables.items() if v is not None}

    # Build MITRE info
    mitre_info = None
    if mitre:
        tactics = mitre.get("tactic", [])
        techniques = mitre.get("id", [])
        mitre_info = {
            "tactic": tactics[0] if tactics else None,
            "technique": techniques[0] if techniques else None,
            "subtechnique": techniques[1] if len(techniques) > 1 else None,
        }

    groups = rule.get("groups", [])

    return {
        "alert_id": _generate_alert_id(wazuh_id),
        "timestamp": timestamp,
        "source": "wazuh",
        "source_rule_id": str(rule.get("id", "")),
        "severity": _map_severity(rule.get("level", 0)),
        "category": _map_category(groups),
        "title": rule.get("description", "Unknown Alert"),
        "description": raw.get("full_log", ""),
        "observables": observables,
        "mitre": mitre_info,
        "raw_log": raw.get("full_log"),
        "status": "new",
    }
