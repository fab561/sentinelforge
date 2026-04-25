"""Playbook inspection + dry-run API.

Read-only over the YAML files mounted at PLAYBOOK_DIR — playbooks
themselves are still authored as files and shipped through git, not
edited via the UI. This endpoint exposes them so analysts can see
coverage and preview behaviour before live alerts hit.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.playbook.engine import PlaybookEngine

router = APIRouter(prefix="/playbooks", tags=["Playbooks"])

# Module-level engine — loads playbooks lazily, then caches.
_engine = PlaybookEngine()


class PlaybookSummary(BaseModel):
    name: str
    description: str
    enabled: bool
    priority: int
    match: str
    conditions: list[dict]
    action_types: list[str]
    source_file: str


class DryRunRequest(BaseModel):
    # Loose typing on purpose — alert payloads come from the wild and we
    # don't want strict validation here to mask interesting test cases.
    alert: dict[str, Any]


class DryRunResponse(BaseModel):
    matched_playbooks: list[str]
    planned_actions: list[dict[str, Any]]
    all_playbooks_evaluated: list[str]
    skipped_disabled: list[str]


@router.get("", response_model=list[PlaybookSummary])
async def list_playbooks():
    """All playbooks discovered in PLAYBOOK_DIR."""
    return [
        PlaybookSummary(
            name=pb.name,
            description=pb.description,
            enabled=pb.enabled,
            priority=pb.priority,
            match=pb.match,
            conditions=pb.conditions,
            action_types=[a.get("type", "?") for a in pb.actions],
            source_file=pb.source_file,
        )
        for pb in _engine.playbooks
    ]


@router.post("/reload", status_code=204)
async def reload_playbooks():
    """Re-read all playbook YAML from disk. Useful after editing files."""
    _engine.reload()


@router.post("/dry-run", response_model=DryRunResponse)
async def dry_run(req: DryRunRequest):
    """Show which playbooks would fire on this alert and what they'd do —
    no side effects, no DB writes, no Cloudflare calls."""
    if not req.alert:
        raise HTTPException(status_code=400, detail="alert is required")
    return _engine.dry_run(req.alert)
