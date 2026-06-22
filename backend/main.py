"""RupeeRadar — FastAPI Application Entry Point.

Initialises the app, registers routers, configures CORS,
and sets up lifecycle (startup/shutdown) hooks.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.core.config import settings
from backend.core.database import close_db, init_db
from backend.routers import analysis, report, upload

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s | %(name)-20s | %(levelname)-5s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle: startup and shutdown."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}...")
    await init_db()
    logger.info("Database initialized.")
    yield
    await close_db()
    logger.info("Database connections closed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-powered personal finance assistant that converts raw bank "
                "transaction data into meaningful financial insights.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(analysis.router)
app.include_router(report.router)


# ── Health-check ─────────────────────────────────────────
@app.get(
    "/api/health",
    tags=["Health"],
    summary="Health check",
    description="Returns the current status and version of the API.",
)
async def health_check():
    """Return service health status."""
    from backend.models.schemas import HealthResponse
    return HealthResponse(status="ok", version=settings.APP_VERSION)
