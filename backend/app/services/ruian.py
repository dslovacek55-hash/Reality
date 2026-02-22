"""Load Prague katastrální území (KÚ) boundaries from bundled GeoJSON into PostGIS."""

import json
import logging
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data"
GEOJSON_PATH = DATA_DIR / "prague_ku_boundaries.geojson"


async def load_prague_ku_boundaries(session: AsyncSession) -> int:
    """Load Prague KÚ boundaries from bundled GeoJSON into prague_ku table.

    Idempotent — skips KÚ that already exist (ON CONFLICT DO NOTHING).
    Returns count of newly inserted records.
    """
    # Check if already loaded
    result = await session.execute(text("SELECT count(*) FROM prague_ku"))
    existing = result.scalar()
    if existing and existing > 100:
        logger.info(f"Prague KÚ boundaries already loaded ({existing} records), skipping.")
        return 0

    if not GEOJSON_PATH.exists():
        logger.error(f"Prague KÚ GeoJSON not found at {GEOJSON_PATH}")
        return 0

    logger.info(f"Loading Prague KÚ boundaries from {GEOJSON_PATH}...")

    with open(GEOJSON_PATH, encoding="utf-8") as f:
        geojson = json.load(f)

    features = geojson.get("features", [])
    if not features:
        logger.error("GeoJSON has no features")
        return 0

    count = 0
    for feature in features:
        props = feature.get("properties", {})
        geom = feature.get("geometry")

        # Try common property names for KÚ code and name
        ku_kod = (
            props.get("ku_kod")
            or props.get("KOD")
            or props.get("kod")
            or props.get("KOD_KU")
            or props.get("KU_KOD")
            or props.get("OBJECTID")
        )
        ku_nazev = (
            props.get("ku_nazev")
            or props.get("NAZEV")
            or props.get("nazev")
            or props.get("NAZEV_KU")
            or props.get("KU_NAZEV")
            or props.get("name")
            or ""
        )

        if not ku_kod or not geom:
            continue

        ku_kod = int(ku_kod)
        geom_json = json.dumps(geom)

        # Ensure geometry is MultiPolygon
        geom_type = geom.get("type", "")
        if geom_type == "Polygon":
            # Wrap single Polygon into MultiPolygon
            convert_expr = "ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:geom_json), 4326))"
        else:
            convert_expr = "ST_SetSRID(ST_GeomFromGeoJSON(:geom_json), 4326)"

        try:
            await session.execute(
                text(f"""
                    INSERT INTO prague_ku (ku_kod, ku_nazev, geom)
                    VALUES (:ku_kod, :ku_nazev, {convert_expr})
                    ON CONFLICT (ku_kod) DO NOTHING
                """),
                {"ku_kod": ku_kod, "ku_nazev": ku_nazev, "geom_json": geom_json},
            )
            count += 1
        except Exception as e:
            logger.warning(f"Failed to insert KÚ {ku_kod} ({ku_nazev}): {e}")
            continue

    await session.commit()
    logger.info(f"Loaded {count} Prague KÚ boundaries.")
    return count
