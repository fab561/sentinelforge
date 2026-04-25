import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.redis import close_redis

logger = logging.getLogger("sentinelforge")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SentinelForge backend starting...")

    # Create any missing tables. Idempotent (CREATE TABLE IF NOT EXISTS)
    # so running repeatedly on an already-migrated DB is a no-op. Real
    # schema evolution still belongs in alembic; this catches the case
    # where a new model landed and we haven't added a migration yet.
    from app.core.database import engine
    from app.models import Alert, AuditLog, Case, Evidence, IOC, Rule, User  # noqa: F401
    from app.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # MinIO bucket for case evidence attachments. Logged on create, silent
    # on the common already-exists path.
    try:
        from app.core.storage import ensure_bucket
        await ensure_bucket()
    except Exception as exc:
        logger.warning("MinIO bucket init failed: %s (evidence uploads will fail until fixed)", exc)

    # Start the Wazuh alert poller in background
    from app.ingestion.wazuh_poller import start_poller
    poller_task = asyncio.create_task(start_poller())

    yield

    # Shutdown
    poller_task.cancel()
    try:
        await poller_task
    except asyncio.CancelledError:
        pass
    await close_redis()
    logger.info("SentinelForge backend stopped.")


app = FastAPI(
    title="SentinelForge",
    description="SOC Automation Platform - SIEM Core & Data Pipeline API",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend (Module 4) and dev tools
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(api_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "sentinelforge-backend"}
