import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.properties import router as properties_router
from app.api.stats import router as stats_router
from app.api.filters import router as filters_router
from scrapers.scheduler import setup_scheduler, run_initial_scrape

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Real Estate Tracker backend...")
    setup_scheduler()
    # Run initial scrape in background
    asyncio.create_task(run_initial_scrape())
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="Czech Real Estate Tracker",
    description="API for tracking Czech real estate listings from Sreality, Bazos, and Bezrealitky",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(properties_router)
app.include_router(stats_router)
app.include_router(filters_router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "reality-tracker"}
