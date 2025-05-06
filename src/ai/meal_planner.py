"""
Модуль для генерации плана питания на основе КБЖУ с помощью OpenAI.
"""

import json
from typing import Dict, List

from loguru import logger

from src.ai.openai_service import get_openai_client


def generate_meal_plan(kbju_data: Dict) -> List[Dict]:
    """
    Генерирует план питания на основе рассчитанного КБЖУ с помощью OpenAI.

    Args:
        kbju_data: Словарь с данными КБЖУ, содержащий:
            - calories: Суточная норма калорий
            - protein: Суточная норма белков (г)
            - fat: Суточная норма жиров (г)
            - carbs: Суточная норма углеводов (г)

    Returns:
        List[Dict]: Список приемов пищи с разбивкой по КБЖУ
        Пример:
        [
            {
                "meal": "Завтрак",
                "calories": 600,
                "protein": 40,
                "fat": 15,
                "carbs": 70
            },
            ...
        ]
    """
    # Определяем количество приемов пищи в зависимости от калорийности
    calories = kbju_data["calories"]
    meal_count = 4 if calories >= 2000 else 3

    # Формируем системный промпт для OpenAI
    system_prompt = (
        "Ты - диетолог-нутрициолог. Твоя задача - разбить суточную норму КБЖУ "
        + "на приемы пищи.\n\n"
        + "Правила:\n"
        + "1. Если калорий < 2000, разбить на 3 приема пищи: Завтрак, Обед, "
        + "Ужин\n"
        + "2. Если калорий ≥ 2000, разбить на 4 приема пищи: Завтрак, "
        + "Обед, Полдник, Ужин\n"
        + "3. Распределить калории, белки, жиры и углеводы пропорционально "
        + "между приемами пищи\n"
        + "4. Вернуть только JSON-массив, без дополнительных пояснений\n"
        + "5. Каждый элемент массива должен содержать: название приема "
        + "пищи, калории, белки, жиры, углеводы\n"
        + "6. Округлить значения калорий до целых чисел, а белки, жиры и "
        + "углеводы до 1 десятичного знака"
    )

    user_prompt = (
        f"Разбей следующую суточную норму КБЖУ на "
        f"{'4' if meal_count == 4 else '3'} приема пищи:\n\n"
        f"Калории: {calories} ккал\n"
        f"Белки: {kbju_data['protein']} г\n"
        f"Жиры: {kbju_data['fat']} г\n"
        f"Углеводы: {kbju_data['carbs']} г\n\n"
        "Верни только JSON-массив с приемами пищи и разбивкой КБЖУ, "
        "без пояснений.\n"
        'Формат: [{"meal": "Название", "calories": "число", '
        '"protein": "число", "fat": "число", "carbs": "число"}, ...]'
    )

    client = get_openai_client()
    msg = "Запрос к OpenAI для генерации плана питания " f"на {meal_count} приемов пищи"
    logger.info(msg)

    try:
        # Отправляем запрос к OpenAI
        response = client.get_completion(
            prompt=user_prompt, system_message=system_prompt
        )

        # Попытка преобразовать ответ в JSON
        try:
            # Ищем JSON-массив в ответе
            response_text = response.strip()

            # Если ответ не начинается с [, ищем начало массива
            if not response_text.startswith("["):
                start_index = response_text.find("[")
                if start_index != -1:
                    response_text = response_text[start_index:]

            # Если ответ не заканчивается на ], ищем конец массива
            if not response_text.endswith("]"):
                end_index = response_text.rfind("]")
                if end_index != -1:
                    response_text = response_text[: end_index + 1]

            # Преобразуем текст в JSON
            meal_plan = json.loads(response_text)

            # Проверяем, что полученный результат - это список словарей
            if not isinstance(meal_plan, list):
                raise ValueError("Результат не является списком")

            msg = (
                "Успешно сгенерирован план питания с "
                + f"{len(meal_plan)} приемами пищи"
            )
            logger.info(msg)
            return meal_plan

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка при обработке ответа OpenAI: {e}")
            logger.debug(f"Проблемный ответ: {response}")
            # Если не удалось получить корректный JSON, генерируем план
            # по умолчанию
            return _generate_default_meal_plan(kbju_data, meal_count)

    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        # В случае ошибки при запросе к API, генерируем план по умолчанию
        return _generate_default_meal_plan(kbju_data, meal_count)


def _generate_default_meal_plan(kbju_data: Dict, meal_count: int) -> List[Dict]:
    """
    Генерирует план питания по умолчанию на основе рассчитанного КБЖУ.
    Используется как запасной вариант при ошибках с OpenAI.

    Args:
        kbju_data: Словарь с данными КБЖУ
        meal_count: Количество приемов пищи

    Returns:
        List[Dict]: Список приемов пищи с разбивкой по КБЖУ
    """
    meal_plan = []

    # Определяем распределение калорий и нутриентов по приемам пищи
    if meal_count == 3:
        distribution = [
            ("Завтрак", 0.3),  # 30% от дневной нормы
            ("Обед", 0.45),  # 45% от дневной нормы
            ("Ужин", 0.25),  # 25% от дневной нормы
        ]
    else:  # 4 приема пищи
        distribution = [
            ("Завтрак", 0.25),  # 25% от дневной нормы
            ("Обед", 0.35),  # 35% от дневной нормы
            ("Полдник", 0.15),  # 15% от дневной нормы
            ("Ужин", 0.25),  # 25% от дневной нормы
        ]

    calories = kbju_data["calories"]
    protein = kbju_data["protein"]
    fat = kbju_data["fat"]
    carbs = kbju_data["carbs"]

    # Распределяем КБЖУ по приемам пищи
    for meal_name, ratio in distribution:
        meal = {
            "meal": meal_name,
            "calories": round(calories * ratio),
            "protein": round(protein * ratio, 1),
            "fat": round(fat * ratio, 1),
            "carbs": round(carbs * ratio, 1),
        }
        meal_plan.append(meal)

    msg = "Сгенерирован план питания по умолчанию " f"с {meal_count} приемами пищи"
    logger.info(msg)
    return meal_plan


