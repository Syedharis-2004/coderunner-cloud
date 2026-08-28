import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.v1 import api_router
from app.services.language_registry import language_registry
from app.services.docker_engine import docker_engine
from app.core.rate_limiter import limiter, rate_limit_exceeded_handler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CodeRunner Cloud API",
    description="Secure Code Execution Infrastructure for Developers",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
)

# Add rate limiter state
app.state.limiter = limiter

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Add rate limit exception handler
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# ── Middleware to attach user to request state ────────────────────────────────
@app.middleware("http")
async def attach_user_to_request(request: Request, call_next):
    """
    Middleware to make user available to rate limiter.
    This runs before the dependency injection system.
    """
    # We'll let the dependencies handle auth; this is just for rate limiting prep
    response = await call_next(request)
    return response


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    # Never expose internal error details in production
    message = str(exc) if settings.DEBUG else "An internal server error occurred."
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": message}},
    )


# ── Root & Health endpoints ────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "product": "CodeRunner Cloud",
        "tagline": "Secure Code Execution Infrastructure for Developers",
        "version": "1.0.0",
        "docs": "/swagger",
    }


@app.get("/health")
def health():
    return {"status": "ok", "service": "coderunner-cloud-api"}


@app.get("/health/docker")
def health_docker():
    available = docker_engine.is_available()
    return {
        "docker": "connected" if available else "unavailable",
    }


@app.get("/api/v1/languages")
def list_languages():
    return {"languages": language_registry.list_all()}
