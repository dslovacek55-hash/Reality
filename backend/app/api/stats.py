from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Property, PriceHistory, ScrapeRun
from app.schemas import StatsResponse
from app.reference_prices import (
    get_reference_price_async,
    normalize_city,
    get_base_city,
    get_city_display_name,
)

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

    # Price drops today: count properties where today's price_history entry
    # is lower than the previous entry (actual price decrease, not just any change)
    prev_price = (
        select(
            PriceHistory.property_id,
            PriceHistory.price,
            func.row_number().over(
                partition_by=PriceHistory.property_id,
                order_by=PriceHistory.recorded_at.desc(),
            ).label("rn"),
        )
        .where(PriceHistory.recorded_at < today_start)
        .subquery()
    )
    latest_prev = (
        select(prev_price.c.property_id, prev_price.c.price)
        .where(prev_price.c.rn == 1)
        .subquery()
    )
    today_price = (
        select(
            PriceHistory.property_id,
            func.min(PriceHistory.price).label("price"),
        )
        .where(PriceHistory.recorded_at >= today_start)
        .group_by(PriceHistory.property_id)
        .subquery()
    )
    price_drops_today = (
        await db.execute(
            select(func.count()).select_from(
                today_price.join(
                    latest_prev,
                    today_price.c.property_id == latest_prev.c.property_id,
                )
            ).where(today_price.c.price < latest_prev.c.price)
        )
    ).scalar() or 0

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
    """Return list of base cities (Praha, Brno, ...) with listing counts."""
    query = (
        select(Property.city, func.count().label("cnt"))
        .where(Property.status == "active", Property.city.isnot(None), Property.city != "")
        .group_by(Property.city)
    )
    rows = (await db.execute(query)).all()

    # Group street-level city strings into base cities
    city_counts: dict[str, int] = {}
    for city_str, cnt in rows:
        base = get_base_city(city_str)
        city_counts[base] = city_counts.get(base, 0) + cnt

    sorted_cities = sorted(city_counts.items(), key=lambda x: -x[1])[:50]
    return [
        {"city": base, "label": get_city_display_name(base), "count": cnt}
        for base, cnt in sorted_cities
    ]


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


