"""
Модуль для работы с ИИ-сервисами.

Экспортирует основные функции для взаимодействия с OpenAI API.
"""

from src.ai.meal_planner import generate_meal_examples, generate_meal_plan
from src.ai.openai_service import get_cached_completion, get_openai_client

__all__ = [
    "get_cached_completion",
    "get_openai_client",
    "generate_meal_plan",
    "generate_meal_examples",
]
