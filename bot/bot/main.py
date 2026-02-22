import asyncio
import logging
import sys
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.config import bot_settings
from bot.handlers import start, filters
from bot.handlers.notifications import notification_worker
from bot.keyboards import main_menu_keyboard
from bot.models import Property, UserFilter, Notification

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Database setup
engine = create_async_engine(bot_settings.database_url, echo=False)
session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Store background task reference to prevent garbage collection
_background_tasks: set[asyncio.Task] = set()


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
        while True:
            await asyncio.sleep(3600)

    bot = Bot(
        token=bot_settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
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

        lines = ["\U0001f4ca <b>Statistiky</b>\n", f"Celkem aktivnich: {total}\n"]
        for source, count in source_rows:
            lines.append(f"  {source}: {count}")

        await callback.message.edit_text(
            "\n".join(lines),
            reply_markup=main_menu_keyboard(),
        )
        await callback.answer()

    # Start notification worker in background
    task = asyncio.create_task(
        notification_worker(bot, session_maker, bot_settings.redis_url)
    )
    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    logger.info("Bot starting polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
