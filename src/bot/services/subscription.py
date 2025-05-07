import re

from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from src.core.logger import error_logger, user_logger


class SubscriptionService:
    """Сервис для проверки подписки пользователя на Telegram-канал."""

    @staticmethod
    def extract_chat_id(channel_identifier: str) -> str:
        """
        Извлекает идентификатор для API из предоставленной строки.

        Для "@username" возвращает его же. Для числовых ID возвращает их.
        Пытается извлечь username из ссылок t.me/username.

        Args:
            channel_identifier: Имя пользователя, ID или ссылка на канал.

        Returns:
            str: Предполагаемый идентификатор для использования в API.
        """
        if channel_identifier.startswith("@"):
            return channel_identifier
        if re.match(r"^-?\\d+$", channel_identifier):  # Числовой ID
            return channel_identifier

        # Попытка извлечь username из ссылки t.me/username
        username_match = re.search(r"t\\.me/([a-zA-Z0-9_]+)/?", channel_identifier)
        if username_match:
            return "@" + username_match.group(1)

        user_logger.warning(
            f"Не удалось извлечь chat_id из '{channel_identifier}'. "
            f"Используется как есть."
        )
        return channel_identifier

    @staticmethod
    async def is_subscribed(bot: Bot, user_id: int, channel_username: str) -> bool:
        """
        Проверяет подписку пользователя на Telegram-канал.

        Канал должен быть публичным (@username), или бот должен быть
        администратором в приватном канале (с числовым ID).

        Args:
            bot: Экземпляр aiogram.Bot.
            user_id: ID пользователя Telegram.
            channel_username: Имя пользователя канала (например, "@channel_name").
                               Для приватных каналов здесь должен быть числовой ID.

        Returns:
            bool: True, если пользователь подписан, иначе False.
        """
        log_base = f"user_id={user_id}, канал='{channel_username}'"
        user_logger.info(f"Проверка подписки: {log_base}")

        try:
            member = await bot.get_chat_member(
                chat_id=channel_username, user_id=user_id
            )

            # member.status приходит как строка (согласно логам ошибки AttributeError).
            actual_status_str = member.status
            user_logger.info(f"Получен статус '{actual_status_str}' для {log_base}")

            # Сравниваем со строковыми значениями статусов.
            # .value берем для каноничности, хотя member.status и так строка.
            subscribed_statuses_values = [
                ChatMemberStatus.MEMBER.value,  # "member"
                ChatMemberStatus.ADMINISTRATOR.value,  # "administrator"
                ChatMemberStatus.CREATOR.value,  # "creator"
            ]

            is_member = actual_status_str in subscribed_statuses_values

            if is_member:
                user_logger.info(
                    f"Подписка ОК: {log_base}, фактический статус='{actual_status_str}'"
                )
                return True
            else:
                user_logger.warning(
                    f"НЕ подписан: {log_base}, фактический статус='{actual_status_str}'"
                )
                return False

        except TelegramBadRequest:
            msg = (
                f"BadRequest (проверка): {log_base}. Не найден/заблокирован."
                f" Считаем НЕ подписанным."
            )
            error_logger.warning(msg)
            return False
        except TelegramForbiddenError:
            msg = (
                f"Forbidden (проверка): {log_base}. Бот заблокирован/нет прав."
                f" Считаем НЕ подписанным."
            )
            error_logger.error(msg)
            return False
        except Exception as e:
            msg = f"Ошибка (проверка): {log_base}. {e!r}." f" Считаем НЕ подписанным."
            error_logger.exception(msg)
            return False
