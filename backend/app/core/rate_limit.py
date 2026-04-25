"""Rate limiting setup.

slowapi gives us a FastAPI-friendly limiter on top of `limits`. We key
on remote IP, which is correct for our deployment (no shared NAT
between trusted analysts) and trivial to upgrade later — swap the key
function for one that prefers an authenticated user id once auth lands.

In-process storage is the default; for a multi-replica deployment swap
to Redis (storage_uri="redis://...") so limits are shared across pods.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

# Default applies to every request that hits a route covered by the
# limiter dependency. Per-route overrides go on the route via the
# `@limiter.limit(...)` decorator (or via `limit_value=` deps).
limiter = Limiter(key_func=get_remote_address, default_limits=["120/minute"])


async def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return 429 + Retry-After. The default handler returns plain text and
    omits Retry-After, which most clients (browsers, k6) don't honour."""
    response = JSONResponse(
        status_code=429,
        content={
            "error": "rate_limited",
            "detail": f"Limit exceeded: {exc.detail}",
        },
    )
    # slowapi exposes the seconds-until-reset on the exception.
    retry_after = getattr(exc, "retry_after", None)
    if retry_after is not None:
        response.headers["Retry-After"] = str(int(retry_after))
    return response


def install(app: FastAPI) -> None:
    """Wire the limiter into a FastAPI app. Call once at app construction.

    SlowAPIMiddleware is required for default_limits to apply globally;
    without it, only routes with explicit @limiter.limit() decorators
    get limited.
    """
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
    app.add_middleware(SlowAPIMiddleware)