def generate_meal_examples(kbju_data: Dict) -> List[Dict]:
    """Генерирует план питания с примерами блюд на основе рассчитанного КБЖУ
    с помощью OpenAI.

    Args:
        kbju_data: Словарь с данными КБЖУ, содержащий:
            - calories: Суточная норма калорий
            - protein: Суточная норма белков (г)
            - fat: Суточная норма жиров (г)
            - carbs: Суточная норма углеводов (г)

    Returns:
        List[Dict]: Список приемов пищи с разбивкой по КБЖУ и примерами блюд
    """
    # Сначала получаем базовый план питания с распределением КБЖУ
    meal_plan = generate_meal_plan(kbju_data)
    meal_count = len(meal_plan)

    # Формируем системный промпт для OpenAI
    system_prompt = (
        "Ты - опытный диетолог-нутрициолог. Твоя задача - предложить "
        + "ОДИН точный вариант для каждого приема пищи, который будет "
        + "точно соответствовать указанным значениям КБЖУ.\n\n"
        + "Правила:\n"
        + "1. Для каждого приема пищи предложи ТОЛЬКО ОДИН набор продуктов\n"
        + "2. Для каждого ингредиента ОБЯЗАТЕЛЬНО указывай:\n"
        + "   - вес в сухом виде (до приготовления) в граммах\n"
        + "   - для круп/макарон указывать вес ДО варки\n"
        + "   - для мяса указывать вес в сыром виде\n"
        + "3. Блюда должны ТОЧНО соответствовать указанным значениям КБЖУ\n"
        + "   (допустимая погрешность ±1г для БЖУ)\n"
        + "4. Используй только обычные продукты, доступные в России\n"
        + "5. Вернуть только JSON-массив, без дополнительных пояснений\n"
        + "6. Каждый прием пищи должен быть реалистичным и сбалансированным\n"
        + "7. Указывай способ приготовления (варка/жарка/запекание)\n"
        + '8. Используй формат: "продукт - Xг (сухой вес)" для каждого '
        "ингредиента"
    )

    # Формируем список приемов пищи с их КБЖУ
    meals_info = []
    for meal in meal_plan:
        meal_info = (
            f"- {meal['meal']}:\\n"
            f"Калории: {meal['calories']} ккал\\n"
            f"Белки: {meal['protein']} г\\n"
            f"Жиры: {meal['fat']} г\\n"
            f"Углеводы: {meal['carbs']} г"
        )
        meals_info.append(meal_info)

    meals_text = "\\n\\n".join(meals_info)

    user_prompt = (
        "Предложи ОДИН точный набор продуктов для каждого приема пищи.\\n\\n"
        f"{meals_text}\\n\\n"
        "Для каждого приема пищи укажи:\\n"
        "1. Точный список ингредиентов с весом в сухом виде "
        "(до приготовления)\\n"
        + "2. Для круп/макарон - вес ДО варки\\n"
        + "3. Для мяса - вес в сыром виде\\n"
        + "4. Способ приготовления\\n"
    )

    client = get_openai_client()
    msg = (
        "Запрос к OpenAI для генерации списка продуктов на "
        + f"{meal_count} приемов пищи"
    )
    logger.info(msg)

    try:
        # Отправляем запрос к OpenAI
        response = client.get_completion(
            prompt=user_prompt, system_message=system_prompt
        )

        # Попытка преобразовать ответ в JSON
        try:
            # Ищем JSON-массив в ответе
            response_text = response.strip()

            # Если ответ не начинается с [, ищем начало массива
            if not response_text.startswith("["):
                start_index = response_text.find("[")
                if start_index != -1:
                    response_text = response_text[start_index:]

            # Если ответ не заканчивается на ], ищем конец массива
            if not response_text.endswith("]"):
                end_index = response_text.rfind("]")
                if end_index != -1:
                    response_text = response_text[: end_index + 1]

            # Преобразуем текст в JSON
            examples = json.loads(response_text)

            # Проверяем, что полученный результат - это список словарей
            if not isinstance(examples, list):
                raise ValueError("Результат не является списком")

            msg = (
                "Успешно сгенерированы списки продуктов для "
                + f"{len(examples)} приемов пищи"
            )
            logger.info(msg)

            # Объединяем списки продуктов с базовым планом питания
            result = []
            for meal_data in meal_plan:
                meal_name = meal_data["meal"]
                # Ищем список продуктов для текущего приема пищи
                foods_text = ""
                for example in examples:
                    if example.get("meal") == meal_name:
                        foods_text = example.get("foods", "")
                        break

                # Добавляем данные о продуктах к базовому плану
                meal_data["foods"] = foods_text
                result.append(meal_data)

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка при обработке ответа OpenAI: {e}")
            logger.debug(f"Проблемный ответ: {response}")
            # Если не удалось получить корректный JSON, возвращаем план
            # без списка продуктов
            return meal_plan

    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        # В случае ошибки при запросе к API, возвращаем план
        # без списка продуктов
        return meal_plan
