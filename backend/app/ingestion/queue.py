"""Redis queue helpers for the alert pipeline."""

import json

import redis.asyncio as aioredis

from app.core.redis import get_redis

# Queue names — Module 2 and Module 3 consume from these
ENRICHMENT_QUEUE = "alerts:pending_enrichment"
PLAYBOOK_QUEUE = "alerts:pending_playbook"

# Checkpoint key for poller
POLL_CHECKPOINT_KEY = "sentinel:last_poll_timestamp"


async def push_for_enrichment(alert_data: dict) -> None:
    """Push a normalized alert to the enrichment queue (Module 2 consumes)."""
    redis = await get_redis()
    await redis.lpush(ENRICHMENT_QUEUE, json.dumps(alert_data, default=str))


async def pop_for_enrichment(timeout: int = 0) -> dict | None:
    """Pop next alert from enrichment queue. Blocking if timeout > 0."""
    redis = await get_redis()
    if timeout > 0:
        result = await redis.brpop(ENRICHMENT_QUEUE, timeout=timeout)
        if result:
            return json.loads(result[1])
        return None
    else:
        result = await redis.rpop(ENRICHMENT_QUEUE)
        return json.loads(result) if result else None


async def push_for_playbook(alert_data: dict) -> None:
    """Push an enriched alert to the playbook queue (Module 3 consumes)."""
    redis = await get_redis()
    await redis.lpush(PLAYBOOK_QUEUE, json.dumps(alert_data, default=str))


async def get_checkpoint() -> str | None:
    """Get the last poll timestamp checkpoint."""
    redis = await get_redis()
    return await redis.get(POLL_CHECKPOINT_KEY)


async def set_checkpoint(timestamp: str) -> None:
    """Save the last poll timestamp checkpoint."""
    redis = await get_redis()
    await redis.set(POLL_CHECKPOINT_KEY, timestamp)


async def get_queue_lengths() -> dict[str, int]:
    """Get current queue lengths (for monitoring)."""
    redis = await get_redis()
    enrichment_len = await redis.llen(ENRICHMENT_QUEUE)
    playbook_len = await redis.llen(PLAYBOOK_QUEUE)
    return {
        "enrichment_queue": enrichment_len,
        "playbook_queue": playbook_len,
    }
