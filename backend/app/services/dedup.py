import logging
import math

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Property

logger = logging.getLogger(__name__)


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in meters between two GPS points."""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)

    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def compute_similarity_score(prop_a: dict, prop_b: dict) -> int:
    """Compute deduplication score between two properties.
    Score >= 5 means likely duplicate."""
    score = 0

    # GPS proximity (2 points)
    if all(
        v is not None
        for v in [
            prop_a.get("latitude"),
            prop_a.get("longitude"),
            prop_b.get("latitude"),
            prop_b.get("longitude"),
        ]
    ):
        dist = haversine_distance(
            prop_a["latitude"],
            prop_a["longitude"],
            prop_b["latitude"],
            prop_b["longitude"],
        )
        if dist <= 50:
            score += 2

    # Same disposition (1 point)
    if (
        prop_a.get("disposition")
        and prop_b.get("disposition")
        and prop_a["disposition"] == prop_b["disposition"]
    ):
        score += 1

    # Similar area ±5% (1 point)
    if prop_a.get("size_m2") and prop_b.get("size_m2"):
        ratio = prop_a["size_m2"] / prop_b["size_m2"]
        if 0.95 <= ratio <= 1.05:
            score += 1

    # Similar price ±10% (1 point)
    if prop_a.get("price") and prop_b.get("price"):
        ratio = prop_a["price"] / prop_b["price"]
        if 0.90 <= ratio <= 1.10:
            score += 1

    # Same property type + transaction type (1 point)
    if (
        prop_a.get("property_type") == prop_b.get("property_type")
        and prop_a.get("transaction_type") == prop_b.get("transaction_type")
    ):
        score += 1

    return score


async def run_deduplication(db: AsyncSession):
    """Find and link duplicate properties across different sources."""
    query = (
        select(Property)
        .where(
            Property.status == "active",
            Property.duplicate_of.is_(None),
            Property.latitude.isnot(None),
            Property.longitude.isnot(None),
        )
        .order_by(Property.first_seen_at.asc())
    )

    result = await db.execute(query)
    properties = result.scalars().all()

    # Group by source for cross-source comparison
    by_source: dict[str, list] = {}
    for prop in properties:
        by_source.setdefault(prop.source, []).append(prop)

    sources = list(by_source.keys())
    duplicates_found = 0

    for i, source_a in enumerate(sources):
        for source_b in sources[i + 1:]:
            for prop_a in by_source[source_a]:
                for prop_b in by_source[source_b]:
                    if prop_b.duplicate_of is not None:
                        continue

                    prop_a_dict = {
                        "latitude": prop_a.latitude,
                        "longitude": prop_a.longitude,
                        "disposition": prop_a.disposition,
                        "size_m2": float(prop_a.size_m2) if prop_a.size_m2 else None,
                        "price": float(prop_a.price) if prop_a.price else None,
                        "property_type": prop_a.property_type,
                        "transaction_type": prop_a.transaction_type,
                    }
                    prop_b_dict = {
                        "latitude": prop_b.latitude,
                        "longitude": prop_b.longitude,
                        "disposition": prop_b.disposition,
                        "size_m2": float(prop_b.size_m2) if prop_b.size_m2 else None,
                        "price": float(prop_b.price) if prop_b.price else None,
                        "property_type": prop_b.property_type,
                        "transaction_type": prop_b.transaction_type,
                    }

                    score = compute_similarity_score(prop_a_dict, prop_b_dict)
                    if score >= 5:
                        # Link newer to older
                        older = prop_a if prop_a.first_seen_at <= prop_b.first_seen_at else prop_b
                        newer = prop_b if older is prop_a else prop_a
                        newer.duplicate_of = older.id
                        duplicates_found += 1

    if duplicates_found > 0:
        await db.commit()
        logger.info(f"Deduplication: found {duplicates_found} duplicates")
    else:
        logger.info("Deduplication: no new duplicates found")
