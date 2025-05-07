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
        + "ОДИН вариант для каждого приема пищи, который соответствует указанным "
        + "значениям КБЖУ.\n\n"
        + "Правила:\n"
        + "1. Для каждого приема пищи предложи список продуктов в текстовом формате\n"
        + "2. Каждый продукт должен быть указан в формате: 'продукт - Xг (сухой вес)'\n"
        + "3. Для каждого приема пищи верни текстовое описание в формате:\n"
        + "   - Продукт 1 - XXг (сухой вес)\n"
        + "   - Продукт 2 - XXг (сухой вес)\n"
        + "   Способ приготовления: описание\n"
        + "4. Каждый прием пищи должен быть в своем элементе массива\n"
        + "5. Используй только обычные продукты, доступные в России\n"
        + "6. Для круп/макарон указывай вес ДО варки\n"
        + "7. Для мяса указывай вес в сыром виде\n"
        + "8. Верни только JSON-массив без дополнительного текста"
    )

    # Формируем список приемов пищи с их КБЖУ
    meals_info = []
    for meal in meal_plan:
        meal_info = (
            f"- {meal['meal']}:\n"
            f"Калории: {meal['calories']} ккал\n"
            f"Белки: {meal['protein']} г\n"
            f"Жиры: {meal['fat']} г\n"
            f"Углеводы: {meal['carbs']} г"
        )
        meals_info.append(meal_info)

    meals_text = "\n\n".join(meals_info)

    user_prompt = (
        "Предложи набор продуктов для каждого приема пищи для следующего "
        "плана питания:\n\n"
        f"{meals_text}\n\n"
        "Для каждого приема пищи верни текстовое описание в формате JSON:\n"
        '[{"meal": "Название", "foods": "- Продукт 1 - XXг (сухой вес)\\n- Продукт 2 - XXг (сухой вес)\\nСпособ приготовления: описание"}, ...]\n\n'
        "Убедись, что JSON правильно форматирован и все строки экранированы."
    )

    client = get_openai_client()
    logger.info(
        f"Запрос к OpenAI для генерации списка продуктов на {meal_count} приемов пищи"
    )

    try:
        # Отправляем запрос к OpenAI
        response = client.get_completion(
            prompt=user_prompt, system_message=system_prompt
        )

        # Логгируем ответ для отладки
        logger.debug(f"Ответ OpenAI: {response}")

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
            try:
                examples = json.loads(response_text)

                # Если данные пришли, но не в нужном формате, попробуем преобразовать их
                if isinstance(examples, list) and examples:
                    # Проверяем наличие необходимых полей
                    processed_examples = []

                    for example in examples:
                        meal_name = None
                        foods_text = None

                        # Проверяем различные варианты ключей
                        for key in example:
                            # Ищем ключи с именем приема пищи
                            if key.lower() in [
                                "meal",
                                "прием_пищи",
                                "название",
                                "name",
                            ]:
                                meal_name = example[key]
                                # Стандартизуем названия
                                if (
                                    meal_name.lower() == "завтрак"
                                    or meal_name.lower() == "breakfast"
                                ):
                                    meal_name = "Завтрак"
                                elif (
                                    meal_name.lower() == "обед"
                                    or meal_name.lower() == "lunch"
                                ):
                                    meal_name = "Обед"
                                elif (
                                    meal_name.lower() == "полдник"
                                    or meal_name.lower() == "snack"
                                ):
                                    meal_name = "Полдник"
                                elif (
                                    meal_name.lower() == "ужин"
                                    or meal_name.lower() == "dinner"
                                ):
                                    meal_name = "Ужин"

                            # Ищем ключи с информацией о продуктах
                            if key.lower() in ["foods", "ингредиенты", "продукты"]:
                                value = example[key]
                                # Если получен список ингредиентов
                                if isinstance(value, list):
                                    ingredients_text = []
                                    for item in value:
                                        if isinstance(item, dict):
                                            product = item.get(
                                                "продукт", ""
                                            ) or item.get("product", "")
                                            weight = item.get("вес", "") or item.get(
                                                "weight", ""
                                            )
                                            ingredients_text.append(
                                                f"- {product} - {weight}"
                                            )
                                        else:
                                            ingredients_text.append(f"- {item}")
                                    foods_text = "\n".join(ingredients_text)
                                else:
                                    foods_text = value

                        # Добавляем информацию о способе приготовления, если есть
                        if (
                            "способ_приготовления" in example
                            or "cooking_method" in example
                        ):
                            method = example.get(
                                "способ_приготовления", ""
                            ) or example.get("cooking_method", "")
                            if method and foods_text:
                                foods_text += f"\nСпособ приготовления: {method}"

                        if meal_name and foods_text:
                            processed_examples.append(
                                {"meal": meal_name, "foods": foods_text}
                            )

                    examples = processed_examples
            except json.JSONDecodeError as decode_error:
                logger.error(f"Ошибка парсинга JSON: {decode_error}")
                # Пытаемся извлечь данные даже если JSON некорректен
                # Создаем базовый шаблон на основе полученного ответа
                examples = []
                for meal in meal_plan:
                    meal_name = meal["meal"]

                    # Ищем в тексте ответа информацию о данном приеме пищи
                    if meal_name.lower() in response_text.lower():
                        # Извлекаем примерный блок текста для этого приема пищи
                        start_text = meal_name.lower()
                        start_idx = response_text.lower().find(start_text)

                        if start_idx != -1:
                            # Ищем следующий прием пищи или конец текста
                            next_meal_idx = len(response_text)
                            for next_meal in ["завтрак", "обед", "полдник", "ужин"]:
                                if next_meal.lower() != meal_name.lower():
                                    next_idx = response_text.lower().find(
                                        next_meal, start_idx + len(start_text)
                                    )
                                    if next_idx != -1 and next_idx < next_meal_idx:
                                        next_meal_idx = next_idx

                            # Извлекаем текст между текущим и следующим приемом пищи
                            meal_text = response_text[start_idx:next_meal_idx].strip()
                            # Удаляем заголовок и форматируем как список продуктов
                            lines = meal_text.split("\n")
                            food_lines = []

                            for line in lines:
                                if (
                                    "- " in line
                                    or "• " in line
                                    or line.strip().startswith("*")
                                ):
                                    food_lines.append(line.strip())

                            if food_lines:
                                foods_text = "\n".join(food_lines)
                                examples.append(
                                    {"meal": meal_name, "foods": foods_text}
                                )

            # Проверяем результат и форматируем дальше
            if not examples:
                # Если не удалось получить нормальные данные, создаем шаблонные
                examples = []
                for meal in meal_plan:
                    meal_name = meal["meal"]
                    # Базовые рецепты для каждого приема пищи
                    default_foods = {
                        "Завтрак": (
                            "- Овсяные хлопья - 60г (сухой вес)\n"
                            "- Куриное яйцо - 2 шт (100г)\n"
                            "- Молоко 2.5% - 200мл\n"
                            "- Ягоды замороженные - 50г\n"
                            "Способ приготовления: овсянку варить на молоке, добавить яйца и ягоды"
                        ),
                        "Обед": (
                            "- Куриная грудка - 150г (сырой вес)\n"
                            "- Гречка - 70г (сухой вес)\n"
                            "- Овощи для салата - 150г\n"
                            "- Масло оливковое - 10г\n"
                            "Способ приготовления: куриную грудку запечь, гречку отварить"
                        ),
                        "Полдник": (
                            "- Творог 5% - 150г\n"
                            "- Орехи (миндаль) - 20г\n"
                            "- Фрукты (яблоко) - 150г\n"
                            "Способ приготовления: смешать творог с фруктами и орехами"
                        ),
                        "Ужин": (
                            "- Рыба (треска) - 150г (сырой вес)\n"
                            "- Рис - 70г (сухой вес)\n"
                            "- Овощи тушеные - 200г\n"
                            "Способ приготовления: рыбу запечь, рис отварить, овощи потушить"
                        ),
                    }
                    foods_text = default_foods.get(meal_name, "")
                    examples.append({"meal": meal_name, "foods": foods_text})

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

            logger.info(
                f"Успешно сгенерированы списки продуктов для {len(result)} приемов пищи"
            )
            return result

        except Exception as e:
            logger.error(f"Ошибка при обработке ответа OpenAI: {e}")
            logger.debug(f"Проблемный ответ: {response}")

            # Если не удалось получить корректный JSON, используем резервные данные
            return _add_default_foods_to_meal_plan(meal_plan)

    except Exception as e:
        logger.error(f"Ошибка при запросе к OpenAI: {e}")
        # В случае ошибки при запросе к API, используем резервные данные
        return _add_default_foods_to_meal_plan(meal_plan)


