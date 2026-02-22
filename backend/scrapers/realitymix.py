"""Scrape monthly Praha 1-10 price statistics from RealityMix.cz."""

import logging
import re
from datetime import datetime, timezone

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

URLS = {
    "prodej": "https://realitymix.centrum.cz/statistika-nemovitosti/byty-prodej-prumerna-cena-za-1m2-bytu.html",
    "pronajem": "https://realitymix.centrum.cz/statistika-nemovitosti/byty-pronajem-prumerna-cena-pronajmu-1m2-mesic.html",
}

# Mapping of district names found in RealityMix tables to normalized region names
DISTRICT_NORMALIZE = {
    "Praha 1": "Praha 1",
    "Praha 2": "Praha 2",
    "Praha 3": "Praha 3",
    "Praha 4": "Praha 4",
    "Praha 5": "Praha 5",
    "Praha 6": "Praha 6",
    "Praha 7": "Praha 7",
    "Praha 8": "Praha 8",
    "Praha 9": "Praha 9",
    "Praha 10": "Praha 10",
}


def _parse_price(text_val: str) -> float | None:
    """Parse a Czech-formatted price string like '132 456' or '132456' into a float."""
    cleaned = re.sub(r"[^\d,.]", "", text_val.replace("\xa0", ""))
    cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _parse_price_table(html: str, transaction_type: str) -> list[dict]:
    """Parse RealityMix HTML and extract Praha district price data."""
    soup = BeautifulSoup(html, "lxml")
    results = []

    period = datetime.now(timezone.utc).strftime("%Y-%m")

    # Find all tables on the page
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all(["td", "th"])
            if len(cells) < 2:
                continue

            # First cell is typically the location name
            location = cells[0].get_text(strip=True)

            # Check if this is a Praha district
            matched_region = None
            for key, region in DISTRICT_NORMALIZE.items():
                if key in location:
                    matched_region = region
                    break

            if not matched_region:
                continue

            # Try to find a price value in remaining cells
            # Usually the last cell or the one with the most recent data
            for cell in reversed(cells[1:]):
                price = _parse_price(cell.get_text(strip=True))
                if price and price > 100:  # Sanity check
                    results.append({
                        "source": "realitymix",
                        "region": matched_region,
                        "property_type": "byt",
                        "transaction_type": transaction_type,
                        "price_m2": price,
                        "period": period,
                    })
                    break

    return results


async def fetch_realitymix_stats(session: AsyncSession) -> int:
    """Fetch Praha 1-10 price stats from RealityMix. Returns count of records upserted."""
    count = 0

    async with httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RealityTracker/1.0)"},
        follow_redirects=True,
    ) as client:
        for txn_type, url in URLS.items():
            try:
                resp = await client.get(url)
                resp.raise_for_status()
                rows = _parse_price_table(resp.text, txn_type)

                if not rows:
                    logger.warning(f"RealityMix: no data parsed from {txn_type} page")
                    continue

                for row in rows:
                    await session.execute(
                        text("""
                            INSERT INTO reference_benchmarks
                                (source, region, property_type, transaction_type, price_m2, period, fetched_at)
                            VALUES
                                (:source, :region, :property_type, :transaction_type, :price_m2, :period, NOW())
                            ON CONFLICT ON CONSTRAINT uq_ref_benchmark
                            DO UPDATE SET
                                price_m2 = EXCLUDED.price_m2,
                                fetched_at = NOW()
                        """),
                        row,
                    )
                    count += 1

                await session.commit()
                logger.info(f"RealityMix {txn_type}: upserted {len(rows)} district records")

            except Exception as e:
                logger.error(f"RealityMix fetch failed for {txn_type}: {e}")
                await session.rollback()

    return count
