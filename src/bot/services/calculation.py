from typing import Dict


class CalculationService:
    """Service for calculating BMR and macronutrients"""

    # Activity level coefficients
    ACTIVITY_LEVELS = {"low": 1.2, "medium": 1.55, "high": 1.725}

    # Default activity level
    DEFAULT_ACTIVITY = "medium"

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

    @staticmethod
    def calculate_macros(calories: float) -> Dict[str, float]:
        """
        Calculate macronutrients based on calories

        Protein: 20% of calories (4 calories per gram)
        Fat: 25% of calories (9 calories per gram)
        Carbs: 55% of calories (4 calories per gram)
        """
        protein_grams = calories * 0.20 / 4
        fat_grams = calories * 0.25 / 9
        carbs_grams = calories * 0.55 / 4

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
        cls, gender: str, weight: float, height: int, age: int, activity: str
    ) -> Dict:
        """
        Calculate full KBJU (calories, protein, fat, carbs) based on user parameters
        """
        # Calculate BMR based on gender
        if gender.lower() == "male":
            bmr = cls.calc_bmr_male(weight, height, age)
        else:
            bmr = cls.calc_bmr_female(weight, height, age)

        # Apply activity factor
        activity_factor = cls.get_activity_factor(activity)
        total_calories = bmr * activity_factor

        # Calculate macronutrients
        macros = cls.calculate_macros(total_calories)
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
