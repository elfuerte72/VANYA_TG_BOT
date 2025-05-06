"""
Модуль настройки логирования для проекта.
Использует TimeRotatingFileHandler для ротации логов по времени.
"""
import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Dict

from src.config.settings import LOGS_DIR


def get_logger(
    name: str,
    log_file: str = "bot.log",
    level: int = logging.INFO,
    when: str = "midnight",
    interval: int = 1,
    backup_count: int = 30,
) -> logging.Logger:
    """
    Создает и настраивает логгер с ротацией по времени.

    Args:
        name: Имя логгера
        log_file: Имя файла логов
        level: Уровень логирования
        when: Когда выполнять ротацию
            ('S', 'M', 'H', 'D', 'W0'-'W6', 'midnight')
        interval: Интервал для ротации
        backup_count: Количество бэкап-файлов для хранения

    Returns:
        Настроенный логгер
    """
    # Проверяем существование директории для логов
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)

    # Получаем или создаем логгер
    logger = logging.getLogger(name)

    # Если логгер уже настроен, возвращаем его
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # Создаем форматтер
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s"
    )

    # Настраиваем файловый обработчик с ротацией
    file_handler = TimedRotatingFileHandler(
        os.path.join(LOGS_DIR, log_file),
        when=when,
        interval=interval,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Добавляем вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    return logger


def setup_loggers() -> Dict[str, logging.Logger]:
    """
    Создает и настраивает все логгеры приложения.

    Returns:
        Словарь с настроенными логгерами
    """
    loggers = {
        "main": get_logger("main", "main.log"),
        "user": get_logger("user", "user.log"),
        "error": get_logger("error", "error.log", level=logging.ERROR),
        "api": get_logger("api", "api.log"),
        "db": get_logger("db", "db.log"),
    }
    return loggers


# Создаем основные логгеры
main_logger = get_logger("main", "main.log")
user_logger = get_logger("user", "user.log")
error_logger = get_logger("error", "error.log", level=logging.ERROR)
api_logger = get_logger("api", "api.log")
db_logger = get_logger("db", "db.log")
