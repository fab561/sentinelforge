"""Shared pytest config.

Runs from /app inside the backend container; sys.path adjustment lets
imports use the same `from app.x` form the application code uses.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# /app/tests/conftest.py → /app
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# Tests must not stand up real services — set defaults so pydantic-settings
# doesn't blow up if a developer runs pytest without a populated .env.
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
