import logging
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)


def format_kbju_result(calculation: Dict) -> str:
    """
    Format KBJU calculation result as a formatted message

    Args:
        calculation: Dict with calculation results

    Returns:
        str: Formatted message with HTML formatting
    """
    calories = calculation["calories"]
    protein = calculation["protein"]
    fat = calculation["fat"]
    carbs = calculation["carbs"]
    meal_count = calculation["meal_count"]

    # Базовое сообщение с КБЖУ
    message = (
        f"<b>🔢 Ваш расчет КБЖУ:</b>\n\n"
        f"<b>📊 Суточная норма калорий:</b> {calories} ккал\n\n"
        f"<b>🥩 Белки:</b> {protein} г\n"
        f"<b>🥑 Жиры:</b> {fat} г\n"
        f"<b>🍞 Углеводы:</b> {carbs} г\n\n"
        f"<b>🍽️ Рекомендуемое количество приемов пищи:</b> "
        f"{meal_count}\n\n"
    )

    # Добавляем разделитель
    message += "<b>📝 Детальный план питания:</b>\n\n"

    # Определяем распределение по приемам пищи
    meal_distribution = distribute_meals(calories, protein, fat, carbs, meal_count)

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

    # Добавляем информацию о каждом приеме пищи в отдельных блоках
    for name, meal_data in meal_distribution:
        message += (
            f"<b>🍳 {name}</b>\n"
            f"Целевые значения:\n"
            f"🔸 Калории: {meal_data['calories']} ккал\n"
            f"🔸 Белки: {meal_data['protein']} г\n"
            f"🔸 Жиры: {meal_data['fat']} г\n"
            f"🔸 Углеводы: {meal_data['carbs']} г\n\n"
            f"Продукты (вес в сухом виде):\n{default_foods.get(name, '')}\n\n"
        )

    return message


def format_user_data_summary(data: Dict) -> str:
    """
    Format user data summary for confirmation

    Args:
        data: Dict with user data

    Returns:
        str: Formatted message with HTML formatting
    """
    # Map activity values to readable text
    activity_map = {"low": "Низкий", "medium": "Средний", "high": "Высокий"}

    # Map goal values to readable text
    goal_map = {
        "weightloss": "Похудение",
        "musclegain": "Набор мышечной массы",
        "recomp": "Рекомпозиция",
    }

    # Map gender values to readable text
    gender_map = {"male": "Мужской", "female": "Женский"}

    gender = gender_map.get(data.get("gender", ""), "Не указан")
    age = data.get("age", "Не указан")
    height = data.get("height", "Не указан")
    weight = data.get("weight", "Не указан")
    activity = activity_map.get(data.get("activity", ""), "Не указан")
    goal = goal_map.get(data.get("goal", ""), "Не указан")

    message = (
        f"<b>📋 Проверьте введенные данные:</b>\n\n"
        f"<b>👤 Пол:</b> {gender}\n"
        f"<b>🔢 Возраст:</b> {age} лет\n"
        f"<b>📏 Рост:</b> {height} см\n"
        f"<b>⚖️ Вес:</b> {weight} кг\n"
        f"<b>🏃 Уровень активности:</b> {activity}\n"
        f"<b>🎯 Цель:</b> {goal}\n\n"
        f"Если все данные верны, нажмите кнопку <b>«Подтвердить»</b>.\n"
        f"Если хотите что-то изменить, воспользуйтесь соответствующими кнопками."
    )

    return message


def distribute_meals(
    calories: int, protein: float, fat: float, carbs: float, meal_count: int
) -> List[Tuple[str, Dict]]:
    """
    Distribute total nutrition values across meals

    Args:
        calories: Total daily calories
        protein: Total daily protein (g)
        fat: Total daily fat (g)
        carbs: Total daily carbs (g)
        meal_count: Number of meals per day

    Returns:
        List of tuples (meal_name, meal_data)
    """
    # Define meal names and distributions based on meal count
    if meal_count == 3:
        meals = [("Завтрак", 0.3), ("Обед", 0.45), ("Ужин", 0.25)]
    else:  # 4 meals
        meals = [("Завтрак", 0.25), ("Обед", 0.35), ("Полдник", 0.15), ("Ужин", 0.25)]

    # Calculate values for each meal
    result = []
    for name, ratio in meals:
        meal_calories = round(calories * ratio)
        meal_protein = round(protein * ratio, 1)
        meal_fat = round(fat * ratio, 1)
        meal_carbs = round(carbs * ratio, 1)

        meal_data = {
            "calories": meal_calories,
            "protein": meal_protein,
            "fat": meal_fat,
            "carbs": meal_carbs,
        }

        result.append((name, meal_data))

    return result
