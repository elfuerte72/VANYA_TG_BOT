"""
Middlewares для Telegram-бота.
Включает middleware для проверки подписки на канал и другие промежуточные обработчики.
"""

from src.bot.middlewares.repository import RepositoryMiddleware

__all__ = ["RepositoryMiddleware"]
