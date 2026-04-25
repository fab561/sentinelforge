"""Playbook engine — loads YAML definitions, matches conditions, executes actions.

Playbook YAML schema
--------------------
name: string (required)
description: string (optional)
enabled: bool (default true)
priority: int (default 100, lower = evaluated first)
match: "all" | "any" (default "all")

conditions:
  - field: string          # dot-notation path into alert dict
    operator: eq|neq|gt|gte|lt|lte|contains|in|not_in|exists|not_exists
    value: any             # comparison value (not needed for exists/not_exists)

actions:
  - type: block_ip | wazuh_active_response | create_case | notify | tag_alert | update_status
    target: string         # optional: observable field name (used by block_ip)
    params: {}             # action-specific parameters
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

import yaml

from app.core.config import settings
from app.playbook.actions.base import ActionResult, BaseAction
from app.playbook.actions.case import CreateCaseAction
from app.playbook.actions.cloudflare import BlockIPAction
from app.playbook.actions.notify import NotifyAction, TagAlertAction, UpdateStatusAction
from app.playbook.actions.wazuh import WazuhActiveResponseAction
from app.playbook.conditions import evaluate_conditions

logger = logging.getLogger(__name__)

# Registry of available action handlers
_ACTION_REGISTRY: dict[str, BaseAction] = {
    "block_ip": BlockIPAction(),
    "wazuh_active_response": WazuhActiveResponseAction(),
    "create_case": CreateCaseAction(),
    "notify": NotifyAction(),
    "tag_alert": TagAlertAction(),
    "update_status": UpdateStatusAction(),
}


class Playbook:
    """Parsed and validated playbook definition."""

    def __init__(self, raw: dict, source_file: str) -> None:
        self.name: str = raw.get("name", Path(source_file).stem)
        self.description: str = raw.get("description", "")
        self.enabled: bool = raw.get("enabled", True)
        self.priority: int = raw.get("priority", 100)
        self.match: str = raw.get("match", "all")
        self.conditions: list[dict] = raw.get("conditions", [])
        self.actions: list[dict] = raw.get("actions", [])
        self.source_file: str = source_file

    def matches(self, alert_data: dict) -> bool:
        if not self.enabled:
            return False
        return evaluate_conditions(alert_data, self.conditions, self.match)

    def __repr__(self) -> str:
        return f"<Playbook name={self.name!r} priority={self.priority} enabled={self.enabled}>"


class PlaybookEngine:
    """Loads playbooks from disk and executes them against alerts."""

    def __init__(self, playbook_dir: str | None = None) -> None:
        self._playbook_dir = Path(playbook_dir or settings.PLAYBOOK_DIR)
        self._playbooks: list[Playbook] = []
        self._loaded = False

    def _load_playbooks(self) -> None:
        """Load all .yaml/.yml files from the playbook directory."""
        self._playbooks = []
        if not self._playbook_dir.exists():
            logger.warning("Playbook dir not found: %s", self._playbook_dir)
            return

        files = sorted(
            self._playbook_dir.glob("**/*.yaml"),
        ) + sorted(self._playbook_dir.glob("**/*.yml"))

        for path in files:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    raw = yaml.safe_load(f)
                if not isinstance(raw, dict):
                    logger.warning("Skipping invalid playbook (not a dict): %s", path)
                    continue
                pb = Playbook(raw, str(path))
                self._playbooks.append(pb)
                logger.debug("Loaded playbook: %s (priority=%d)", pb.name, pb.priority)
            except Exception as exc:
                logger.error("Failed to load playbook %s: %s", path, exc)

        # Sort by priority (ascending = highest priority first)
        self._playbooks.sort(key=lambda p: p.priority)
        logger.info(
            "Loaded %d playbook(s) from %s",
            len(self._playbooks), self._playbook_dir,
        )
        self._loaded = True

    def reload(self) -> None:
        """Force reload of all playbooks from disk."""
        self._loaded = False
        self._load_playbooks()

    @property
    def playbooks(self) -> list[Playbook]:
        if not self._loaded:
            self._load_playbooks()
        return self._playbooks

    def dry_run(self, alert_data: dict) -> dict[str, Any]:
        """Evaluate playbooks against an alert WITHOUT executing actions.

        Returns the same shape as run() minus side effects, so the UI can
        preview which playbooks would fire and which actions they'd take
        before flipping a rule on in production.
        """
        matched = [pb for pb in self.playbooks if pb.matches(alert_data)]
        return {
            "matched_playbooks": [pb.name for pb in matched],
            "planned_actions": [
                {
                    "playbook": pb.name,
                    "action_type": a.get("type"),
                    "target": a.get("target"),
                    "params": a.get("params") or {},
                }
                for pb in matched
                for a in pb.actions
            ],
            "all_playbooks_evaluated": [pb.name for pb in self.playbooks],
            "skipped_disabled": [pb.name for pb in self._playbooks if not pb.enabled],
        }

    async def run(self, alert_data: dict) -> dict[str, Any]:
        """Match and execute all applicable playbooks for an alert.

        Returns a dict with:
          - playbook_actions: list of action result dicts (to store in DB)
          - final_status: suggested alert status after all actions
          - matched_playbooks: list of matched playbook names
        """
        alert_id = alert_data.get("alert_id", "unknown")
        all_action_results: list[dict] = []
        matched_names: list[str] = []
        final_status: str | None = None

        matched = [pb for pb in self.playbooks if pb.matches(alert_data)]

        if not matched:
            logger.info("[%s] No playbooks matched", alert_id)
            return {
                "playbook_actions": [],
                "final_status": None,
                "matched_playbooks": [],
            }

        logger.info("[%s] Matched %d playbook(s): %s", alert_id, len(matched), [p.name for p in matched])

        for playbook in matched:
            matched_names.append(playbook.name)
            pb_results = await self._execute_playbook(playbook, alert_data)
            all_action_results.extend(pb_results)

            # Extract suggested status from update_status actions
            for res in pb_results:
                if res.get("action_type") == "update_status" and res.get("status") == "completed":
                    final_status = res.get("result", {}).get("new_status")

        return {
            "playbook_actions": all_action_results,
            "final_status": final_status or "escalated",
            "matched_playbooks": matched_names,
        }

    async def _execute_playbook(self, playbook: Playbook, alert_data: dict) -> list[dict]:
        """Execute all actions in a playbook sequentially. Returns list of result dicts."""
        results: list[dict] = []
        alert_id = alert_data.get("alert_id", "unknown")

        for action_def in playbook.actions:
            action_type = action_def.get("type")
            if not action_type:
                logger.warning("[%s] Action missing 'type' in playbook %s", alert_id, playbook.name)
                continue

            handler = _ACTION_REGISTRY.get(action_type)
            if not handler:
                logger.warning("[%s] Unknown action type: %s", alert_id, action_type)
                results.append({
                    "playbook": playbook.name,
                    "action_type": action_type,
                    "status": "skipped",
                    "error": f"Unknown action type: {action_type}",
                })
                continue

            # Merge top-level 'target' into params for actions that need it
            params = dict(action_def.get("params") or {})
            if "target" in action_def and "target" not in params:
                params["target"] = action_def["target"]

            try:
                result: ActionResult = await handler.execute(alert_data, params, playbook.name)
                result_dict = result.to_dict(playbook.name, params.get("target"))
                results.append(result_dict)

                logger.info(
                    "[%s] Action %s/%s → %s",
                    alert_id, playbook.name, action_type, result.status,
                )
            except Exception as exc:
                logger.error(
                    "[%s] Action %s/%s raised: %s",
                    alert_id, playbook.name, action_type, exc,
                    exc_info=True,
                )
                results.append({
                    "playbook": playbook.name,
                    "action_type": action_type,
                    "status": "failed",
                    "error": str(exc),
                })

        return results