def _add_default_foods_to_meal_plan(meal_plan: List[Dict]) -> List[Dict]:
    """
    Добавляет стандартные списки продуктов к плану питания

    Args:
        meal_plan: Список приемов пищи с КБЖУ

    Returns:
        List[Dict]: Дополненный список приемов пищи с продуктами
    """
    # Базовые рецепты для каждого приема пищи
    default_foods = {
        "Завтрак": (
            "- Овсяные хлопья - 60г (сухой вес)\n"
            "- Куриное яйцо - 2 шт (100г)\n"
            "- Молоко 2.5% - 200мл\n"
            "- Ягоды замороженные - 50г\n"
            "Способ приготовления: овсянку варить на молоке, добавить яйца и ягоды"
        ),
        "Обед": (
            "- Куриная грудка - 150г (сырой вес)\n"
            "- Гречка - 70г (сухой вес)\n"
            "- Овощи для салата - 150г\n"
            "- Масло оливковое - 10г\n"
            "Способ приготовления: куриную грудку запечь, гречку отварить"
        ),
        "Полдник": (
            "- Творог 5% - 150г\n"
            "- Орехи (миндаль) - 20г\n"
            "- Фрукты (яблоко) - 150г\n"
            "Способ приготовления: смешать творог с фруктами и орехами"
        ),
        "Ужин": (
            "- Рыба (треска) - 150г (сырой вес)\n"
            "- Рис - 70г (сухой вес)\n"
            "- Овощи тушеные - 200г\n"
            "Способ приготовления: рыбу запечь, рис отварить, овощи потушить"
        ),
    }

    for meal in meal_plan:
        meal_name = meal["meal"]
        meal["foods"] = default_foods.get(meal_name, "")

    logger.info(f"Добавлены стандартные продукты для {len(meal_plan)} приемов пищи")
    return meal_plan
