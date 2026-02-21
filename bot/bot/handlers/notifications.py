import asyncio
import json
import logging

import redis.asyncio as aioredis
from aiogram import Bot
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.config import bot_settings

logger = logging.getLogger(__name__)


async def notification_worker(
    bot: Bot,
    session_maker: async_sessionmaker[AsyncSession],
    redis_url: str,
):
    """Background worker that polls Redis for new listing events and sends notifications."""
    redis_client = aioredis.from_url(redis_url)

    logger.info("Notification worker started")

    while True:
        try:
            # Pop event from Redis queue
            raw = await redis_client.lpop("property_events")
            if not raw:
                await asyncio.sleep(5)
                continue

            event = json.loads(raw)
            event_type = event.get("type")  # 'new_listing' or 'price_drop'
            property_id = event.get("property_id")

            if not property_id:
                continue

            async with session_maker() as db:
                await process_event(bot, db, event_type, property_id, event)

        except Exception as e:
            logger.error(f"Notification worker error: {e}")
            await asyncio.sleep(10)


async def process_event(
    bot: Bot,
    db: AsyncSession,
    event_type: str,
    property_id: int,
    event: dict,
):
    """Match event against user filters and send notifications."""
    from bot.main import Property, UserFilter, Notification

    # Get property
    prop = (
        await db.execute(select(Property).where(Property.id == property_id))
    ).scalar_one_or_none()

    if not prop:
        return

    # Find matching filters
    query = select(UserFilter).where(UserFilter.active == True)
    filters_result = await db.execute(query)
    user_filters = filters_result.scalars().all()

    for uf in user_filters:
        if not matches_filter(prop, uf, event_type):
            continue

        # Check if already notified
        existing = (
            await db.execute(
                select(Notification).where(
                    Notification.user_filter_id == uf.id,
                    Notification.property_id == property_id,
                    Notification.notification_type == event_type,
                )
            )
        ).scalar_one_or_none()

        if existing:
            continue

        # Send notification
        try:
            message = format_notification(prop, event_type, event)
            await bot.send_message(
                chat_id=uf.telegram_chat_id,
                text=message,
                parse_mode="HTML",
                disable_web_page_preview=False,
            )

            # Log notification
            notif = Notification(
                user_filter_id=uf.id,
                property_id=property_id,
                notification_type=event_type,
            )
            db.add(notif)
            await db.commit()

            logger.info(
                f"Sent {event_type} notification to chat {uf.telegram_chat_id} "
                f"for property {property_id}"
            )
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


def matches_filter(prop, uf, event_type: str) -> bool:
    """Check if a property matches a user filter."""
    if event_type == "new_listing" and not uf.notify_new:
        return False
    if event_type == "price_drop" and not uf.notify_price_drop:
        return False

    if uf.property_type and prop.property_type != uf.property_type:
        return False
    if uf.transaction_type and prop.transaction_type != uf.transaction_type:
        return False
    if uf.city and prop.city and uf.city.lower() not in prop.city.lower():
        return False
    if uf.price_min and prop.price and float(prop.price) < float(uf.price_min):
        return False
    if uf.price_max and prop.price and float(prop.price) > float(uf.price_max):
        return False
    if uf.size_min and prop.size_m2 and float(prop.size_m2) < float(uf.size_min):
        return False
    if uf.size_max and prop.size_m2 and float(prop.size_m2) > float(uf.size_max):
        return False
    if uf.disposition and prop.disposition:
        allowed = [d.strip() for d in uf.disposition.split(",")]
        if prop.disposition not in allowed:
            return False

    return True


def format_notification(prop, event_type: str, event: dict) -> str:
    """Format a notification message."""
    if event_type == "new_listing":
        emoji = "🏠"
        header = "Novy inzerat"
    elif event_type == "price_drop":
        emoji = "📉"
        old_price = event.get("old_price", 0)
        new_price = float(prop.price) if prop.price else 0
        pct = ((old_price - new_price) / old_price * 100) if old_price else 0
        header = f"Pokles ceny o {pct:.1f}%"
    else:
        emoji = "ℹ️"
        header = "Aktualizace"

    price_str = f"{int(float(prop.price)):,} CZK".replace(",", " ") if prop.price else "N/A"
    size_str = f"{prop.size_m2} m²" if prop.size_m2 else "N/A"

    lines = [
        f"{emoji} <b>{header}</b>",
        f"",
        f"<b>{prop.title or 'Bez nazvu'}</b>",
        f"📍 {prop.city or ''} {prop.district or ''}".strip(),
        f"💰 {price_str}",
        f"📐 {size_str} | {prop.disposition or 'N/A'}",
        f"🔗 {prop.source.capitalize()}",
    ]

    if event_type == "price_drop":
        old_price = event.get("old_price", 0)
        old_str = f"{int(old_price):,} CZK".replace(",", " ")
        lines.insert(3, f"💰 <s>{old_str}</s> → {price_str}")
        lines.pop(5)  # Remove duplicate price line

    if prop.url:
        lines.append(f"\n<a href=\"{prop.url}\">Zobrazit inzerat</a>")

    return "\n".join(lines)
