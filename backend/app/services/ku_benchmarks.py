"""Spatial assignment of KÚ codes to properties and benchmark computation."""

import logging

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def assign_ku_to_properties(session: AsyncSession) -> int:
    """Assign katastrální území codes to Prague properties using PostGIS spatial join.

    Only processes properties that:
    - Have GPS coordinates (latitude, longitude)
    - Don't have a KÚ code assigned yet (ku_kod IS NULL)

    Returns count of properties updated.
    """
    result = await session.execute(text("""
        UPDATE properties p
        SET ku_kod = ku.ku_kod, ku_nazev = ku.ku_nazev
        FROM prague_ku ku
        WHERE p.latitude IS NOT NULL
          AND p.longitude IS NOT NULL
          AND p.ku_kod IS NULL
          AND ST_Contains(
              ku.geom,
              ST_SetSRID(ST_MakePoint(p.longitude, p.latitude), 4326)
          )
    """))
    count = result.rowcount
    await session.commit()

    if count > 0:
        logger.info(f"Assigned KÚ codes to {count} properties.")
    return count


async def compute_ku_price_stats(session: AsyncSession) -> int:
    """Compute median and average CZK/m² per katastrální území.

    Groups by ku_kod, property_type, transaction_type.
    Requires at least 3 samples per group.
    Upserts into ku_price_stats table.

    Returns count of stats records upserted.
    """
    result = await session.execute(text("""
        INSERT INTO ku_price_stats
            (ku_kod, ku_nazev, property_type, transaction_type,
             median_price_m2, avg_price_m2, sample_count, computed_at)
        SELECT
            p.ku_kod,
            p.ku_nazev,
            p.property_type,
            p.transaction_type,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY p.price / p.size_m2),
            ROUND(AVG(p.price / p.size_m2), 0),
            COUNT(*),
            NOW()
        FROM properties p
        WHERE p.status = 'active'
          AND p.ku_kod IS NOT NULL
          AND p.price IS NOT NULL
          AND p.price > 0
          AND p.size_m2 > 0
          AND p.duplicate_of IS NULL
          AND p.transaction_type IS NOT NULL
          AND (p.price / p.size_m2) BETWEEN 5000 AND 500000
        GROUP BY p.ku_kod, p.ku_nazev, p.property_type, p.transaction_type
        HAVING COUNT(*) >= 3
        ON CONFLICT ON CONSTRAINT uq_ku_price_stats
        DO UPDATE SET
            ku_nazev = EXCLUDED.ku_nazev,
            median_price_m2 = EXCLUDED.median_price_m2,
            avg_price_m2 = EXCLUDED.avg_price_m2,
            sample_count = EXCLUDED.sample_count,
            computed_at = EXCLUDED.computed_at
    """))
    count = result.rowcount
    await session.commit()

    logger.info(f"Computed KÚ price stats: {count} records upserted.")
    return count
