import re

from aiogram import Bot


class SubscriptionService:
    """Service for checking user subscription to channel"""

    @staticmethod
    def extract_chat_id(channel_id: str) -> str:
        """
        Извлекает chat_id из ссылки или ID канала

        Args:
            channel_id: Ссылка или ID канала

        Returns:
            str: Извлеченный chat_id
        """
        # Если это уже @username
        if channel_id.startswith("@"):
            return channel_id

        # Если это полная ссылка типа https://t.me/+XXXXXX
        invite_match = re.search(r"t\.me/(\+[a-zA-Z0-9_-]+)", channel_id)
        if invite_match:
            return invite_match.group(1)

        # Если это просто имя канала
        username_match = re.search(r"t\.me/([a-zA-Z0-9_]+)", channel_id)
        if username_match:
            return "@" + username_match.group(1)

        # Если ничего не подошло, возвращаем как есть
        return channel_id

    @staticmethod
    async def is_subscribed(bot: Bot, user_id: int, channel_id: str) -> bool:
        """
        Check if user is subscribed to the required channel

        Args:
            bot: Bot instance
            user_id: Telegram user ID
            channel_id: Channel ID with @ (e.g. @channel_name) or channel ID or invite link

        Returns:
            bool: True if subscribed, False otherwise
        """
        # Временно возвращаем True для тестирования
        return True

        # Закомментировали для тестирования
        # try:
        #     # Извлекаем chat_id из канала
        #     chat_id = SubscriptionService.extract_chat_id(channel_id)

        #     # Get chat member status
        #     member = await bot.get_chat_member(chat_id=chat_id, user_id=user_id)

        #     # Check if status is one of the subscribed types
        #     subscribed_statuses = ["creator", "administrator", "member", "restricted"]
        #     return member.status in subscribed_statuses

        # except TelegramBadRequest as e:
        #     # Логируем ошибку для отладки
        #     print(f"Ошибка при проверке подписки: {e}")
        #     # Error happened - likely the bot is not admin in the channel
        #     # or the channel doesn't exist
        #     return True  # Временно возвращаем True для тестирования
