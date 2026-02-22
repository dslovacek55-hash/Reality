import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.config import settings
from app.database import async_session
from app.services.dedup import run_deduplication
from app.services.ruian import load_prague_ku_boundaries
from app.services.ku_benchmarks import assign_ku_to_properties, compute_ku_price_stats
from scrapers.sreality import SrealityScraper
from scrapers.bezrealitky import BezrealitkyScraper
from scrapers.idnes import IdnesScraper
from scrapers.realitymix import fetch_realitymix_stats
from scrapers.mf_rental import fetch_mf_rental_data

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_scraper(scraper_class):
    """Run a scraper within its own database session, then run deduplication."""
    async with async_session() as session:
        scraper = scraper_class(session)
        try:
            await scraper.run_full()
        except Exception as e:
            logger.error(f"Scraper {scraper_class.source} failed: {e}")

    # Run deduplication after each scrape
    async with async_session() as session:
        try:
            await run_deduplication(session)
        except Exception as e:
            logger.error(f"Deduplication after {scraper_class.source} failed: {e}")


async def run_sreality():
    logger.info("Starting Sreality scrape...")
    await run_scraper(SrealityScraper)


async def run_bezrealitky():
    logger.info("Starting Bezrealitky scrape...")
    await run_scraper(BezrealitkyScraper)


async def run_idnes():
    logger.info("Starting iDNES Reality scrape...")
    await run_scraper(IdnesScraper)


async def run_ku_pipeline():
    """Assign KÚ codes to Prague properties and recompute price benchmarks."""
    logger.info("Starting KÚ assignment and benchmark computation...")
    async with async_session() as session:
        try:
            assigned = await assign_ku_to_properties(session)
            stats = await compute_ku_price_stats(session)
            logger.info(f"KÚ pipeline: assigned {assigned} properties, "
                        f"computed {stats} benchmark records")
        except Exception as e:
            logger.error(f"KÚ pipeline failed: {e}")


async def run_realitymix():
    """Fetch monthly district-level stats from RealityMix."""
    logger.info("Starting RealityMix stats fetch...")
    async with async_session() as session:
        try:
            count = await fetch_realitymix_stats(session)
            logger.info(f"RealityMix: upserted {count} benchmark records")
        except Exception as e:
            logger.error(f"RealityMix fetch failed: {e}")


async def run_mf_rental():
    """Fetch quarterly KÚ-level rental data from Ministry of Finance."""
    logger.info("Starting MF rental data fetch...")
    async with async_session() as session:
        try:
            count = await fetch_mf_rental_data(session)
            logger.info(f"MF rental: upserted {count} benchmark records")
        except Exception as e:
            logger.error(f"MF rental fetch failed: {e}")


def setup_scheduler():
    """Configure and start the APScheduler."""
    # Listing scrapers
    scheduler.add_job(
        run_sreality,
        "interval",
        minutes=settings.sreality_interval_minutes,
        id="sreality_scraper",
        name="Sreality Scraper",
        max_instances=1,
    )
    scheduler.add_job(
        run_bezrealitky,
        "interval",
        minutes=settings.bezrealitky_interval_minutes,
        id="bezrealitky_scraper",
        name="Bezrealitky Scraper",
        max_instances=1,
    )
    scheduler.add_job(
        run_idnes,
        "interval",
        minutes=settings.idnes_interval_minutes,
        id="idnes_scraper",
        name="iDNES Reality Scraper",
        max_instances=1,
    )

    # KÚ assignment + benchmark computation: daily at 3 AM
    scheduler.add_job(
        run_ku_pipeline,
        "cron",
        hour=3,
        id="ku_pipeline",
        name="KÚ Assignment & Benchmarks",
        max_instances=1,
    )

    # RealityMix district stats: monthly (1st of each month, 6 AM)
    scheduler.add_job(
        run_realitymix,
        "cron",
        day=1,
        hour=6,
        id="realitymix_scraper",
        name="RealityMix Monthly Stats",
        max_instances=1,
    )

    # MF rental price map: quarterly (Jan/Apr/Jul/Oct 15th, 7 AM)
    scheduler.add_job(
        run_mf_rental,
        "cron",
        month="1,4,7,10",
        day=15,
        hour=7,
        id="mf_rental_scraper",
        name="MF Rental Price Map",
        max_instances=1,
    )

    scheduler.start()
    logger.info("Scheduler started with intervals: "
                f"Sreality={settings.sreality_interval_minutes}min, "
                f"Bezrealitky={settings.bezrealitky_interval_minutes}min, "
                f"iDNES={settings.idnes_interval_minutes}min, "
                "KÚ=daily@3am, RealityMix=monthly, MF rental=quarterly")


async def run_initial_scrape():
    """Run all scrapers once at startup with staggered delays."""
    logger.info("Running initial scrape for all sources...")

    # Load RUIAN KÚ boundaries first (fast, idempotent)
    async with async_session() as session:
        try:
            await load_prague_ku_boundaries(session)
        except Exception as e:
            logger.error(f"RUIAN KÚ load failed: {e}")

    # Run listing scrapers
    await run_sreality()
    await asyncio.sleep(5)
    await run_bezrealitky()
    await asyncio.sleep(5)
    await run_idnes()

    # Run KÚ pipeline after listings are loaded
    await run_ku_pipeline()

    # Fetch external benchmarks (non-blocking)
    try:
        await run_realitymix()
    except Exception as e:
        logger.error(f"Initial RealityMix fetch failed: {e}")

    logger.info("Initial scrape completed.")
