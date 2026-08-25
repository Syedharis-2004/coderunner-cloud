"""
Rate Limiting Middleware
========================
Plan-based rate limiting for API endpoints using SlowAPI.
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


def get_plan_rate_limit(request: Request) -> str:
    """Return a slowapi rate-limit string based on the user's subscription plan."""
    default_limit = f"{settings.RATE_LIMIT_FREE}/minute"

    if not hasattr(request.state, "user") or not request.state.user:
        return default_limit

    try:
        from app.services.subscription_service import subscription_service
        from app.core.database import SessionLocal

        db = SessionLocal()
        try:
            plan = subscription_service.get_user_plan(db, request.state.user)
            rate_limit = f"{plan.rate_limit_per_minute}/minute"
            logger.debug(
                f"Rate limit for user {request.state.user.id}: "
                f"{rate_limit} (plan: {plan.key})"
            )
            return rate_limit
        finally:
            db.close()
    except Exception as exc:
        logger.error(f"Error resolving plan rate limit: {exc}")
        return default_limit


# Initialize SlowAPI limiter backed by Redis
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=["1000/hour"],
    storage_uri=settings.REDIS_URL,
    strategy="fixed-window",
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """Return a proper JSON 429 response instead of raising inside a handler."""
    logger.warning(
        f"Rate limit exceeded: key={get_rate_limit_key(request)} "
        f"path={request.url.path}"
    )
    retry_after = None
    if hasattr(exc, "detail") and "Retry after" in str(exc.detail):
        retry_after = str(exc.detail).split("Retry after ")[-1]

    return JSONResponse(
        status_code=429,
        content={
            "success": False,
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": (
                    "You have exceeded the rate limit for your plan. "
                    "Please slow down or upgrade your plan."
                ),
                "retry_after": retry_after,
            },
        },
    )
