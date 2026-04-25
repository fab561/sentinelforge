"""Cowrie session-log evidence harvester.

Pulls events + tty replays from the cowrie volumes shared with this
container and uploads them to MinIO as case evidence. Runs from the
playbook-worker (where cowrie-logs / cowrie-data are mounted read-
only at /cowrie-evidence).

Best-effort by design: if cowrie isn't writing yet, or paths shift,
we log + return empty so case creation still succeeds.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import UUID

from app.core.database import async_session
from app.core.storage import upload_bytes
from app.services import evidence_service

logger = logging.getLogger(__name__)

_LOG_PATH = Path(os.environ.get("COWRIE_LOG_PATH", "/cowrie-evidence/logs/cowrie.json"))
_TTY_DIR = Path(os.environ.get("COWRIE_TTY_DIR", "/cowrie-evidence/data/tty"))

# Cap on events we'll bundle into one evidence file. Cowrie can fire
# thousands per scanner; we want a useful sample, not a 50MB upload.
_MAX_EVENTS = 500
# Look back this far from the alert time when matching events.
_LOOKBACK = timedelta(hours=2)


def _parse_ts(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # Cowrie writes RFC3339 with trailing Z.
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _collect_session_events(src_ip: str) -> tuple[list[dict], set[str]]:
    """Return (events, session_ids) for cowrie events matching src_ip."""
    if not _LOG_PATH.exists():
        logger.info("cowrie log not found at %s — skipping harvest", _LOG_PATH)
        return [], set()

    cutoff = datetime.now(timezone.utc) - _LOOKBACK
    events: list[dict] = []
    sessions: set[str] = set()

    try:
        with _LOG_PATH.open("r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("src_ip") != src_ip:
                    continue
                ts = _parse_ts(e.get("timestamp"))
                if ts is not None and ts < cutoff:
                    continue
                events.append(e)
                sid = e.get("session")
                if sid:
                    sessions.add(sid)
                if len(events) >= _MAX_EVENTS:
                    break
    except OSError as exc:
        logger.warning("reading cowrie log failed: %s", exc)
        return [], set()

    return events, sessions


def _read_tty_files(session_ids: set[str]) -> list[tuple[str, bytes]]:
    """Return (filename, bytes) pairs for tty replay files of these sessions."""
    if not session_ids or not _TTY_DIR.exists():
        return []
    out: list[tuple[str, bytes]] = []
    try:
        for entry in _TTY_DIR.iterdir():
            if not entry.is_file():
                continue
            # Cowrie names tty files by session uuid; substring match keeps
            # us tolerant to suffixes like .log.
            if any(sid in entry.name for sid in session_ids):
                try:
                    out.append((entry.name, entry.read_bytes()))
                except OSError:
                    continue
    except OSError as exc:
        logger.warning("scanning tty dir failed: %s", exc)
    return out


async def attach_cowrie_evidence(
    case_id: UUID,
    alert_id: str,
    src_ip: str,
) -> dict:
    """Harvest matching cowrie events + tty replays for this source IP and
    attach them to the case. Returns a result dict for the playbook log."""
    events, sessions = _collect_session_events(src_ip)
    if not events:
        return {"attached": 0, "events": 0, "reason": "no cowrie events for ip"}

    bundle = "\n".join(json.dumps(e, separators=(",", ":")) for e in events).encode("utf-8")
    bundle_name = f"cowrie-events-{src_ip}-{alert_id}.jsonl"

    attached = 0
    async with async_session() as db:
        upload = await upload_bytes(
            data=bundle, content_type="application/x-ndjson", prefix="cowrie",
        )
        await evidence_service.create(
            db, case_id=case_id, kind="cowrie_session",
            filename=bundle_name, content_type="application/x-ndjson",
            size_bytes=upload.size_bytes, sha256=upload.sha256,
            storage_key=upload.storage_key,
            description=(
                f"{len(events)} cowrie events from {src_ip} "
                f"across {len(sessions)} session(s) "
                f"auto-harvested by playbook for alert {alert_id}"
            ),
        )
        attached += 1

        for fname, blob in _read_tty_files(sessions):
            up = await upload_bytes(
                data=blob, content_type="application/octet-stream", prefix="cowrie/tty",
            )
            await evidence_service.create(
                db, case_id=case_id, kind="cowrie_session",
                filename=f"tty-{fname}", content_type="application/octet-stream",
                size_bytes=up.size_bytes, sha256=up.sha256,
                storage_key=up.storage_key,
                description=f"Cowrie TTY replay for session in {src_ip} attack",
            )
            attached += 1

    logger.info(
        "[%s] cowrie evidence attached: %d files (%d events, %d sessions)",
        alert_id, attached, len(events), len(sessions),
    )
    return {
        "attached": attached,
        "events": len(events),
        "sessions": len(sessions),
        "ip": src_ip,
    }
