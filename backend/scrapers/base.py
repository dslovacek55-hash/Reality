import asyncio
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx
import redis.asyncio as aioredis
from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Property, ScrapeRun

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_DELAY = 5.0  # seconds


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
            limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        )
        self.redis = aioredis.from_url(settings.redis_url)
        self.run: ScrapeRun | None = None
        self.seen_ids: set[str] = set()

    async def fetch_with_retry(self, url: str, method: str = "GET", **kwargs) -> httpx.Response:
        """Fetch URL with retry logic for transient failures."""
        last_error = None
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                if method.upper() == "POST":
                    resp = await self.client.post(url, **kwargs)
                else:
                    resp = await self.client.get(url, **kwargs)
                resp.raise_for_status()
                return resp
            except (httpx.TransportError, httpx.HTTPStatusError) as e:
                last_error = e
                if attempt < MAX_RETRIES:
                    wait = RETRY_DELAY * attempt
                    logger.warning(
                        f"[{self.source}] Attempt {attempt}/{MAX_RETRIES} failed for {url}: {e}. "
                        f"Retrying in {wait}s..."
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        f"[{self.source}] All {MAX_RETRIES} attempts failed for {url}: {e}"
                    )
        raise last_error

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

    async def save_listing(self, data: dict) -> tuple[str, int | None]:
        """Upsert a single listing. Returns (status, property_id).
        Status is 'new', 'price_changed', or 'updated'."""
        external_id = data["external_id"]
        self.seen_ids.add(external_id)

        now = datetime.now(timezone.utc)

        # Check if listing already exists (before upsert)
        existing = (
            await self.db.execute(
                select(Property.id, Property.price)
                .where(Property.source == self.source, Property.external_id == external_id)
            )
        ).first()

        old_price = float(existing.price) if existing and existing.price else None

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
                last_seen_at=now,
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
                    "last_seen_at": now,
                },
            )
            .returning(Property.id)
        )

        result = await self.db.execute(stmt)
        row = result.fetchone()
        property_id = row.id if row else None

        if existing is None:
            return "new", property_id

        new_price = float(data["price"]) if data.get("price") else None
        if old_price and new_price and old_price != new_price:
            return "price_changed", property_id

        return "updated", property_id

    async def publish_event(self, event_type: str, property_id: int, extra: dict | None = None):
        """Publish a property event to Redis for the notification worker and SSE clients."""
        event = {
            "type": event_type,
            "property_id": property_id,
            "source": self.source,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if extra:
            event.update(extra)
        event_json = json.dumps(event)
        try:
            await self.redis.rpush("property_events", event_json)
            # Also publish to pubsub channel for SSE clients
            await self.redis.publish("property_updates", event_json)
        except Exception as e:
            logger.error(f"[{self.source}] Failed to publish event to Redis: {e}")

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
                    status, property_id = await self.save_listing(parsed)
                    if status == "new":
                        new_count += 1
                        if property_id:
                            await self.publish_event("new_listing", property_id)
                    elif status == "price_changed":
                        updated_count += 1
                        if property_id:
                            await self.publish_event(
                                "price_drop",
                                property_id,
                                {"old_price": float(parsed.get("price", 0))},
                            )
                    elif status == "updated":
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
            await self.redis.aclose()
