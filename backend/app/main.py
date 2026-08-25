import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.services.language_registry import language_registry
from app.services.docker_engine import docker_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="CodeRunner Cloud API",
    description="Secure Code Execution Infrastructure for Developers",
    version="1.0.0",
    docs_url="/swagger",
    redoc_url="/redoc",
)

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


# ── Global exception handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": str(exc)}},
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
