from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject


class RepositoryMiddleware(BaseMiddleware):
    """Middleware to inject repository instances into handler"""

    def __init__(self, repository_factory):
        """
        Initialize middleware with repository factory

        Args:
            repository_factory: Factory function that returns repository instance
        """
        self.repository_factory = repository_factory

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """
        Execute middleware

        Args:
            handler: Event handler
            event: Telegram event object (Message, CallbackQuery, etc.)
            data: Additional data dict

        Returns:
            Any: Handler result
        """
        # Create repository instance
        repository = self.repository_factory()

        # Add repository to handler data
        data["user_repo"] = repository

        # Call next handler
        return await handler(event, data)
