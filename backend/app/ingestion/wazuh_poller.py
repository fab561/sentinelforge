"""Background task that polls Wazuh Indexer for new alerts and feeds the pipeline."""

import asyncio
import logging

from app.core.config import settings
from app.core.database import async_session
from app.core.wazuh_client import WazuhIndexerClient
from app.ingestion.normalizer import normalize_wazuh_alert
from app.ingestion.queue import (
    get_checkpoint,
    push_for_enrichment,
    set_checkpoint,
)
from app.models.alert import Alert
from app.services.alert_service import get_alert

logger = logging.getLogger("sentinelforge.poller")


async def poll_once() -> int:
    """Run a single poll cycle. Returns number of new alerts ingested."""
    client = WazuhIndexerClient()
    count = 0

    try:
        checkpoint = await get_checkpoint()
        raw_alerts = await client.search_alerts(since=checkpoint, size=200)

        if not raw_alerts:
            return 0

        latest_timestamp = checkpoint

        # Persist all alerts first, then push to Redis only after COMMIT
        # succeeds. Avoids split-brain where the queue references an
        # alert_id that was never persisted due to rollback.
        newly_persisted: list[dict] = []
        async with async_session() as db:
            for raw in raw_alerts:
                normalized = normalize_wazuh_alert(raw)

                existing = await get_alert(db, normalized["alert_id"])
                if existing:
                    continue

                db.add(Alert(**normalized))
                newly_persisted.append(normalized)

                ts = raw.get("timestamp", "")
                if ts and (not latest_timestamp or ts > latest_timestamp):
                    latest_timestamp = ts

            await db.commit()

        for normalized in newly_persisted:
            await push_for_enrichment(normalized)
            count += 1

        # Update checkpoint
        if latest_timestamp and latest_timestamp != checkpoint:
            await set_checkpoint(latest_timestamp)

    except Exception as e:
        logger.error(f"Poll cycle failed: {e}")
    finally:
        await client.close()

    return count


async def start_poller() -> None:
    """Run the poller loop forever."""
    logger.info(
        f"Wazuh poller starting (interval={settings.POLL_INTERVAL}s, "
        f"indexer={settings.WAZUH_INDEXER_URL})"
    )

    while True:
        try:
            count = await poll_once()
            if count > 0:
                logger.info(f"Ingested {count} new alerts from Wazuh")
        except asyncio.CancelledError:
            logger.info("Poller shutting down")
            raise
        except Exception as e:
            logger.error(f"Poller error: {e}")

        await asyncio.sleep(settings.POLL_INTERVAL)
