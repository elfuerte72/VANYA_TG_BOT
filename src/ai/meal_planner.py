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
    system_prompt = """
    Ты - диетолог-нутрициолог. Твоя задача - разбить суточную норму КБЖУ на приемы пищи.
    
    Правила:
    1. Если калорий < 2000, разбить на 3 приема пищи: Завтрак, Обед, Ужин
    2. Если калорий ≥ 2000, разбить на 4 приема пищи: Завтрак, Обед, Полдник, Ужин
    3. Распределить калории, белки, жиры и углеводы пропорционально между приемами пищи
    4. Вернуть только JSON-массив, без дополнительных пояснений
    5. Каждый элемент массива должен содержать: название приема пищи, калории, белки, жиры, углеводы
    6. Округлить значения калорий до целых чисел, а белки, жиры и углеводы до 1 десятичного знака
    """

    user_prompt = (
        f"Разбей следующую суточную норму КБЖУ на "
        f"{'4' if meal_count == 4 else '3'} приема пищи:\n\n"
        f"Калории: {calories} ккал\n"
        f"Белки: {kbju_data['protein']} г\n"
        f"Жиры: {kbju_data['fat']} г\n"
        f"Углеводы: {kbju_data['carbs']} г\n\n"
        "Верни только JSON-массив с приемами пищи и разбивкой КБЖУ, без пояснений.\n"
        'Формат: [{"meal": "Название", "calories": "число", '
        '"protein": "число", "fat": "число", "carbs": "число"}, ...]'
    )

    client = get_openai_client()
    logger.info(
        f"Запрос к OpenAI для генерации плана питания на {meal_count} приемов пищи"
    )

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

            logger.info(
                f"Успешно сгенерирован план питания с {len(meal_plan)} приемами пищи"
            )
            return meal_plan

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка при обработке ответа OpenAI: {e}")
            logger.debug(f"Проблемный ответ: {response}")
            # Если не удалось получить корректный JSON, генерируем план по умолчанию
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

    logger.info(f"Сгенерирован план питания по умолчанию с {meal_count} приемами пищи")
    return meal_plan


def generate_meal_examples(kbju_data: Dict) -> List[Dict]:
    """
    Генерирует план питания с примерами блюд на основе рассчитанного КБЖУ с помощью OpenAI.

    Args:
        kbju_data: Словарь с данными КБЖУ, содержащий:
            - calories: Суточная норма калорий
            - protein: Суточная норма белков (г)
            - fat: Суточная норма жиров (г)
            - carbs: Суточная норма углеводов (г)

    Returns:
        List[Dict]: Список приемов пищи с разбивкой по КБЖУ и примерами блюд
        Пример:
        [
            {
                "meal": "Завтрак",
                "calories": 600,
                "protein": 40,
                "fat": 15,
                "carbs": 70,
                "examples": "Омлет из 3 яиц с сыром, овсянка на воде, тост с авокадо"
            },
            ...
        ]
    """
    # Сначала получаем базовый план питания с распределением КБЖУ
    meal_plan = generate_meal_plan(kbju_data)

    # Формируем системный промпт для OpenAI
    system_prompt = """
    Ты - диетолог-нутрициолог. Твоя задача - предложить примеры блюд для каждого 
    приема пищи с заданным КБЖУ.
    
    Правила:
    1. Предложи 2-3 варианта блюд для каждого приема пищи
    2. Блюда должны соответствовать указанным значениям КБЖУ
    3. Предлагай разнообразные, вкусные и здоровые варианты
    4. Вернуть только JSON-массив, без дополнительных пояснений
    5. Примеры блюд должны быть на русском языке
    6. Придерживайся обычных продуктов, доступных в России
    """

    # Формируем список приемов пищи
    meals_info = []
    for meal in meal_plan:
        meal_info = (
            f"- {meal['meal']}: {meal['calories']} ккал, "
            f"{meal['protein']} г белка, {meal['fat']} г жиров, "
            f"{meal['carbs']} г углеводов"
        )
        meals_info.append(meal_info)

    meals_text = "\n".join(meals_info)

    user_prompt = (
        "Предложи варианты блюд для следующих приемов пищи с указанным КБЖУ:\n\n"
        f"{meals_text}\n\n"
        "Для каждого приема пищи предложи 2-3 варианта блюд. "
        "Верни результат в формате JSON:\n"
        '[{"meal": "Название приема", "examples": "Примеры блюд через запятую"}, ...]'
    )

    client = get_openai_client()
    logger.info("Запрос к OpenAI для генерации примеров блюд")

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

            logger.info(
                f"Успешно сгенерированы примеры блюд для {len(examples)} приемов пищи"
            )

            # Объединяем примеры с базовым планом питания
            result = []
            for meal_data in meal_plan:
                meal_name = meal_data["meal"]
                # Ищем примеры для текущего приема пищи
                example_text = ""
                for example in examples:
                    if example.get("meal") == meal_name:
                        example_text = example.get("examples", "")
                        break

                # Добавляем данные о примерах блюд к базовому плану
                meal_data["examples"] = example_text
                result.append(meal_data)

            return result

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Ошибка при обработке ответа OpenAI: {e}")
            logger.debug(f"Проблемный ответ: {response}")
            # Если не удалось получить корректный JSON, возвращаем план без примеров
            return meal_plan

    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        # В случае ошибки при запросе к API, возвращаем план без примеров
        return meal_plan
