"""
Настройка логирования для проекта.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

# Создаем директорию для логов, если её нет
log_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
os.makedirs(log_directory, exist_ok=True)

# Конфигурация логгера
def setup_logger(name: str, log_file: str, level=logging.INFO):
    """Функция для настройки логгера с ротацией файлов."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Настройка ротации логов (максимальный размер файла 10 МБ, до 5 бэкапов)
    handler = RotatingFileHandler(
        filename=os.path.join(log_directory, log_file),
        maxBytes=10_000_000,  # 10 МБ
        backupCount=5,
        encoding='utf-8'
    )

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Добавляем вывод в консоль для режима разработки
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger

# Основные логгеры приложения
main_logger = setup_logger('bot_main', 'bot.log')
user_logger = setup_logger('user_actions', 'user_actions.log')
error_logger = setup_logger('errors', 'errors.log', level=logging.ERROR)
