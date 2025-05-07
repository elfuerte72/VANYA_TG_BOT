"""
Middleware для проверки подписки пользователя на Telegram-канал.
"""
from typing import Any, Awaitable, Callable, Dict, Union

from aiogram import BaseMiddleware, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline_kb import get_start_keyboard
from src.bot.services.subscription import SubscriptionService
from src.core.logger import error_logger, user_logger

# Указываем ID канала напрямую
CHANNEL_ID = "@ivanfit_health"


class ChannelSubscriptionMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки пользователя на Telegram-канал
    перед обработкой сообщений.
    """

    async def __call__(
        self,
        handler: Callable[
            [Union[Message, CallbackQuery], Dict[str, Any]], Awaitable[Any]
        ],
        event: Union[Message, CallbackQuery],
        data: Dict[str, Any],
    ) -> Any:
        """
        Проверяет подписку пользователя на канал.

        Args:
            handler: Обработчик события
            event: Объект сообщения или callback query
            data: Словарь с данными

        Returns:
            Any: Результат обработки события
        """
        # Получаем бота из контекста
        bot = data.get("bot")
        if not isinstance(bot, Bot):
            error_logger.error("Bot instance not found in middleware data")
            return await handler(event, data)

        # Определяем тип события и получаем user_id
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
            # Пропускаем команду /start
            if event.text and event.text.startswith("/start"):
                user_logger.info("Пропускаем проверку подписки для /start")
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
            # Пропускаем проверку подписки для callback проверки подписки
            if event.data and event.data == "check_subscription":
                user_logger.info("Пропускаем проверку подписки для check_subscription")
                return await handler(event, data)
        else:
            error_logger.warning(f"Unexpected event type: {type(event)}")
            return await handler(event, data)

        if not user_id:
            error_logger.error("User ID not found in event")
            return await handler(event, data)

        try:
            # Проверяем подписку через сервис
            is_subscribed = await SubscriptionService.is_subscribed(
                bot, user_id, CHANNEL_ID
            )

            if not is_subscribed:
                # Отправляем сообщение о необходимости подписки
                message_text = (
                    f"⚠️ Для использования бота необходимо подписаться "
                    f"на канал {CHANNEL_ID}.\n\n"
                    "Нажмите кнопку 'Подписаться', затем вернитесь в бот."
                )

                if isinstance(event, Message):
                    await event.answer(
                        message_text,
                        reply_markup=get_start_keyboard(
                            show_calculation=False, show_subscription=True
                        ),
                    )
                elif isinstance(event, CallbackQuery) and event.message:
                    await event.message.answer(
                        message_text,
                        reply_markup=get_start_keyboard(
                            show_calculation=False, show_subscription=True
                        ),
                    )
                    await event.answer()

                return

            # Если пользователь подписан, продолжаем обработку
            return await handler(event, data)

        except TelegramBadRequest as e:
            error_msg = f"Error checking subscription for user {user_id}: {e}"
            error_logger.error(error_msg)
            # В случае ошибки пропускаем проверку, считая пользователя подписанным
            user_logger.info(f"Пропускаем проверку для {user_id} из-за ошибки API")
            return await handler(event, data)
