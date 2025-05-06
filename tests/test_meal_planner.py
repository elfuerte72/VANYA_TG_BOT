"""
Тесты для модуля генерации плана питания.
"""

import json
import unittest
from unittest.mock import MagicMock, patch

from src.ai.meal_planner import _generate_default_meal_plan, generate_meal_plan


class TestMealPlanner(unittest.TestCase):
    """Тестовый класс для проверки функций генерации плана питания."""

    def test_generate_default_meal_plan_3_meals(self):
        """Проверка генерации плана питания по умолчанию для 3 приемов пищи."""
        kbju_data = {"calories": 1800, "protein": 120, "fat": 60, "carbs": 180}

        result = _generate_default_meal_plan(kbju_data, 3)

        # Проверяем количество приемов пищи
        self.assertEqual(len(result), 3)

        # Проверяем названия приемов пищи
        self.assertEqual(result[0]["meal"], "Завтрак")
        self.assertEqual(result[1]["meal"], "Обед")
        self.assertEqual(result[2]["meal"], "Ужин")

        # Проверяем распределение калорий
        self.assertEqual(result[0]["calories"], round(1800 * 0.3))
        self.assertEqual(result[1]["calories"], round(1800 * 0.45))
        self.assertEqual(result[2]["calories"], round(1800 * 0.25))

        # Проверяем общую сумму (с округлением могут быть незначительные отклонения)
        total_calories = sum(meal["calories"] for meal in result)
        self.assertAlmostEqual(total_calories, 1800, delta=3)

    def test_generate_default_meal_plan_4_meals(self):
        """Проверка генерации плана питания по умолчанию для 4 приемов пищи."""
        kbju_data = {"calories": 2500, "protein": 150, "fat": 70, "carbs": 300}

        result = _generate_default_meal_plan(kbju_data, 4)

        # Проверяем количество приемов пищи
        self.assertEqual(len(result), 4)

        # Проверяем названия приемов пищи
        self.assertEqual(result[0]["meal"], "Завтрак")
        self.assertEqual(result[1]["meal"], "Обед")
        self.assertEqual(result[2]["meal"], "Полдник")
        self.assertEqual(result[3]["meal"], "Ужин")

        # Проверяем распределение калорий
        self.assertEqual(result[0]["calories"], round(2500 * 0.25))
        self.assertEqual(result[1]["calories"], round(2500 * 0.35))
        self.assertEqual(result[2]["calories"], round(2500 * 0.15))
        self.assertEqual(result[3]["calories"], round(2500 * 0.25))

        # Проверяем общую сумму (с округлением могут быть незначительные отклонения)
        total_calories = sum(meal["calories"] for meal in result)
        self.assertAlmostEqual(total_calories, 2500, delta=4)

    @patch("src.ai.meal_planner.get_openai_client")
    def test_generate_meal_plan_success(self, mock_get_client):
        """Проверка успешной генерации плана питания с помощью OpenAI."""
        # Входные данные
        kbju_data = {"calories": 2450, "protein": 160, "fat": 70, "carbs": 280}

        # Ожидаемый результат от OpenAI
        expected_result = [
            {"meal": "Завтрак", "calories": 600, "protein": 40, "fat": 15, "carbs": 70},
            {"meal": "Обед", "calories": 750, "protein": 50, "fat": 20, "carbs": 90},
            {"meal": "Полдник", "calories": 500, "protein": 30, "fat": 15, "carbs": 60},
            {"meal": "Ужин", "calories": 600, "protein": 40, "fat": 20, "carbs": 60},
        ]

        # Создаем мок-объект для клиента OpenAI
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Настраиваем, что должен вернуть метод get_completion
        mock_client.get_completion.return_value = json.dumps(expected_result)

        # Вызываем тестируемую функцию
        result = generate_meal_plan(kbju_data)

        # Проверяем, что функция вернула ожидаемый результат
        self.assertEqual(result, expected_result)

        # Проверяем, что клиент был вызван с правильными параметрами
        mock_client.get_completion.assert_called_once()

    @patch("src.ai.meal_planner.get_openai_client")
    def test_generate_meal_plan_error_handling(self, mock_get_client):
        """Проверка обработки ошибок при генерации плана питания."""
        # Входные данные
        kbju_data = {"calories": 2450, "protein": 160, "fat": 70, "carbs": 280}

        # Создаем мок-объект для клиента OpenAI
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Настраиваем, что метод get_completion вызовет исключение
        mock_client.get_completion.side_effect = Exception("API Error")

        # Вызываем тестируемую функцию
        result = generate_meal_plan(kbju_data)

        # Проверяем, что функция вернула план по умолчанию
        self.assertEqual(len(result), 4)  # Для 2450 калорий должно быть 4 приема пищи
        self.assertEqual(result[0]["meal"], "Завтрак")
        self.assertEqual(result[1]["meal"], "Обед")
        self.assertEqual(result[2]["meal"], "Полдник")
        self.assertEqual(result[3]["meal"], "Ужин")


if __name__ == "__main__":
    unittest.main()
