"""
Сервис для расчета КБЖУ с использованием формулы Бенедикта.
"""
from dataclasses import dataclass
from src.config.settings import (
    ACTIVITY_MULTIPLIERS,
    CALORIES_THRESHOLD,
    PROTEIN_PERCENTAGE,
    FAT_PERCENTAGE,
    CARB_PERCENTAGE
)

@dataclass
class NutritionPlan:
    """Класс, представляющий результат расчета КБЖУ."""
    daily_calories: int
    proteins_g: int
    fats_g: int
    carbs_g: int
    meals_count: int
    meals_breakdown: list[dict]

def calculate_bmr(gender: str, weight: float, height: float, age: int) -> float:
    """
    Рассчитывает базовую скорость метаболизма (BMR) по формуле Бенедикта.

    Args:
        gender: Пол ('мужской' или 'женский')
        weight: Вес в кг
        height: Рост в см
        age: Возраст в годах

    Returns:
        float: Базовая скорость метаболизма (BMR)
    """
    if gender.lower() == "мужской":
        # Формула для мужчин
        bmr = 66.47 + (13.75 * weight) + (5.0 * height) - (6.76 * age)
    else:
        # Формула для женщин
        bmr = 655.1 + (9.56 * weight) + (1.85 * height) - (4.68 * age)

    return bmr

def calculate_nutrition_plan(
    gender: str,
    age: int,
    height: float,
    weight: float,
    activity_level: str = "medium"
) -> NutritionPlan:
    """
    Рассчитывает план питания с КБЖУ на основе данных пользователя.

    Args:
        gender: Пол ('мужской' или 'женский')
        age: Возраст в годах
        height: Рост в см
        weight: Вес в кг
        activity_level: Уровень активности ('low', 'medium', 'high')

    Returns:
        NutritionPlan: Объект с результатами расчета КБЖУ
    """
    # Получаем коэффициент активности
    activity_multiplier = ACTIVITY_MULTIPLIERS.get(activity_level.lower(), 1.55)

    # Рассчитываем BMR
    bmr = calculate_bmr(gender, weight, height, age)

    # Рассчитываем суточную норму калорий
    daily_calories = round(bmr * activity_multiplier)

    # Определяем количество приемов пищи
    meals_count = 4 if daily_calories >= CALORIES_THRESHOLD else 3

    # Рассчитываем граммы макронутриентов
    proteins_g = round((daily_calories * (PROTEIN_PERCENTAGE / 100)) / 4)  # 4 ккал/г белка
    fats_g = round((daily_calories * (FAT_PERCENTAGE / 100)) / 9)          # 9 ккал/г жира
    carbs_g = round((daily_calories * (CARB_PERCENTAGE / 100)) / 4)        # 4 ккал/г углеводов

    # Распределение по приемам пищи
    meals_breakdown = distribute_meals(daily_calories, proteins_g, fats_g, carbs_g, meals_count)

    return NutritionPlan(
        daily_calories=daily_calories,
        proteins_g=proteins_g,
        fats_g=fats_g,
        carbs_g=carbs_g,
        meals_count=meals_count,
        meals_breakdown=meals_breakdown
    )

def distribute_meals(daily_calories: int, proteins_g: int, fats_g: int, carbs_g: int, meals_count: int) -> list[dict]:
    """
    Распределяет КБЖУ по приемам пищи.

    Args:
        daily_calories: Суточная норма калорий
        proteins_g: Суточная норма белков в граммах
        fats_g: Суточная норма жиров в граммах
        carbs_g: Суточная норма углеводов в граммах
        meals_count: Количество приемов пищи

    Returns:
        list[dict]: Список с распределением КБЖУ по приемам пищи
    """
    meals = []

    if meals_count == 3:
        # Распределение для 3-х приемов пищи
        # Завтрак: 30%, Обед: 45%, Ужин: 25%
        distribution = [0.30, 0.45, 0.25]
        meal_names = ["Завтрак", "Обед", "Ужин"]
    else:
        # Распределение для 4-х приемов пищи
        # Завтрак: 25%, Обед: 35%, Полдник: 15%, Ужин: 25%
        distribution = [0.25, 0.35, 0.15, 0.25]
        meal_names = ["Завтрак", "Обед", "Полдник", "Ужин"]

    for i, (name, ratio) in enumerate(zip(meal_names, distribution)):
        meal = {
            "name": name,
            "calories": round(daily_calories * ratio),
            "proteins": round(proteins_g * ratio),
            "fats": round(fats_g * ratio),
            "carbs": round(carbs_g * ratio)
        }
        meals.append(meal)

    return meals
