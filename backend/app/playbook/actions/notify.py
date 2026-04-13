"""Notification / logging action.

Action type: notify

Structured log entry at WARNING level — visible in container logs.
Extensible hook point for future Slack/webhook/email integrations.

YAML usage:
  - type: notify
    params:
      message: "High-severity alert triggered: {alert.title}"
      level: warning    # info | warning | critical (default: warning)
      # Future params (not yet implemented, reserved):
      # channel: slack
      # webhook_url: "${SLACK_WEBHOOK_URL}"
"""

from __future__ import annotations

import logging
import re

from app.playbook.actions.base import ActionResult, BaseAction

logger = logging.getLogger(__name__)

_TEMPLATE_RE = re.compile(r"\{alert\.([^}]+)\}")

_LEVELS = {
    "info": logger.info,
    "warning": logger.warning,
    "critical": logger.critical,
}


def _render(template: str, alert_data: dict) -> str:
    def replacer(match: re.Match) -> str:
        key = match.group(1)
        val = alert_data.get(key)
        return str(val) if val is not None else match.group(0)
    return _TEMPLATE_RE.sub(replacer, template)


class NotifyAction(BaseAction):
    action_type = "notify"

    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult:
        template = params.get(
            "message",
            "Playbook '{playbook}' triggered for alert {alert.alert_id} | verdict={alert.verdict} score={alert.threat_score}",
        )
        level = params.get("level", "warning").lower()

        message = _render(template, alert_data)
        message = message.replace("{playbook}", playbook_name)

        log_fn = _LEVELS.get(level, logger.warning)
        log_fn("[PLAYBOOK:%s] %s", playbook_name, message)

        return ActionResult(
            action_type=self.action_type,
            status="completed",
            result={"message": message, "level": level},
        )


class TagAlertAction(BaseAction):
    """Add tags to alert enrichment summary.tags (returns patch data for worker)."""

    action_type = "tag_alert"

    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult:
        tags: list[str] = params.get("tags", [])
        if not tags:
            return ActionResult.skipped(self.action_type, "No tags specified")

        rendered_tags = [_render(t, alert_data) for t in tags]

        return ActionResult(
            action_type=self.action_type,
            status="completed",
            result={"tags_added": rendered_tags},
        )


class UpdateStatusAction(BaseAction):
    """Set alert status field — resolved by worker after all actions run."""

    action_type = "update_status"

    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult:
        status = params.get("status")
        if not status:
            return ActionResult.skipped(self.action_type, "No status specified")

        return ActionResult(
            action_type=self.action_type,
            status="completed",
            result={"new_status": status},
        )
