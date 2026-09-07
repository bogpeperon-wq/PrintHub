"""
Telegram Bot Runner - main entry point for the bot.
"""
import asyncio
import logging
from aiogram import Bot, Dispatcher

from src.utils.config import settings
from src.db.session import AsyncSessionLocal
from src.bot.handlers import router
from src.domain.models.base import Base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main():
    """Main bot runner."""
    logger.info("Starting Print Hub Bot...")
    
    # Create bot and dispatcher
    bot = Bot(token=settings.telegram_token)
    dp = Dispatcher()
    
    # Include routers
    dp.include_router(router)
    
    # Delete webhook (for polling mode)
    await bot.delete_webhook()
    logger.info("Webhook deleted, starting polling...")
    
    try:
        # Start polling
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.session.close()
        logger.info("Bot session closed")


if __name__ == "__main__":
    asyncio.run(main())
