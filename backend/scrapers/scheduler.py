import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import async_session
from scrapers.sreality import SrealityScraper
from scrapers.bazos import BazosScraper
from scrapers.bezrealitky import BezrealitkyScraper

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def run_scraper(scraper_class):
    """Run a scraper within its own database session."""
    async with async_session() as session:
        scraper = scraper_class(session)
        try:
            await scraper.run_full()
        except Exception as e:
            logger.error(f"Scraper {scraper_class.source} failed: {e}")


async def run_sreality():
    logger.info("Starting Sreality scrape...")
    await run_scraper(SrealityScraper)


async def run_bazos():
    logger.info("Starting Bazos scrape...")
    await run_scraper(BazosScraper)


async def run_bezrealitky():
    logger.info("Starting Bezrealitky scrape...")
    await run_scraper(BezrealitkyScraper)


def setup_scheduler():
    """Configure and start the APScheduler."""
    scheduler.add_job(
        run_sreality,
        "interval",
        minutes=settings.sreality_interval_minutes,
        id="sreality_scraper",
        name="Sreality Scraper",
        max_instances=1,
    )
    scheduler.add_job(
        run_bazos,
        "interval",
        minutes=settings.bazos_interval_minutes,
        id="bazos_scraper",
        name="Bazos Scraper",
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

    scheduler.start()
    logger.info("Scheduler started with intervals: "
                f"Sreality={settings.sreality_interval_minutes}min, "
                f"Bazos={settings.bazos_interval_minutes}min, "
                f"Bezrealitky={settings.bezrealitky_interval_minutes}min")


async def run_initial_scrape():
    """Run all scrapers once at startup with staggered delays."""
    logger.info("Running initial scrape for all sources...")
    await run_sreality()
    await asyncio.sleep(5)
    await run_bazos()
    await asyncio.sleep(5)
    await run_bezrealitky()
    logger.info("Initial scrape completed.")
