"""Fetch quarterly rental price data from Ministry of Finance cenová mapa nájmů.

The MF publishes min/max/median rent per m² by katastrální území within Prague,
segmented by apartment layout (1+kk through 4+kk) and construction type.
Updated quarterly at: mf.gov.cz/cs/rozpoctova-politika/podpora-projektoveho-rizeni/cenova-mapa

Data format: The MF site provides an interactive map backed by a GIS service.
The underlying data is typically available via WMS/WFS or as downloadable files.
This scraper attempts to fetch the data from the service endpoints.
"""

import logging
import re

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

# Known MF cenová mapa API endpoints
# These may need updating as the MF site changes
MF_BASE_URL = "https://www.mfcr.cz"
MF_MAP_URL = "https://www.mfcr.cz/cs/rozpoctova-politika/podpora-projektoveho-rizeni/cenova-mapa"

# ArcGIS REST service that backs the MF rental map (if available)
MF_ARCGIS_URL = None  # Will be populated after page inspection


async def _discover_data_endpoint(client: httpx.AsyncClient) -> str | None:
    """Try to discover the actual data endpoint from the MF map page."""
    try:
        resp = await client.get(MF_MAP_URL, follow_redirects=True)
        resp.raise_for_status()

        # Look for ArcGIS / GIS service URLs in the page source
        patterns = [
            r'(https?://[^"\']+/arcgis/rest/services/[^"\']+)',
            r'(https?://[^"\']+/wfs[^"\']*)',
            r'(https?://[^"\']+\.geojson)',
            r'(https?://[^"\']+/api/[^"\']*rent[^"\']*)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, resp.text, re.IGNORECASE)
            if matches:
                logger.info(f"MF rental: discovered endpoint: {matches[0]}")
                return matches[0]

        logger.warning("MF rental: no data endpoint found in map page")
        return None

    except Exception as e:
        logger.error(f"MF rental: failed to access map page: {e}")
        return None


async def _fetch_from_arcgis(client: httpx.AsyncClient, endpoint: str) -> list[dict]:
    """Fetch KÚ-level rental data from ArcGIS REST service."""
    results = []
    try:
        # Query all features
        query_url = f"{endpoint}/query"
        params = {
            "where": "1=1",
            "outFields": "*",
            "f": "json",
            "returnGeometry": "false",
        }
        resp = await client.get(query_url, params=params)
        resp.raise_for_status()
        data = resp.json()

        for feature in data.get("features", []):
            attrs = feature.get("attributes", {})
            ku_name = attrs.get("NAZEV_KU") or attrs.get("nazev") or attrs.get("KU_NAZEV")
            median_rent = attrs.get("MEDIAN") or attrs.get("median_rent") or attrs.get("cena_median")
            if ku_name and median_rent:
                results.append({
                    "source": "mf_rental",
                    "region": ku_name,
                    "property_type": "byt",
                    "transaction_type": "pronajem",
                    "price_m2": float(median_rent),
                })
    except Exception as e:
        logger.error(f"MF rental: ArcGIS query failed: {e}")

    return results


async def fetch_mf_rental_data(session: AsyncSession) -> int:
    """Fetch quarterly MF rental price map data. Returns count of records upserted.

    This function attempts to discover and fetch data from the MF's web service.
    If the data format changes, it logs warnings and returns 0 gracefully.
    """
    from datetime import datetime, timezone
    quarter = (datetime.now(timezone.utc).month - 1) // 3 + 1
    year = datetime.now(timezone.utc).year
    period = f"{year}-Q{quarter}"

    count = 0

    async with httpx.AsyncClient(
        timeout=30.0,
        headers={"User-Agent": "Mozilla/5.0 (compatible; RealityTracker/1.0)"},
        follow_redirects=True,
    ) as client:
        # Step 1: Try to discover the data endpoint
        endpoint = await _discover_data_endpoint(client)

        records = []
        if endpoint and "arcgis" in endpoint.lower():
            records = await _fetch_from_arcgis(client, endpoint)

        if not records:
            logger.warning(
                "MF rental: no data fetched. The MF site may have changed. "
                "Manual inspection of the cenová mapa page is needed."
            )
            return 0

        # Step 2: Upsert records
        for record in records:
            record["period"] = period
            try:
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
                    record,
                )
                count += 1
            except Exception as e:
                logger.warning(f"MF rental: failed to upsert record for {record.get('region')}: {e}")

        await session.commit()
        logger.info(f"MF rental: upserted {count} KÚ rental records for {period}")

    return count
