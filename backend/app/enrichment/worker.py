"""Module 2 — Enrichment Worker.

Entrypoint: python -m app.enrichment.worker

Loop:
  1. Blocking-pop from Redis queue  alerts:pending_enrichment
  2. Run EnrichmentEngine.enrich()
  3. Update alert in PostgreSQL via alert_service.update_alert()
  4. Push enriched alert to     alerts:pending_playbook  (for M3)
  5. On any error: log + continue (alert stays in DB as 'new')
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
from app.enrichment.engine import EnrichmentEngine
from app.ingestion.queue import ENRICHMENT_QUEUE, push_for_playbook
from app.schemas.alert import AlertUpdate
from app.services.alert_service import update_alert

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger("enrichment.worker")

_SHUTDOWN = False


def _handle_signal(sig: int, _frame: object) -> None:
    global _SHUTDOWN
    logger.info("Signal %s received — shutting down after current task", sig)
    _SHUTDOWN = True


async def _process_one(engine: EnrichmentEngine, alert_data: dict) -> None:
    alert_id: str = alert_data.get("alert_id", "")
    if not alert_id:
        logger.warning("Received queue item with no alert_id — skipping: %s", alert_data)
        return

    logger.info("[%s] Starting enrichment", alert_id)

    try:
        payload = await engine.enrich(alert_data)
    except Exception as exc:
        logger.error("[%s] Engine error: %s", alert_id, exc, exc_info=True)
        return

    # Persist enrichment to DB
    update_data = AlertUpdate(
        enrichment=payload["enrichment"],
        threat_score=payload["threat_score"],
        verdict=payload["verdict"],
        status="enriched",
    )
    try:
        async with async_session() as db:
            updated = await update_alert(db, alert_id, update_data)
        if updated is None:
            logger.warning("[%s] alert not found in DB — enrichment not saved", alert_id)
            return
    except Exception as exc:
        logger.error("[%s] DB update failed: %s", alert_id, exc, exc_info=True)
        return

    # Forward to playbook queue (M3)
    try:
        enriched_payload = {
            **alert_data,
            "enrichment": payload["enrichment"],
            "threat_score": payload["threat_score"],
            "verdict": payload["verdict"],
            "status": "enriched",
        }
        await push_for_playbook(enriched_payload)
    except Exception as exc:
        logger.error("[%s] Failed to push to playbook queue: %s", alert_id, exc, exc_info=True)
        # Not fatal — alert is already enriched in DB

    logger.info(
        "[%s] Done — score=%d verdict=%s",
        alert_id,
        payload["threat_score"],
        payload["verdict"],
    )


async def run() -> None:
    global _SHUTDOWN

    logger.info(
        "Enrichment worker starting (concurrency=%d cache_ttl=%ds)",
        settings.ENRICHMENT_CONCURRENT_LIMIT,
        settings.ENRICHMENT_CACHE_TTL,
    )

    engine = EnrichmentEngine()
    redis = await get_redis()

    try:
        while not _SHUTDOWN:
            try:
                # Blocking pop with 5s timeout so we can check _SHUTDOWN
                result = await redis.brpop(ENRICHMENT_QUEUE, timeout=5)
            except Exception as exc:
                logger.error("Redis brpop error: %s — retrying in 5s", exc)
                await asyncio.sleep(5)
                # Re-acquire redis in case of disconnect
                redis = await get_redis()
                continue

            if result is None:
                # Timeout — loop again
                continue

            _, raw = result
            try:
                alert_data = json.loads(raw)
            except json.JSONDecodeError as exc:
                logger.error("Invalid JSON in queue item: %s — skipping", exc)
                continue

            await _process_one(engine, alert_data)

    finally:
        logger.info("Enrichment worker shutting down — closing Redis connection")
        await close_redis()


def main() -> None:
    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        pass
    logger.info("Enrichment worker stopped")
    sys.exit(0)


if __name__ == "__main__":
    main()
