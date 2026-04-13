"""Cloudflare action — block an IP via Firewall Access Rules (API v4).

Action type: block_ip

Required config (env vars):
  CLOUDFLARE_API_TOKEN   — API token with Zone:Firewall Rules:Edit permission
  CLOUDFLARE_ZONE_ID     — Target zone ID

YAML usage:
  - type: block_ip
    target: source_ip          # observable field to read IP from
    params:
      note: "Optional comment"   # default: "SentinelForge auto-block"
"""

from __future__ import annotations

import logging

import httpx

from app.core.config import settings
from app.playbook.actions.base import ActionResult, BaseAction

logger = logging.getLogger(__name__)

_CF_BASE = "https://api.cloudflare.com/client/v4"
_TIMEOUT = 15.0


def _resolve_ip(alert_data: dict, target: str) -> str | None:
    """Resolve the target field to an IP string."""
    obs: dict = alert_data.get("observables") or {}
    # target can be a field name like "source_ip" or a literal IP
    ip = obs.get(target) or alert_data.get(target)
    if ip and isinstance(ip, str) and ip.strip():
        return ip.strip()
    return None


class BlockIPAction(BaseAction):
    action_type = "block_ip"

    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult:
        if not settings.CLOUDFLARE_API_TOKEN or not settings.CLOUDFLARE_ZONE_ID:
            return ActionResult.skipped(self.action_type, "Cloudflare not configured (missing API token or zone ID)")

        target_field = params.get("target", "source_ip")
        ip = _resolve_ip(alert_data, target_field)
        if not ip:
            return ActionResult.skipped(self.action_type, f"No IP found in field '{target_field}'")

        note = params.get("note", f"SentinelForge auto-block | alert={alert_data.get('alert_id', 'unknown')}")

        try:
            async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
                resp = await client.post(
                    f"{_CF_BASE}/zones/{settings.CLOUDFLARE_ZONE_ID}/firewall/access-rules/rules",
                    headers={
                        "Authorization": f"Bearer {settings.CLOUDFLARE_API_TOKEN}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "mode": "block",
                        "configuration": {"target": "ip", "value": ip},
                        "notes": note[:500],
                    },
                )

            body = resp.json()

            # 409 = rule already exists — treat as success
            if resp.status_code == 409:
                logger.info("CF block: IP %s already blocked", ip)
                return ActionResult(
                    action_type=self.action_type,
                    status="completed",
                    result={"ip": ip, "already_blocked": True},
                )

            if not body.get("success"):
                errors = body.get("errors", [])
                raise RuntimeError(f"Cloudflare API error: {errors}")

            rule_id = body.get("result", {}).get("id")
            logger.info("CF block: IP %s blocked (rule=%s)", ip, rule_id)

            return ActionResult(
                action_type=self.action_type,
                status="completed",
                result={"ip": ip, "rule_id": rule_id, "zone_id": settings.CLOUDFLARE_ZONE_ID},
            )

        except Exception as exc:
            logger.error("CF block failed for %s: %s", ip, exc)
            return ActionResult.failed(self.action_type, exc)
