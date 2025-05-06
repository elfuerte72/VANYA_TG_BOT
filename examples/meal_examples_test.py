"""
Пример использования функции генерации плана питания с примерами блюд.
"""

import json
import os

from dotenv import load_dotenv

from src.ai import generate_meal_examples

# Загружаем переменные окружения из .env файла
load_dotenv()


def main():
    """
    Основная функция примера.

    Демонстрирует использование функции generate_meal_examples
    для создания плана питания с примерами блюд на основе КБЖУ.
    """
    # Проверяем наличие API ключа OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        print("Ошибка: не установлен OPENAI_API_KEY.")
        message = "Установите переменную окружения OPENAI_API_KEY или "
        message += "создайте файл .env"
        print(message)
        return

    # Пример данных для генерации плана
    kbju_data = {"calories": 2450, "protein": 160, "fat": 70, "carbs": 280}

    # Вызываем функцию генерации плана питания с примерами блюд
    try:
        print(f"Генерация плана питания с примерами блюд для: {kbju_data}...\n")
        meal_plan = generate_meal_examples(kbju_data)

        # Выводим сгенерированный план питания
        print("Сгенерированный план питания с примерами блюд:")
        print(json.dumps(meal_plan, indent=2, ensure_ascii=False))

    except Exception as e:
        print(f"Ошибка при генерации плана питания: {e}")


if __name__ == "__main__":
    main()
