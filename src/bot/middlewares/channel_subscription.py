"""
Middleware для проверки подписки пользователя на Telegram-канал.
"""
from aiogram import types
from aiogram.dispatcher.handler import CancelHandler
from aiogram.dispatcher.middlewares import BaseMiddleware

from src.config.settings import TELEGRAM_CHANNEL_ID


class ChannelSubscriptionMiddleware(BaseMiddleware):
    """
    Middleware для проверки подписки пользователя на Telegram-канал перед обработкой сообщений.
    """

    async def on_pre_process_message(self, message: types.Message, data: dict):
        """
        Проверяет, подписан ли пользователь на указанный канал.

        Args:
            message: Объект сообщения
            data: Словарь с данными

        Raises:
            CancelHandler: Если пользователь не подписан на канал
        """
        # Пропускаем команду /start, чтобы пользователь мог начать диалог
        if message.text and message.text.startswith("/start"):
            return

        user_id = message.from_user.id

        # Проверка подписки пользователя
        chat_member = await message.bot.get_chat_member(chat_id=TELEGRAM_CHANNEL_ID, user_id=user_id)

        # Статусы, указывающие на подписку
        subscription_statuses = [
            types.ChatMemberStatus.MEMBER,
            types.ChatMemberStatus.ADMINISTRATOR,
            types.ChatMemberStatus.CREATOR
        ]

        if chat_member.status not in subscription_statuses:
            # Пользователь не подписан на канал
            await message.answer("⚠️ Для использования бота необходимо подписаться на канал.\n\nПосле подписки нажмите /start для начала диалога.")
            raise CancelHandler()
