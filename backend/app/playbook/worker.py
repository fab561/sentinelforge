"""Module 3 — Playbook Worker.

Entrypoint: python -m app.playbook.worker

Loop:
  1. Blocking-pop from Redis queue  alerts:pending_playbook
  2. Run PlaybookEngine.run() — match + execute all applicable playbooks
  3. Update alert in PostgreSQL:
       playbook_actions = accumulated results
       status           = final_status from playbooks (or "escalated")
       case_id          = set if create_case action ran
  4. On any error: log + continue (alert stays as "enriched")
"""

from __future__ import annotations

import asyncio
import json
import logging
import signal
import sys

from app.core.config import settings
from app.core.database import async_session
from app.core.redis import close_redis, get_redis
from app.ingestion.queue import PLAYBOOK_QUEUE
from app.playbook.engine import PlaybookEngine
from app.schemas.alert import AlertUpdate
from app.services.alert_service import get_alert, update_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("playbook.worker")

_SHUTDOWN = False


def _handle_signal(sig: int, _frame: object) -> None:
    global _SHUTDOWN
    logger.info("Signal %s received — shutting down after current task", sig)
    _SHUTDOWN = True


async def _process_one(engine: PlaybookEngine, alert_data: dict) -> None:
    alert_id: str = alert_data.get("alert_id", "")
    if not alert_id:
        logger.warning("Queue item missing alert_id — skipping: %s", alert_data)
        return

    logger.info("[%s] Starting playbook evaluation", alert_id)

    try:
        outcome = await engine.run(alert_data)
    except Exception as exc:
        logger.error("[%s] Engine error: %s", alert_id, exc, exc_info=True)
        return

    action_results = outcome["playbook_actions"]
    final_status = outcome["final_status"]
    matched = outcome["matched_playbooks"]

    if not matched:
        logger.info("[%s] No playbooks matched — no DB update needed", alert_id)
        return

    # Determine new case_id from create_case actions
    new_case_id: str | None = None
    for res in action_results:
        if res.get("action_type") == "create_case" and res.get("status") == "completed":
            new_case_id = res.get("result", {}).get("case_id")
            break

    # Merge with existing playbook_actions (append, don't overwrite)
    try:
        async with async_session() as db:
            existing = await get_alert(db, alert_id)
            if existing is None:
                logger.warning("[%s] Alert not found in DB", alert_id)
                return

            existing_actions: list = existing.playbook_actions or []
            merged_actions = existing_actions + action_results

            # Only include case_id in the update when this run actually
            # created a case — AlertUpdate uses exclude_unset, so passing
            # None explicitly would wipe any pre-existing case link.
            update_kwargs: dict = {
                "playbook_actions": merged_actions,
                "status": final_status or "escalated",
            }
            if new_case_id:
                from uuid import UUID
                update_kwargs["case_id"] = UUID(new_case_id)

            update_data = AlertUpdate(**update_kwargs)
            await update_alert(db, alert_id, update_data)

    except Exception as exc:
        logger.error("[%s] DB update failed: %s", alert_id, exc, exc_info=True)
        return

    logger.info(
        "[%s] Done — matched=%s actions=%d status=%s",
        alert_id, matched, len(action_results), final_status,
    )


async def run() -> None:
    global _SHUTDOWN

    logger.info(
        "Playbook worker starting — playbook_dir=%s",
        settings.PLAYBOOK_DIR,
    )

    engine = PlaybookEngine()
    engine.reload()  # Load on startup

    redis = await get_redis()

    try:
        while not _SHUTDOWN:
            try:
                result = await redis.brpop(PLAYBOOK_QUEUE, timeout=5)
            except Exception as exc:
                logger.error("Redis brpop error: %s — retrying in 5s", exc)
                await asyncio.sleep(5)
                redis = await get_redis()
                continue

            if result is None:
                continue

            _, raw = result
            try:
                alert_data = json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON in queue item: %s — skipping", exc)
                continue

            await _process_one(engine, alert_data)

    finally:
        logger.info("Playbook worker shutting down")
        await close_redis()


def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    logger.info("Playbook worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
