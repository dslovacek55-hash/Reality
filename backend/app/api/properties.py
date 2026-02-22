import math
from datetime import datetime, timedelta, timezone
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Property, PriceHistory
from app.schemas import (
    PropertyResponse,
    PropertyDetailResponse,
    PropertyListResponse,
    PriceHistoryResponse,
)

router = APIRouter(prefix="/api/properties", tags=["properties"])


def escape_like(value: str) -> str:
    """Escape special LIKE characters (%, _) in user input."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


VALID_SORTS = {"newest", "price_asc", "price_desc", "size_asc", "size_desc"}
VALID_STATUSES = {"active", "removed", "sold"}
VALID_PROPERTY_TYPES = {"byt", "dum", "pozemek", "komercni"}
VALID_TRANSACTION_TYPES = {"prodej", "pronajem"}
VALID_SOURCES = {"sreality", "bezrealitky", "idnes"}


@router.get("", response_model=PropertyListResponse)
async def list_properties(
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    property_type: str | None = None,
    transaction_type: str | None = None,
    city: str | None = None,
    district: str | None = None,
    disposition: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    size_min: float | None = None,
    size_max: float | None = None,
    status: str = "active",
    source: str | None = None,
    sort: str = "newest",
    search: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(Property).where(Property.duplicate_of.is_(None))

    if status:
        if status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
        query = query.where(Property.status == status)
    if property_type:
        if property_type not in VALID_PROPERTY_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid property_type: {property_type}")
        query = query.where(Property.property_type == property_type)
    if transaction_type:
        if transaction_type not in VALID_TRANSACTION_TYPES:
            raise HTTPException(status_code=400, detail=f"Invalid transaction_type: {transaction_type}")
        query = query.where(Property.transaction_type == transaction_type)
    if city:
        escaped = escape_like(city)
        query = query.where(Property.city.ilike(f"%{escaped}%", escape="\\"))
    if district:
        escaped = escape_like(district)
        query = query.where(Property.district.ilike(f"%{escaped}%", escape="\\"))
    if disposition:
        dispositions = [d.strip() for d in disposition.split(",")]
        query = query.where(Property.disposition.in_(dispositions))
    if price_min is not None:
        query = query.where(Property.price >= price_min)
    if price_max is not None:
        query = query.where(Property.price <= price_max)
    if size_min is not None:
        query = query.where(Property.size_m2 >= size_min)
    if size_max is not None:
        query = query.where(Property.size_m2 <= size_max)
    if source:
        if source not in VALID_SOURCES:
            raise HTTPException(status_code=400, detail=f"Invalid source: {source}")
        query = query.where(Property.source == source)
    if search:
        search_stripped = search.strip()
        if search_stripped:
            # Use PostgreSQL full-text search with tsvector/tsquery
            ts_query = func.plainto_tsquery("simple", search_stripped)
            query = query.where(Property.search_vector.op("@@")(ts_query))

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    # Sort
    if sort not in VALID_SORTS:
        sort = "newest"

    if sort == "newest":
        query = query.order_by(Property.first_seen_at.desc())
    elif sort == "price_asc":
        query = query.order_by(Property.price.asc().nullslast())
    elif sort == "price_desc":
        query = query.order_by(Property.price.desc().nullslast())
    elif sort == "size_asc":
        query = query.order_by(Property.size_m2.asc().nullslast())
    elif sort == "size_desc":
        query = query.order_by(Property.size_m2.desc().nullslast())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    result = await db.execute(query)
    items = result.scalars().all()

    return PropertyListResponse(
        items=[PropertyResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total > 0 else 0,
    )


# IMPORTANT: /geo/markers must be defined BEFORE /{property_id}
# to avoid FastAPI matching "geo" as a property_id
@router.get("/geo/markers")
async def get_map_markers(
    property_type: str | None = None,
    transaction_type: str | None = None,
    city: str | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return minimal property data for map markers."""
    query = select(
        Property.id,
        Property.latitude,
        Property.longitude,
        Property.price,
        Property.disposition,
        Property.title,
        Property.source,
    ).where(
        Property.status == "active",
        Property.latitude.isnot(None),
        Property.longitude.isnot(None),
        Property.duplicate_of.is_(None),
    )

    if property_type:
        query = query.where(Property.property_type == property_type)
    if transaction_type:
        query = query.where(Property.transaction_type == transaction_type)
    if city:
        escaped = escape_like(city)
        query = query.where(Property.city.ilike(f"%{escaped}%", escape="\\"))
    if price_min is not None:
        query = query.where(Property.price >= price_min)
    if price_max is not None:
        query = query.where(Property.price <= price_max)

    query = query.limit(2000)
    result = await db.execute(query)

    markers = []
    for row in result.all():
        markers.append({
            "id": row.id,
            "lat": row.latitude,
            "lng": row.longitude,
            "price": float(row.price) if row.price else None,
            "disposition": row.disposition,
            "title": row.title,
            "source": row.source,
        })

    return markers


@router.get("/{property_id}", response_model=PropertyDetailResponse)
async def get_property(property_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(Property)
        .options(selectinload(Property.price_history))
        .where(Property.id == property_id)
    )
    result = await db.execute(query)
    prop = result.scalar_one_or_none()

    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    return PropertyDetailResponse.model_validate(prop)


@router.get("/{property_id}/price-history", response_model=list[PriceHistoryResponse])
async def get_price_history(property_id: int, db: AsyncSession = Depends(get_db)):
    query = (
        select(PriceHistory)
        .where(PriceHistory.property_id == property_id)
        .order_by(PriceHistory.recorded_at.asc())
    )
    result = await db.execute(query)
    return [PriceHistoryResponse.model_validate(ph) for ph in result.scalars().all()]
