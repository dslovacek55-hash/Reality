import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from bot.config import bot_settings
from bot.handlers import start, filters
from bot.handlers.notifications import notification_worker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Database setup (reuse same schema as backend)
engine = create_async_engine(bot_settings.database_url, echo=False)
session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# Import models (we need to define them here or import from shared location)
# For simplicity, define lightweight model references
from sqlalchemy import (
    BigInteger, Boolean, DateTime, ForeignKey, Integer, Numeric,
    String, Text, Float,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func


class Property(Base):
    __tablename__ = "properties"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    source: Mapped[str] = mapped_column(String(50))
    external_id: Mapped[str] = mapped_column(String(100))
    url: Mapped[str | None] = mapped_column(Text)
    title: Mapped[str | None] = mapped_column(Text)
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    disposition: Mapped[str | None] = mapped_column(String(20))
    price: Mapped[float | None] = mapped_column(Numeric(14, 2))
    size_m2: Mapped[float | None] = mapped_column(Numeric(10, 2))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    city: Mapped[str | None] = mapped_column(String(200))
    district: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(20))
    first_seen_at: Mapped[None] = mapped_column(DateTime(timezone=True))
    last_seen_at: Mapped[None] = mapped_column(DateTime(timezone=True))


class UserFilter(Base):
    __tablename__ = "user_filters"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    telegram_chat_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(200), default="My Filter")
    property_type: Mapped[str | None] = mapped_column(String(30))
    transaction_type: Mapped[str | None] = mapped_column(String(20))
    city: Mapped[str | None] = mapped_column(String(200))
    district: Mapped[str | None] = mapped_column(String(200))
    disposition: Mapped[str | None] = mapped_column(Text)
    price_min: Mapped[float | None] = mapped_column(Numeric(14, 2))
    price_max: Mapped[float | None] = mapped_column(Numeric(14, 2))
    size_min: Mapped[float | None] = mapped_column(Numeric(10, 2))
    size_max: Mapped[float | None] = mapped_column(Numeric(10, 2))
    notify_new: Mapped[bool] = mapped_column(Boolean, default=True)
    notify_price_drop: Mapped[bool] = mapped_column(Boolean, default=True)
    price_drop_threshold: Mapped[float] = mapped_column(Numeric(5, 2), default=5.0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[None] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = {"extend_existing": True}

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_filter_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("user_filters.id"))
    property_id: Mapped[int | None] = mapped_column(BigInteger, ForeignKey("properties.id"))
    notification_type: Mapped[str] = mapped_column(String(30))
    sent_at: Mapped[None] = mapped_column(DateTime(timezone=True), server_default=func.now())


# Middleware to inject DB session
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject


class DbSessionMiddleware(BaseMiddleware):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        super().__init__()
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.session_maker() as session:
            data["db"] = session
            return await handler(event, data)


async def main():
    if not bot_settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN not set, bot will not start. "
                       "Set it in .env to enable the Telegram bot.")
        # Keep alive but do nothing
        while True:
            await asyncio.sleep(3600)

    bot = Bot(token=bot_settings.telegram_bot_token, default_parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    # Add middleware
    dp.message.middleware(DbSessionMiddleware(session_maker))
    dp.callback_query.middleware(DbSessionMiddleware(session_maker))

    # Include routers
    dp.include_router(start.router)
    dp.include_router(filters.router)

    # Stats callback handler
    @dp.callback_query(lambda c: c.data == "stats")
    async def cb_stats(callback, db: AsyncSession):
        from sqlalchemy import select, func
        total = (
            await db.execute(
                select(func.count()).select_from(Property).where(Property.status == "active")
            )
        ).scalar() or 0

        source_rows = (
            await db.execute(
                select(Property.source, func.count())
                .where(Property.status == "active")
                .group_by(Property.source)
            )
        ).all()

        lines = [f"📊 <b>Statistiky</b>\n", f"Celkem aktivnich: {total}\n"]
        for source, count in source_rows:
            lines.append(f"  {source}: {count}")

        from bot.keyboards import main_menu_keyboard
        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()

    # Start notification worker in background
    asyncio.create_task(
        notification_worker(bot, session_maker, bot_settings.redis_url)
    )

    logger.info("Bot starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
