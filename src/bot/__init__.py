"""Telegram Bot package."""
from aiogram import Bot, Dispatcher
from src.utils.config import settings

def create_bot() -> Bot:
    """Create Telegram Bot instance."""
    return Bot(token=settings.telegram_token)


def create_dispatcher() -> Dispatcher:
    """Create Telegram Dispatcher instance."""
    return Dispatcher()


__all__ = ["create_bot", "create_dispatcher"]
