from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Property, PriceHistory, ScrapeRun
from app.schemas import StatsResponse

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("", response_model=StatsResponse)
async def get_stats(db: AsyncSession = Depends(get_db)):
    today_start = datetime.now(timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Total active
    total_active = (
        await db.execute(
            select(func.count()).where(Property.status == "active")
        )
    ).scalar() or 0

    # New today
    new_today = (
        await db.execute(
            select(func.count()).where(
                Property.first_seen_at >= today_start,
                Property.status == "active",
            )
        )
    ).scalar() or 0

    # Price drops today (from price_history)
    price_drops_today = (
        await db.execute(
            select(func.count(func.distinct(PriceHistory.property_id))).where(
                PriceHistory.recorded_at >= today_start
            )
        )
    ).scalar() or 0
    # Subtract new listings (they also get initial price_history entry)
    price_drops_today = max(0, price_drops_today - new_today)

    # Removed today
    removed_today = (
        await db.execute(
            select(func.count()).where(
                Property.status == "removed",
                Property.updated_at >= today_start,
            )
        )
    ).scalar() or 0

    # By source
    source_rows = (
        await db.execute(
            select(Property.source, func.count())
            .where(Property.status == "active")
            .group_by(Property.source)
        )
    ).all()
    by_source = {row[0]: row[1] for row in source_rows}

    # By property type
    type_rows = (
        await db.execute(
            select(Property.property_type, func.count())
            .where(Property.status == "active", Property.property_type.isnot(None))
            .group_by(Property.property_type)
        )
    ).all()
    by_type = {row[0]: row[1] for row in type_rows}

    # By transaction type
    trans_rows = (
        await db.execute(
            select(Property.transaction_type, func.count())
            .where(Property.status == "active", Property.transaction_type.isnot(None))
            .group_by(Property.transaction_type)
        )
    ).all()
    by_transaction = {row[0]: row[1] for row in trans_rows}

    return StatsResponse(
        total_active=total_active,
        new_today=new_today,
        price_drops_today=price_drops_today,
        removed_today=removed_today,
        by_source=by_source,
        by_type=by_type,
        by_transaction=by_transaction,
    )


@router.get("/scrape-runs")
async def get_scrape_runs(limit: int = 20, db: AsyncSession = Depends(get_db)):
    """Return recent scrape run history."""
    query = (
        select(ScrapeRun)
        .order_by(ScrapeRun.started_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    runs = result.scalars().all()

    return [
        {
            "id": r.id,
            "source": r.source,
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
            "listings_found": r.listings_found,
            "listings_new": r.listings_new,
            "listings_updated": r.listings_updated,
            "status": r.status,
        }
        for r in runs
    ]


@router.get("/cities")
async def get_cities(db: AsyncSession = Depends(get_db)):
    """Return list of cities with listing counts."""
    query = (
        select(Property.city, func.count())
        .where(Property.status == "active", Property.city.isnot(None), Property.city != "")
        .group_by(Property.city)
        .order_by(func.count().desc())
        .limit(50)
    )
    result = await db.execute(query)
    return [{"city": row[0], "count": row[1]} for row in result.all()]
