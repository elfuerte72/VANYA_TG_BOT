from typing import Dict


class CalculationService:
    """Service for calculating BMR and macronutrients"""

    # Activity level coefficients
    ACTIVITY_LEVELS = {"low": 1.2, "medium": 1.55, "high": 1.725}

    # Default activity level
    DEFAULT_ACTIVITY = "medium"

    # Goal modifiers (калорийность)
    GOAL_CALORIE_MODIFIERS = {
        "weightloss": 0.8,  # Дефицит 20% для похудения
        "musclegain": 1.15,  # Профицит 15% для набора массы
        "recomp": 0.95,  # Небольшой дефицит 5% для рекомпозиции
    }

    # Макронутриенты для разных целей (% от калорий)
    GOAL_MACROS = {
        "weightloss": {
            "protein_percent": 0.30,  # 30% белка для похудения
            "fat_percent": 0.30,  # 30% жиров для похудения
            "carbs_percent": 0.40,  # 40% углеводов для похудения
        },
        "musclegain": {
            "protein_percent": 0.25,  # 25% белка для набора массы
            "fat_percent": 0.20,  # 20% жиров для набора массы
            "carbs_percent": 0.55,  # 55% углеводов для набора массы
        },
        "recomp": {
            "protein_percent": 0.35,  # 35% белка для рекомпозиции
            "fat_percent": 0.25,  # 25% жиров для рекомпозиции
            "carbs_percent": 0.40,  # 40% углеводов для рекомпозиции
        },
        "default": {
            "protein_percent": 0.20,  # 20% белка по умолчанию
            "fat_percent": 0.25,  # 25% жиров по умолчанию
            "carbs_percent": 0.55,  # 55% углеводов по умолчанию
        },
    }

    @staticmethod
    def calc_bmr_male(weight: float, height: int, age: int) -> float:
        """
        Calculate BMR for male using Harris-Benedict formula

        BMR = 66.47 + 13.75 × weight(kg) + 5.0 × height(cm) – 6.76 × age(years)
        """
        return 66.47 + (13.75 * weight) + (5.0 * height) - (6.76 * age)

    @staticmethod
    def calc_bmr_female(weight: float, height: int, age: int) -> float:
        """
        Calculate BMR for female using Harris-Benedict formula

        BMR = 655.1 + 9.56 × weight(kg) + 1.85 × height(cm) – 4.68 × age(years)
        """
        return 655.1 + (9.56 * weight) + (1.85 * height) - (4.68 * age)

    @classmethod
    def get_activity_factor(cls, activity: str) -> float:
        """Get activity factor based on activity level"""
        return cls.ACTIVITY_LEVELS.get(
            activity.lower(), cls.ACTIVITY_LEVELS[cls.DEFAULT_ACTIVITY]
        )

    @classmethod
    def get_calorie_modifier(cls, goal: str) -> float:
        """Get calorie modifier based on goal"""
        return cls.GOAL_CALORIE_MODIFIERS.get(goal.lower(), 1.0)

    @classmethod
    def calculate_macros(
        cls, calories: float, goal: str = "default"
    ) -> Dict[str, float]:
        """
        Calculate macronutrients based on calories and goal

        Args:
            calories: Total daily calories
            goal: User's goal (weightloss, musclegain, recomp, or default)

        Returns:
            Dict with protein, fat, and carbs in grams
        """
        # Get macro percentages based on goal
        macro_percents = cls.GOAL_MACROS.get(goal.lower(), cls.GOAL_MACROS["default"])

        protein_percent = macro_percents["protein_percent"]
        fat_percent = macro_percents["fat_percent"]
        carbs_percent = macro_percents["carbs_percent"]

        protein_grams = calories * protein_percent / 4  # 4 ккал/г белка
        fat_grams = calories * fat_percent / 9  # 9 ккал/г жира
        carbs_grams = calories * carbs_percent / 4  # 4 ккал/г углеводов

        return {
            "protein": round(protein_grams, 1),
            "fat": round(fat_grams, 1),
            "carbs": round(carbs_grams, 1),
        }

    @staticmethod
    def get_meal_count(calories: float) -> int:
        """
        Determine number of meals based on total calories

        < 2000 calories: 3 meals
        >= 2000 calories: 4 meals
        """
        return 4 if calories >= 2000 else 3

    @classmethod
    def calculate_kbju(
        cls,
        gender: str,
        weight: float,
        height: int,
        age: int,
        activity: str,
        goal: str = "default",
    ) -> Dict:
        """
        Calculate full KBJU (calories, protein, fat, carbs) based on user parameters and goal

        Args:
            gender: User's gender (male/female)
            weight: Weight in kg
            height: Height in cm
            age: Age in years
            activity: Activity level (low/medium/high)
            goal: User's goal (weightloss/musclegain/recomp)

        Returns:
            Dict with calories, protein, fat, carbs and meal_count
        """
        # Calculate BMR based on gender
        if gender.lower() == "male":
            bmr = cls.calc_bmr_male(weight, height, age)
        else:
            bmr = cls.calc_bmr_female(weight, height, age)

        # Apply activity factor
        activity_factor = cls.get_activity_factor(activity)
        maintenance_calories = bmr * activity_factor

        # Apply goal modifier to calories
        calorie_modifier = cls.get_calorie_modifier(goal)
        total_calories = maintenance_calories * calorie_modifier

        # Calculate macronutrients based on goal
        macros = cls.calculate_macros(total_calories, goal)
        meal_count = cls.get_meal_count(total_calories)

        # Prepare result
        result = {
            "calories": round(total_calories),
            "protein": macros["protein"],
            "fat": macros["fat"],
            "carbs": macros["carbs"],
            "meal_count": meal_count,
        }

        return result
