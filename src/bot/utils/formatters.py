from typing import Dict, List, Tuple

from src.ai import generate_meal_examples


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
        f"<b>🍽️ Рекомендуемое количество приемов пищи:</b> {meal_count}\n\n"
    )

    # Добавляем план приемов пищи с использованием OpenAI
    try:
        kbju_data = {
            "calories": calories,
            "protein": protein,
            "fat": fat,
            "carbs": carbs,
        }

        # Генерация плана питания с примерами блюд
        meal_plan = generate_meal_examples(kbju_data)

        # Добавляем разделитель
        message += "<b>📝 Примерное распределение по приемам пищи:</b>\n\n"

        # Добавляем информацию о каждом приеме пищи
        for meal in meal_plan:
            meal_name = meal["meal"]
            meal_calories = meal["calories"]
            meal_protein = meal["protein"]
            meal_fat = meal["fat"]
            meal_carbs = meal["carbs"]
            meal_examples = meal.get("examples", "")

            message += (
                f"<b>{meal_name}</b>\n"
                f"🔸 Калории: {meal_calories} ккал\n"
                f"🔸 Белки: {meal_protein} г\n"
                f"🔸 Жиры: {meal_fat} г\n"
                f"🔸 Углеводы: {meal_carbs} г\n"
            )

            # Добавляем примеры блюд, если они есть
            if meal_examples:
                message += f"<b>🍲 Примеры блюд:</b> {meal_examples}\n"

            message += "\n"

    except Exception:
        # В случае ошибки просто пропускаем добавление плана питания
        pass

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
