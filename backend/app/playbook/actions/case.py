"""Case creation/escalation action.

Action type: create_case

Creates an incident case and links the alert to it.
If a case already exists for the alert (alert.case_id set), skips creation.

YAML usage:
  - type: create_case
    params:
      title: "Malicious activity: {alert.title}"     # template supported
      description: "Auto-escalated by SentinelForge playbook."
      severity: "{alert.severity}"                   # or literal: critical
"""

from __future__ import annotations

import logging
import re

from app.core.database import async_session
from app.playbook.actions.base import ActionResult, BaseAction
from app.schemas.case import CaseCreate
from app.services import case_service

logger = logging.getLogger(__name__)

_TEMPLATE_RE = re.compile(r"\{alert\.([^}]+)\}")


def _render(template: str, alert_data: dict) -> str:
    """Replace {alert.field} placeholders from alert_data."""
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        val = alert_data.get(key)
        return str(val) if val is not None else match.group(0)
    return _TEMPLATE_RE.sub(replacer, template)


class CreateCaseAction(BaseAction):
    action_type = "create_case"

    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult:
        alert_id: str = alert_data.get("alert_id", "")

        # Skip if already linked to a case
        if alert_data.get("case_id"):
            return ActionResult.skipped(
                self.action_type,
                f"Alert already linked to case {alert_data['case_id']}",
            )

        title_template = params.get("title", "Incident: {alert.title}")
        desc_template = params.get(
            "description",
            f"Auto-escalated by playbook '{playbook_name}'. Alert ID: {alert_id}",
        )
        severity_template = params.get("severity", "{alert.severity}")

        title = _render(title_template, alert_data)
        description = _render(desc_template, alert_data)
        severity = _render(severity_template, alert_data)

        try:
            async with async_session() as db:
                # Try to correlate first — if there's already an open case
                # for this attacker (same source_ip in the last 24h), attach
                # this alert to it instead of opening a duplicate.
                existing = await case_service.find_correlated_open_case(db, alert_data)
                if existing is not None and alert_id:
                    await case_service.attach_alert_to_case(db, existing.id, alert_id)
                    logger.info(
                        "Alert correlated to existing case: %s (alert=%s playbook=%s)",
                        existing.case_number, alert_id, playbook_name,
                    )
                    return ActionResult(
                        action_type=self.action_type,
                        status="completed",
                        result={
                            "case_id": str(existing.id),
                            "case_number": existing.case_number,
                            "title": existing.title,
                            "correlated": True,
                        },
                    )

                case_data = CaseCreate(
                    title=title[:500],
                    description=description,
                    severity=severity or alert_data.get("severity"),
                    alert_ids=[alert_id] if alert_id else [],
                )
                case = await case_service.create_case(db, case_data)

            logger.info(
                "Case created: %s (alert=%s playbook=%s)",
                case.case_number, alert_id, playbook_name,
            )
            return ActionResult(
                action_type=self.action_type,
                status="completed",
                result={
                    "case_id": str(case.id),
                    "case_number": case.case_number,
                    "title": case.title,
                    "correlated": False,
                },
            )
        except Exception as exc:
            logger.error("Case creation failed (alert=%s): %s", alert_id, exc)
            return ActionResult.failed(self.action_type, exc)
