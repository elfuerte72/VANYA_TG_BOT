"""
Reply-клавиатуры для Telegram-бота.
"""
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


# Стартовая клавиатура
def get_start_kb() -> ReplyKeyboardMarkup:
    """Создает стартовую клавиатуру с кнопкой запуска расчета."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("▶️ Запустить расчёт"))
    return keyboard

# Клавиатура для выбора пола
def get_gender_kb() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для выбора пола."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Мужской"), KeyboardButton("Женский"))
    return keyboard

# Клавиатура для выбора уровня активности
def get_activity_kb() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для выбора уровня активности."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("Низкий"), KeyboardButton("Средний"), KeyboardButton("Высокий"))
    return keyboard

# Клавиатура для подтверждения данных
def get_confirm_kb() -> ReplyKeyboardMarkup:
    """Создает клавиатуру для подтверждения введенных данных."""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("✅ Подтвердить"), KeyboardButton("🔄 Начать заново"))
    return keyboard
