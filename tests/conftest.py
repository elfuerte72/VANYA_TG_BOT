"""
Конфигурация pytest для тестов.
"""
import asyncio
import sys
from pathlib import Path

import pytest

# Добавляем корневую директорию проекта в PYTHONPATH
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture(scope="session")
def event_loop():
    """Создает экземпляр event loop для асинхронных тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