async def _compute_avg_prices(
    db: AsyncSession,
    base_where: list,
    txn: str,
    property_type: str | None,
    disposition: str | None,
) -> dict[str, dict]:
    """Core logic: compute KÚ / city averages and reference prices.

    Returns {city_string: entry_dict}.
    """
    price_per_m2_expr = Property.price / Property.size_m2

    # Q1: KÚ-level averages
    ku_avg_q = (
        select(
            Property.ku_kod,
            func.min(Property.ku_nazev).label("ku_nazev"),
            func.round(func.avg(price_per_m2_expr), 0).label("avg_price_m2"),
            func.count().label("sample_count"),
        )
        .where(*base_where, Property.ku_kod.isnot(None))
        .group_by(Property.ku_kod)
        .having(func.count() >= 2)
    )
    ku_avg = {r.ku_kod: r for r in (await db.execute(ku_avg_q)).all()}

    ku_name_lookup: dict[str, int] = {}
    for kk, kr in ku_avg.items():
        if kr.ku_nazev:
            ku_name_lookup[normalize_city(kr.ku_nazev)] = kk

    # Q2: City-level averages (non-Prague / no KÚ)
    city_avg_q = (
        select(
            Property.city,
            func.round(func.avg(price_per_m2_expr), 0).label("avg_price_m2"),
            func.count().label("sample_count"),
        )
        .where(*base_where, Property.ku_kod.is_(None))
        .group_by(Property.city)
        .having(func.count() >= 2)
    )
    city_avg = {r.city: r for r in (await db.execute(city_avg_q)).all()}

    # Q3: All distinct (city, ku_kod) pairs
    pairs_q = select(Property.city, Property.ku_kod).where(*base_where).distinct()
    all_pairs = (await db.execute(pairs_q)).all()

    # Q4/Q5: Disposition averages (optional)
    disp_ku: dict[str, dict] = {}
    disp_city: dict[str, dict] = {}
    if disposition:
        dispositions = [d.strip() for d in disposition.split(",") if d.strip()]
        if dispositions:
            q4 = (
                select(
                    Property.ku_kod, Property.disposition,
                    func.round(func.avg(price_per_m2_expr), 0).label("avg"),
                    func.count().label("cnt"),
                )
                .where(*base_where, Property.ku_kod.isnot(None), Property.disposition.in_(dispositions))
                .group_by(Property.ku_kod, Property.disposition)
                .having(func.count() >= 2)
            )
            for r in (await db.execute(q4)).all():
                disp_ku[f"{r.ku_kod}|{r.disposition}"] = {
                    "avg_price_m2": float(r.avg), "count": r.cnt,
                }
            q5 = (
                select(
                    Property.city, Property.disposition,
                    func.round(func.avg(price_per_m2_expr), 0).label("avg"),
                    func.count().label("cnt"),
                )
                .where(*base_where, Property.ku_kod.is_(None), Property.disposition.in_(dispositions))
                .group_by(Property.city, Property.disposition)
                .having(func.count() >= 2)
            )
            for r in (await db.execute(q5)).all():
                disp_city[f"{r.city}|{r.disposition}"] = {
                    "avg_price_m2": float(r.avg), "count": r.cnt,
                }

    def _match_ku(city_str: str) -> int | None:
        norm = normalize_city(city_str)
        if not norm.startswith("praha-"):
            return None
        parts = norm[6:].split("-")
        while parts and parts[0].isdigit():
            parts = parts[1:]
        for length in range(1, min(len(parts) + 1, 4)):
            c = "-".join(parts[:length])
            if c in ku_name_lookup:
                return ku_name_lookup[c]
        return None

    result: dict[str, dict] = {}
    ref_cache: dict[int | str, tuple[float | None, str | None]] = {}

    for city_name, ku_kod in all_pairs:
        if city_name in result:
            continue

        entry: dict = {}
        eff_ku = ku_kod or _match_ku(city_name)

        if eff_ku and eff_ku in ku_avg:
            d = ku_avg[eff_ku]
            entry["avg_price_m2"] = float(d.avg_price_m2)
            entry["count"] = d.sample_count
        elif city_name in city_avg:
            d = city_avg[city_name]
            entry["avg_price_m2"] = float(d.avg_price_m2)
            entry["count"] = d.sample_count

        cache_key = eff_ku or city_name
        if cache_key not in ref_cache:
            ref_cache[cache_key] = await get_reference_price_async(
                session=db, city=city_name, transaction_type=txn,
                property_type=property_type,
            )
        ref_price, ref_label = ref_cache[cache_key]
        if ref_price:
            entry["czso_price_m2"] = ref_price
            entry["czso_region"] = ref_label

        if disposition:
            for d in [x.strip() for x in disposition.split(",") if x.strip()]:
                if eff_ku and f"{eff_ku}|{d}" in disp_ku:
                    entry["by_disposition"] = disp_ku[f"{eff_ku}|{d}"]
                    break
                if f"{city_name}|{d}" in disp_city:
                    entry["by_disposition"] = disp_city[f"{city_name}|{d}"]
                    break

        if entry.get("avg_price_m2") or entry.get("czso_price_m2"):
            result[city_name] = entry

    return result


@router.get("/avg-price-m2")
async def get_avg_price_m2(
    city: str | None = None,
    property_type: str | None = None,
    transaction_type: str | None = None,
    disposition: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Return average price per m2 for each city string.

    Prague properties are aggregated at KÚ level (Karlín, Žižkov, ...).
    Prodej and pronájem are ALWAYS computed separately (never mixed).
    When transaction_type is not specified, response keys use 'city|txn' format.
    """
    base_where = [
        Property.status == "active",
        Property.price.isnot(None),
        Property.size_m2 > 0,
        Property.city.isnot(None),
        Property.city != "",
        Property.duplicate_of.is_(None),
    ]
    if property_type:
        base_where.append(Property.property_type == property_type)
    if city:
        escaped = _escape_like(city)
        base_where.append(Property.city.ilike(f"%{escaped}%", escape="\\"))

    if transaction_type:
        # Single transaction type: keys are plain city strings
        base_where.append(Property.transaction_type == transaction_type)
        return await _compute_avg_prices(db, base_where, transaction_type, property_type, disposition)
    else:
        # No filter: compute separately for prodej and pronájem, use compound keys
        result: dict[str, dict] = {}
        for txn in ["prodej", "pronajem"]:
            sub_where = base_where + [Property.transaction_type == txn]
            sub_result = await _compute_avg_prices(db, sub_where, txn, property_type, disposition)
            for city_name, entry in sub_result.items():
                result[f"{city_name}|{txn}"] = entry
        return result
