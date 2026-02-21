import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Property, ScrapeRun

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    source: str = ""
    base_url: str = ""

    def __init__(self, session: AsyncSession):
        self.db = session
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            },
        )
        self.run: ScrapeRun | None = None
        self.seen_ids: set[str] = set()

    async def start_run(self) -> ScrapeRun:
        self.run = ScrapeRun(source=self.source, status="running")
        self.db.add(self.run)
        await self.db.flush()
        return self.run

    async def finish_run(self, success: bool = True):
        if self.run:
            self.run.finished_at = datetime.now(timezone.utc)
            self.run.status = "completed" if success else "failed"
            await self.db.commit()

    @abstractmethod
    async def scrape(self) -> list[dict]:
        """Fetch all listings from the portal. Return list of parsed dicts."""
        ...

    @abstractmethod
    def parse_listing(self, raw: dict) -> dict:
        """Transform a raw API response item into a normalized dict."""
        ...

    async def save_listing(self, data: dict) -> str:
        """Upsert a single listing. Returns 'new', 'updated', or 'unchanged'."""
        external_id = data["external_id"]
        self.seen_ids.add(external_id)

        stmt = (
            insert(Property)
            .values(
                source=self.source,
                external_id=external_id,
                url=data.get("url"),
                title=data.get("title"),
                description=data.get("description"),
                property_type=data.get("property_type"),
                transaction_type=data.get("transaction_type"),
                disposition=data.get("disposition"),
                price=data.get("price"),
                size_m2=data.get("size_m2"),
                rooms=data.get("rooms"),
                latitude=data.get("latitude"),
                longitude=data.get("longitude"),
                city=data.get("city"),
                district=data.get("district"),
                address=data.get("address"),
                images=data.get("images", []),
                raw_data=data.get("raw_data", {}),
                status="active",
                missed_runs=0,
                last_seen_at=datetime.now(timezone.utc),
            )
            .on_conflict_do_update(
                constraint="uq_source_external",
                set_={
                    "title": data.get("title"),
                    "description": data.get("description"),
                    "price": data.get("price"),
                    "size_m2": data.get("size_m2"),
                    "rooms": data.get("rooms"),
                    "latitude": data.get("latitude"),
                    "longitude": data.get("longitude"),
                    "city": data.get("city"),
                    "district": data.get("district"),
                    "address": data.get("address"),
                    "images": data.get("images", []),
                    "raw_data": data.get("raw_data", {}),
                    "status": "active",
                    "missed_runs": 0,
                    "last_seen_at": datetime.now(timezone.utc),
                },
            )
            .returning(Property.id, Property.created_at, Property.updated_at)
        )

        result = await self.db.execute(stmt)
        row = result.fetchone()
        if row:
            if row.created_at == row.updated_at:
                return "new"
            return "updated"
        return "unchanged"

    async def mark_missing(self):
        """Increment missed_runs for listings from this source not seen in this run.
        Mark as removed if missed 3+ times."""
        if not self.seen_ids:
            return

        # Increment missed_runs for active listings not seen
        await self.db.execute(
            update(Property)
            .where(
                Property.source == self.source,
                Property.status == "active",
                Property.external_id.notin_(self.seen_ids),
            )
            .values(missed_runs=Property.missed_runs + 1)
        )

        # Mark removed if missed 3+ runs
        await self.db.execute(
            update(Property)
            .where(
                Property.source == self.source,
                Property.status == "active",
                Property.missed_runs >= 3,
            )
            .values(status="removed")
        )

    async def run_full(self):
        """Execute a complete scrape cycle."""
        await self.start_run()
        try:
            raw_listings = await self.scrape()
            self.run.listings_found = len(raw_listings)

            new_count = 0
            updated_count = 0

            for raw in raw_listings:
                try:
                    parsed = self.parse_listing(raw)
                    result = await self.save_listing(parsed)
                    if result == "new":
                        new_count += 1
                    elif result == "updated":
                        updated_count += 1
                except Exception as e:
                    logger.error(f"[{self.source}] Error processing listing: {e}")
                    continue

            self.run.listings_new = new_count
            self.run.listings_updated = updated_count

            await self.mark_missing()
            await self.finish_run(success=True)

            logger.info(
                f"[{self.source}] Scrape complete: {len(raw_listings)} found, "
                f"{new_count} new, {updated_count} updated"
            )
        except Exception as e:
            logger.error(f"[{self.source}] Scrape failed: {e}")
            await self.finish_run(success=False)
            raise
        finally:
            await self.client.aclose()
