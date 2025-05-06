"""
Клавиатуры для Telegram-бота.
Содержит все inline и reply клавиатуры для взаимодействия с пользователем.
"""

from src.bot.keyboards.inline_kb import (
    get_activity_keyboard,
    get_confirmation_keyboard,
    get_gender_keyboard,
    get_start_keyboard,
)

__all__ = [
    "get_start_keyboard",
    "get_gender_keyboard",
    "get_activity_keyboard",
    "get_confirmation_keyboard",
]
