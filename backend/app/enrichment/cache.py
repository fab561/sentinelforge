"""Redis-backed TTL cache for threat intel API responses.

Keys follow:  enrichment:cache:{provider}:{type}:{observable}
Default TTL:  1 hour (configurable via settings.ENRICHMENT_CACHE_TTL)
"""

import json
import logging

from app.core.config import settings
from app.core.redis import get_redis

logger = logging.getLogger(__name__)

_CACHE_PREFIX = "enrichment:cache:"


def _key(provider: str, observable_type: str, observable: str) -> str:
    return f"{_CACHE_PREFIX}{provider}:{observable_type}:{observable}"


async def get_cached(provider: str, observable_type: str, observable: str) -> dict | None:
    try:
        redis = await get_redis()
        raw = await redis.get(_key(provider, observable_type, observable))
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.warning("Cache read failed [%s/%s/%s]: %s", provider, observable_type, observable, exc)
        return None


async def set_cached(
    provider: str,
    observable_type: str,
    observable: str,
    data: dict,
    ttl: int | None = None,
) -> None:
    try:
        redis = await get_redis()
        ttl = ttl if ttl is not None else settings.ENRICHMENT_CACHE_TTL
        await redis.setex(_key(provider, observable_type, observable), ttl, json.dumps(data))
    except Exception as exc:
        logger.warning("Cache write failed [%s/%s/%s]: %s", provider, observable_type, observable, exc)
