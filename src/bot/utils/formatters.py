from typing import Dict, List, Tuple


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

    message = (
        f"<b>🔢 Ваш расчет КБЖУ:</b>\n\n"
        f"<b>📊 Суточная норма калорий:</b> {calories} ккал\n\n"
        f"<b>🥩 Белки:</b> {protein} г\n"
        f"<b>🥑 Жиры:</b> {fat} г\n"
        f"<b>🍞 Углеводы:</b> {carbs} г\n\n"
        f"<b>🍽️ Рекомендуемое количество приемов пищи:</b> {meal_count}\n\n"
    )

    # Add meal distribution
    message += "<b>📋 Распределение по приемам пищи:</b>\n\n"

    meals = distribute_meals(calories, protein, fat, carbs, meal_count)

    for i, (name, meal_data) in enumerate(meals, 1):
        message += (
            f"<b>{i}. {name}</b>\n"
            f"Калории: {meal_data['calories']} ккал\n"
            f"Белки: {meal_data['protein']} г\n"
            f"Жиры: {meal_data['fat']} г\n"
            f"Углеводы: {meal_data['carbs']} г\n\n"
        )

    message += (
        "<i>Этот расчет основан на формуле Харриса-Бенедикта "
        "и предназначен для общего ознакомления.</i>"
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

    # Map gender values to readable text
    gender_map = {"male": "Мужской", "female": "Женский"}

    gender = gender_map.get(data.get("gender", ""), "Не указан")
    age = data.get("age", "Не указан")
    height = data.get("height", "Не указан")
    weight = data.get("weight", "Не указан")
    activity = activity_map.get(data.get("activity", ""), "Не указан")

    message = (
        f"<b>📋 Проверьте введенные данные:</b>\n\n"
        f"<b>👤 Пол:</b> {gender}\n"
        f"<b>🔢 Возраст:</b> {age} лет\n"
        f"<b>📏 Рост:</b> {height} см\n"
        f"<b>⚖️ Вес:</b> {weight} кг\n"
        f"<b>🏃 Уровень активности:</b> {activity}\n\n"
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
