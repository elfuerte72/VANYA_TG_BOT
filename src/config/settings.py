"""
Настройки и конфигурация проекта.
Загрузка переменных окружения из .env файла и предоставление конфигов другим модулям.
"""
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Определение базовых путей
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

# Загрузка переменных окружения из .env файла
load_dotenv(ENV_PATH)

# Конфигурация Telegram
BOT_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID")

# Конфигурация OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4-1106-preview")

# Пути к директориям данных и логам
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"

# Конфигурация базы данных
DATABASE_PATH = DATA_DIR / "users.db"
# Секретный ключ для шифрования базы данных SQLCipher
# Если ключ не задан в .env, используем дефолтный в качестве запасного
DATABASE_SECRET_KEY = os.getenv(
    "DATABASE_SECRET_KEY", "default_secret_key_change_in_production"
)

# Настройки для расчета КБЖУ
CALORIES_THRESHOLD = 2000  # Порог для определения 3 или 4 приемов пищи
PROTEIN_PERCENTAGE = 20  # % белков в рационе
FAT_PERCENTAGE = 25  # % жиров в рационе
CARB_PERCENTAGE = 55  # % углеводов в рационе

# Коэффициенты активности для формулы Бенедикта
ACTIVITY_MULTIPLIERS = {
    "low": 1.2,  # Низкая активность
    "medium": 1.55,  # Средняя активность (по умолчанию)
    "high": 1.9,  # Высокая активность
}

# Telegram IDs администраторов/разработчиков, которым разрешен повторный расчет
ADMIN_USER_IDS = [
    379336096,  # Telegram ID разработчика
]

# Создание директорий, если они не существуют
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)


def validate_config() -> tuple[bool, Optional[str]]:
    """
    Проверяет, что все необходимые переменные окружения установлены.

    Returns:
        tuple[bool, Optional[str]]: Результат проверки (True/False) и сообщение об ошибке при наличии.
    """
    missing_vars = []

    if not BOT_TOKEN:
        missing_vars.append("BOT_TOKEN")

    if not TELEGRAM_CHANNEL_ID:
        missing_vars.append("TELEGRAM_CHANNEL_ID")

    if not OPENAI_API_KEY:
        missing_vars.append("OPENAI_API_KEY")

    if not DATABASE_SECRET_KEY:
        missing_vars.append("DATABASE_SECRET_KEY")

    if missing_vars:
        return (
            False,
            f"Отсутствуют необходимые переменные окружения: {', '.join(missing_vars)}",
        )

    return True, None
