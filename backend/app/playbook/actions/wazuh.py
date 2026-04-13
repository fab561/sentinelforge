"""Wazuh active-response action.

Action type: wazuh_active_response

Triggers a command on the Wazuh agent associated with the alert's
hostname/agent_id observable.

YAML usage:
  - type: wazuh_active_response
    params:
      command: disable-account        # Wazuh active-response command name
      arguments: ["{observables.username}"]  # template strings supported
      agent_field: hostname           # alert field to resolve agent (default: hostname)
"""

from __future__ import annotations

import logging
import re

from app.core.wazuh_client import WazuhManagerClient
from app.playbook.actions.base import ActionResult, BaseAction

logger = logging.getLogger(__name__)

_TEMPLATE_RE = re.compile(r"\{([^}]+)\}")


def _render_template(template: str, alert_data: dict) -> str:
    """Replace {field.path} placeholders with values from alert_data."""
    def replacer(match: re.Match) -> str:
        path = match.group(1)
        parts = path.split(".")
        current = alert_data
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = None
            if current is None:
                return match.group(0)  # Keep original if not found
        return str(current)

    return _TEMPLATE_RE.sub(replacer, template)


async def _resolve_agent_id(wazuh: WazuhManagerClient, hostname: str) -> str | None:
    """Look up Wazuh agent ID by hostname."""
    try:
        agents = await wazuh.get_agents()
        for agent in agents:
            if agent.get("name", "").lower() == hostname.lower():
                return agent.get("id")
    except Exception as exc:
        logger.warning("Agent lookup failed for hostname '%s': %s", hostname, exc)
    return None


class WazuhActiveResponseAction(BaseAction):
    action_type = "wazuh_active_response"

    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult:
        command = params.get("command")
        if not command:
            return ActionResult.skipped(self.action_type, "No command specified")

        # Render template arguments
        raw_args: list[str] = params.get("arguments", [])
        arguments = [_render_template(a, alert_data) for a in raw_args]

        # Resolve agent
        agent_field = params.get("agent_field", "hostname")
        obs: dict = alert_data.get("observables") or {}
        hostname_or_id = obs.get(agent_field) or alert_data.get(agent_field)

        if not hostname_or_id:
            return ActionResult.skipped(
                self.action_type,
                f"No value for agent_field '{agent_field}' in alert",
            )

        wazuh = WazuhManagerClient()
        try:
            # Try as direct agent ID first (numeric), else resolve by name
            if str(hostname_or_id).isdigit():
                agent_id = str(hostname_or_id).zfill(3)
            else:
                agent_id = await _resolve_agent_id(wazuh, str(hostname_or_id))

            if not agent_id:
                return ActionResult.skipped(
                    self.action_type,
                    f"Could not resolve Wazuh agent for '{hostname_or_id}'",
                )

            result = await wazuh.active_response(agent_id, command, arguments)
            logger.info(
                "Wazuh AR: command=%s agent=%s alert=%s",
                command, agent_id, alert_data.get("alert_id"),
            )
            return ActionResult(
                action_type=self.action_type,
                status="completed",
                result={
                    "agent_id": agent_id,
                    "command": command,
                    "arguments": arguments,
                    "wazuh_response": result,
                },
            )
        except Exception as exc:
            logger.error("Wazuh AR failed [%s/%s]: %s", command, hostname_or_id, exc)
            return ActionResult.failed(self.action_type, exc)
        finally:
            await wazuh.close()
