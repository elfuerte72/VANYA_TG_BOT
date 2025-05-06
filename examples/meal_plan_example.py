"""
Пример использования функции генерации плана питания на основе КБЖУ.
"""

import json
import os

from dotenv import load_dotenv

from src.ai import generate_meal_plan

# Загружаем переменные окружения из .env файла
load_dotenv()


def main():
    """
    Основная функция примера.

    Демонстрирует использование функции generate_meal_plan
    для создания плана питания на основе КБЖУ.
    """
    # Проверяем наличие API ключа OpenAI
    if not os.getenv("OPENAI_API_KEY"):
        print("Ошибка: не установлен OPENAI_API_KEY.")
        message = "Установите переменную окружения OPENAI_API_KEY или "
        message += "создайте файл .env"
        print(message)
        return

    # Пример данных для генерации плана (как в задании)
    kbju_data = {"calories": 2450, "protein": 160, "fat": 70, "carbs": 280}

    # Вызываем функцию генерации плана питания
    try:
        print(f"Генерация плана питания для: {kbju_data}...\n")
        meal_plan = generate_meal_plan(kbju_data)

        # Выводим сгенерированный план питания
        print("Сгенерированный план питания:")
        print(json.dumps(meal_plan, indent=2, ensure_ascii=False))

        # Проверяем суммы нутриентов
        total_calories = sum(meal["calories"] for meal in meal_plan)
        total_protein = sum(meal["protein"] for meal in meal_plan)
        total_fat = sum(meal["fat"] for meal in meal_plan)
        total_carbs = sum(meal["carbs"] for meal in meal_plan)

        print("\nПроверка суммарных значений:")
        cal_percent = round((total_calories / kbju_data["calories"]) * 100, 1)
        print(
            (f"Калории: {total_calories}/{kbju_data['calories']} " f"({cal_percent}%)")
        )

        prot_percent = round((total_protein / kbju_data["protein"]) * 100, 1)
        print((f"Белки: {total_protein}/{kbju_data['protein']} " f"({prot_percent}%)"))

        fat_percent = round((total_fat / kbju_data["fat"]) * 100, 1)
        print((f"Жиры: {total_fat}/{kbju_data['fat']} " f"({fat_percent}%)"))

        carb_percent = round((total_carbs / kbju_data["carbs"]) * 100, 1)
        print((f"Углеводы: {total_carbs}/{kbju_data['carbs']} " f"({carb_percent}%)"))

    except Exception as e:
        print(f"Ошибка при генерации плана питания: {e}")


if __name__ == "__main__":
    main()
