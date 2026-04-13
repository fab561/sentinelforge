"""Condition evaluation for playbook matching.

Supports dot-notation field access on alert dicts.
Operators: eq, neq, gt, gte, lt, lte, contains, in, not_in, exists, not_exists
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def _resolve_field(alert_data: dict, field: str) -> Any:
    """Resolve a dot-notation field path from the alert dict.

    Examples:
      "verdict"                        → alert_data["verdict"]
      "threat_score"                   → alert_data["threat_score"]
      "observables.source_ip"          → alert_data["observables"]["source_ip"]
      "enrichment.summary.tags"        → alert_data["enrichment"]["summary"]["tags"]
      "mitre.tactic"                   → alert_data["mitre"]["tactic"]
    """
    parts = field.split(".")
    current: Any = alert_data
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _evaluate_condition(alert_data: dict, condition: dict) -> bool:
    """Evaluate a single condition against alert data. Returns True if matched."""
    field = condition.get("field", "")
    operator = condition.get("operator", "eq").lower()
    expected = condition.get("value")

    actual = _resolve_field(alert_data, field)

    try:
        match operator:
            case "eq":
                return actual == expected
            case "neq":
                return actual != expected
            case "gt":
                return actual is not None and float(actual) > float(expected)
            case "gte":
                return actual is not None and float(actual) >= float(expected)
            case "lt":
                return actual is not None and float(actual) < float(expected)
            case "lte":
                return actual is not None and float(actual) <= float(expected)
            case "contains":
                if actual is None:
                    return False
                if isinstance(actual, (list, str)):
                    return expected in actual
                return False
            case "in":
                if not isinstance(expected, list):
                    return False
                return actual in expected
            case "not_in":
                if not isinstance(expected, list):
                    return True
                return actual not in expected
            case "exists":
                return actual is not None
            case "not_exists":
                return actual is None
            case _:
                logger.warning("Unknown condition operator: %s", operator)
                return False
    except (TypeError, ValueError) as exc:
        logger.warning("Condition eval error [%s %s %s]: %s", field, operator, expected, exc)
        return False


def evaluate_conditions(alert_data: dict, conditions: list[dict], match: str = "all") -> bool:
    """Evaluate a list of conditions with AND (all) or OR (any) logic.

    Args:
        alert_data: The enriched alert dict.
        conditions: List of condition dicts from the YAML playbook.
        match: "all" (AND) or "any" (OR). Defaults to "all".

    Returns:
        True if the alert satisfies the conditions.
    """
    if not conditions:
        return True  # No conditions = always match

    results = [_evaluate_condition(alert_data, c) for c in conditions]

    if match == "any":
        return any(results)
    return all(results)
