"""
Тесты для модуля логирования.
"""
import logging
from logging.handlers import TimedRotatingFileHandler
from unittest.mock import patch

import pytest

from src.core.logger import get_logger, setup_loggers


@pytest.fixture
def temp_logs_dir(tmp_path):
    """Фикстура для создания временной директории логов."""
    with patch("src.core.logger.LOGS_DIR", tmp_path):
        yield tmp_path


def test_get_logger_creates_log_file(temp_logs_dir):
    """Тест создания файла лога."""
    log_file = "test.log"
    logger = get_logger("test", log_file)

    # Проверяем, что файл создан
    log_path = temp_logs_dir / log_file
    assert log_path.exists()

    # Проверяем, что логгер настроен правильно
    assert logger.name == "test"
    assert logger.level == logging.INFO
    assert len(logger.handlers) == 2  # file handler + console handler


def test_get_logger_formatter(temp_logs_dir):
    """Тест форматирования логов."""
    logger = get_logger("test", "formatter_test.log")

    # Проверяем формат для file handler
    file_handler = logger.handlers[0]
    assert isinstance(file_handler, TimedRotatingFileHandler)
    assert file_handler.formatter is not None
    fmt = file_handler.formatter._fmt
    assert "[%(asctime)s]" in fmt
    assert "%(levelname)s" in fmt
    assert "[%(name)s:%(lineno)s]" in fmt
    assert "%(message)s" in fmt


def test_get_logger_rotation_settings(temp_logs_dir):
    """Тест настроек ротации логов."""
    logger = get_logger(
        "test", "rotation_test.log", when="midnight", interval=1, backup_count=30
    )

    # Проверяем настройки ротации
    handler = logger.handlers[0]
    assert isinstance(handler, TimedRotatingFileHandler)
    assert (
        handler.when == "MIDNIGHT"
    )  # TimedRotatingFileHandler преобразует в верхний регистр
    assert handler.interval == 86400  # 24 часа * 60 минут * 60 секунд
    assert handler.backupCount == 30


def test_get_logger_reuse(temp_logs_dir):
    """Тест повторного использования логгера."""
    logger1 = get_logger("test_reuse", "reuse_test.log")
    logger2 = get_logger("test_reuse", "reuse_test.log")

    # Проверяем, что возвращается тот же логгер
    assert logger1 is logger2
    # Проверяем, что handlers не дублируются
    assert len(logger1.handlers) == 2


def test_setup_loggers(temp_logs_dir):
    """Тест создания всех логгеров приложения."""
    loggers = setup_loggers()

    # Проверяем наличие всех необходимых логгеров
    expected_loggers = {"main", "user", "error", "api", "db"}
    assert set(loggers.keys()) == expected_loggers

    # Проверяем настройки каждого логгера
    for name, logger in loggers.items():
        assert isinstance(logger, logging.Logger)
        assert logger.name == name
        assert len(logger.handlers) == 2

        # Проверяем файловый handler
        file_handler = logger.handlers[0]
        assert isinstance(file_handler, TimedRotatingFileHandler)
        assert file_handler.baseFilename.endswith(f"{name}.log")

        # Проверяем уровень логирования
        if name == "error":
            assert logger.level == logging.ERROR
        else:
            assert logger.level == logging.INFO


def test_error_logger_level(temp_logs_dir):
    """Тест уровня логирования для error logger."""
    loggers = setup_loggers()
    error_logger = loggers["error"]
    assert error_logger.level == logging.ERROR


@pytest.mark.asyncio
async def test_logger_async_usage(temp_logs_dir):
    """Тест использования логгера в асинхронном коде."""
    logger = get_logger("test_async", "async_test.log")

    # Логируем сообщение
    test_message = "Test async logging"
    logger.info(test_message)

    # Проверяем, что сообщение записано в файл
    log_path = temp_logs_dir / "async_test.log"
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert test_message in log_content


def test_logger_encoding(temp_logs_dir):
    """Тест поддержки Unicode в логах."""
    logger = get_logger("test_unicode", "unicode_test.log")

    # Логируем сообщение с Unicode
    test_message = "Тестовое сообщение с Unicode символами 🐍"
    logger.info(test_message)

    # Проверяем, что сообщение корректно записано
    log_path = temp_logs_dir / "unicode_test.log"
    with open(log_path, "r", encoding="utf-8") as f:
        log_content = f.read()
        assert test_message in log_content
