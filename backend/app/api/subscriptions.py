import re

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import EmailSubscription
from app.schemas import EmailSubscriptionCreate, EmailSubscriptionResponse

router = APIRouter(prefix="/api/subscriptions", tags=["subscriptions"])

EMAIL_RE = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


@router.post("", response_model=EmailSubscriptionResponse, status_code=201)
async def create_subscription(data: EmailSubscriptionCreate, db: AsyncSession = Depends(get_db)):
    if not EMAIL_RE.match(data.email):
        raise HTTPException(status_code=400, detail="Invalid email address")

    sub = EmailSubscription(
        email=data.email,
        property_type=data.property_type,
        transaction_type=data.transaction_type,
        city=data.city,
        disposition=data.disposition,
        price_min=data.price_min,
        price_max=data.price_max,
        size_min=data.size_min,
        size_max=data.size_max,
        notify_new=data.notify_new,
        notify_price_drop=data.notify_price_drop,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return EmailSubscriptionResponse.model_validate(sub)


@router.get("/{email}", response_model=list[EmailSubscriptionResponse])
async def get_subscriptions(email: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(EmailSubscription)
        .where(EmailSubscription.email == email, EmailSubscription.active == True)
        .order_by(EmailSubscription.created_at.desc())
    )
    return [EmailSubscriptionResponse.model_validate(s) for s in result.scalars().all()]


@router.delete("/{subscription_id}", status_code=204)
async def unsubscribe(subscription_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        update(EmailSubscription)
        .where(EmailSubscription.id == subscription_id)
        .values(active=False)
    )
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.commit()
