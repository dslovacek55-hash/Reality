import asyncio
import logging
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.properties import router as properties_router
from app.api.stats import router as stats_router
from app.api.filters import router as filters_router
from app.api.favorites import router as favorites_router
from app.api.export import router as export_router
from app.api.events import router as events_router
from app.api.images import router as images_router
from app.api.subscriptions import router as subscriptions_router
from app.config import settings
from app.database import engine
from app.middleware import RateLimitMiddleware
from scrapers.scheduler import setup_scheduler, run_initial_scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Store background task reference to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Real Estate Tracker backend...")
    setup_scheduler()
    # Run initial scrape in background, keep reference to prevent GC
    task = asyncio.create_task(run_initial_scrape())
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Czech Real Estate Tracker",
    description="API for tracking Czech real estate listings from Sreality, Bezrealitky, and iDNES",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RateLimitMiddleware, requests_per_minute=120)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties_router)
app.include_router(stats_router)
app.include_router(filters_router)
app.include_router(favorites_router)
app.include_router(export_router)
app.include_router(events_router)
app.include_router(images_router)
app.include_router(subscriptions_router)


@app.get("/api/health")
async def health():
    status = {"status": "ok", "service": "reality-tracker"}
    checks = {}

    # Check database
    try:
        async with engine.connect() as conn:
            await conn.execute(
                __import__("sqlalchemy").text("SELECT 1")
            )
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        status["status"] = "degraded"

    # Check Redis
    try:
        r = aioredis.from_url(settings.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"
        status["status"] = "degraded"

    status["checks"] = checks
    return status
