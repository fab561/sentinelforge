"""Abstract base class for playbook action handlers."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ActionResult:
    action_type: str
    status: str           # completed | failed | skipped
    executed_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    result: dict = field(default_factory=dict)
    error: str | None = None

    def to_dict(self, playbook_name: str, target: str | None = None) -> dict:
        return {
            "playbook": playbook_name,
            "action_type": self.action_type,
            "target": target,
            "status": self.status,
            "executed_at": self.executed_at,
            "result": self.result,
            "error": self.error,
        }

    @classmethod
    def skipped(cls, action_type: str, reason: str) -> "ActionResult":
        return cls(action_type=action_type, status="skipped", error=reason)

    @classmethod
    def failed(cls, action_type: str, exc: Exception) -> "ActionResult":
        return cls(action_type=action_type, status="failed", error=str(exc))


class BaseAction(ABC):
    action_type: str = "base"

    @abstractmethod
    async def execute(
        self,
        alert_data: dict,
        params: dict,
        playbook_name: str,
    ) -> ActionResult: ...
