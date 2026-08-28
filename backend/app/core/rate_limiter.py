"""
Rate Limiting Middleware
========================
Plan-based rate limiting using SlowAPI with in-memory fallback.
Redis is optional — if unavailable, falls back to in-memory storage.
"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings

logger = logging.getLogger(__name__)


def get_rate_limit_key(request: Request) -> str:
    """Rate limit key: user ID > API key ID > IP address."""
    if hasattr(request.state, "user") and request.state.user:
        return f"user:{request.state.user.id}"
    if hasattr(request.state, "api_key") and request.state.api_key:
        return f"api_key:{request.state.api_key.id}"
    return f"ip:{get_remote_address(request)}"


# Use Redis if available, else fall back to in-memory
def _get_storage_uri() -> str:
    try:
        import redis as _redis
        r = _redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        logger.info("Rate limiter: using Redis storage")
        return settings.REDIS_URL
    except Exception:
        logger.warning("Rate limiter: Redis unavailable, using in-memory storage")
        return "memory://"


limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["200/minute"],
    storage_uri=_get_storage_uri(),
    strategy="fixed-window",
)


def get_plan_rate_limit(request: Request) -> str:
    """Return slowapi rate-limit string based on the user's plan."""
    default = f"{settings.RATE_LIMIT_FREE}/minute"
    try:
        if not hasattr(request.state, "user") or not request.state.user:
            return default
        from app.services.subscription_service import subscription_service
        from app.core.database import SessionLocal
        db = SessionLocal()
        try:
            plan = subscription_service.get_user_plan(db, request.state.user)
            return f"{plan.rate_limit_per_minute}/minute"
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"Rate limit plan lookup failed: {exc}")
        return default


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return JSON 429 response."""
    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": "Rate limit exceeded. Please slow down or upgrade your plan.",
            },
        },
    )
