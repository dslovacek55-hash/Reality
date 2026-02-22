import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Property

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/csv")
async def export_csv(
    property_type: str | None = None,
    transaction_type: str | None = None,
    city: str | None = None,
    status: str = "active",
    source: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Export properties as CSV file."""
    query = select(Property).where(Property.duplicate_of.is_(None))

    if status:
        query = query.where(Property.status == status)
    if property_type:
        query = query.where(Property.property_type == property_type)
    if transaction_type:
        query = query.where(Property.transaction_type == transaction_type)
    if city:
        query = query.where(Property.city == city)
    if source:
        query = query.where(Property.source == source)

    query = query.order_by(Property.first_seen_at.desc()).limit(5000)
    result = await db.execute(query)
    properties = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow([
        "ID", "Zdroj", "Nazev", "Typ", "Transakce", "Dispozice",
        "Cena (CZK)", "Plocha (m2)", "Cena/m2", "Mesto", "Okres",
        "Adresa", "Status", "URL", "Prvni videt", "Posledne videt",
    ])

    for p in properties:
        price_m2 = round(float(p.price) / float(p.size_m2), 0) if p.price and p.size_m2 and float(p.size_m2) > 0 else ""
        writer.writerow([
            p.id,
            p.source,
            p.title or "",
            p.property_type or "",
            p.transaction_type or "",
            p.disposition or "",
            float(p.price) if p.price else "",
            float(p.size_m2) if p.size_m2 else "",
            price_m2,
            p.city or "",
            p.district or "",
            p.address or "",
            p.status,
            p.url or "",
            p.first_seen_at.strftime("%Y-%m-%d %H:%M") if p.first_seen_at else "",
            p.last_seen_at.strftime("%Y-%m-%d %H:%M") if p.last_seen_at else "",
        ])

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"nemovitosti_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
