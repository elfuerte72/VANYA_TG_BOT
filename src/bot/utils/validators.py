from typing import Optional, Tuple


def validate_age(value: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate user age input

    Args:
        value: Age as string

    Returns:
        Tuple containing:
        - bool: True if valid, False otherwise
        - Optional[int]: Parsed age value if valid, None otherwise
        - Optional[str]: Error message if invalid, None otherwise
    """
    try:
        age = int(value.strip())

        # Check age range (12-100)
        if age < 12:
            return False, None, "Возраст должен быть не менее 12 лет"
        if age > 100:
            return False, None, "Возраст должен быть не более 100 лет"

        return True, age, None
    except ValueError:
        return False, None, "Пожалуйста, введите целое число"


def validate_height(value: str) -> Tuple[bool, Optional[int], Optional[str]]:
    """
    Validate user height input

    Args:
        value: Height as string (in cm)

    Returns:
        Tuple containing:
        - bool: True if valid, False otherwise
        - Optional[int]: Parsed height value if valid, None otherwise
        - Optional[str]: Error message if invalid, None otherwise
    """
    try:
        height = int(value.strip())

        # Check height range (100-250 cm)
        if height < 100:
            return False, None, "Рост должен быть не менее 100 см"
        if height > 250:
            return False, None, "Рост должен быть не более 250 см"

        return True, height, None
    except ValueError:
        return False, None, "Пожалуйста, введите целое число"


def validate_weight(value: str) -> Tuple[bool, Optional[float], Optional[str]]:
    """
    Validate user weight input

    Args:
        value: Weight as string (in kg)

    Returns:
        Tuple containing:
        - bool: True if valid, False otherwise
        - Optional[float]: Parsed weight value if valid, None otherwise
        - Optional[str]: Error message if invalid, None otherwise
    """
    try:
        # Replace comma with dot if present (for Russian number format)
        clean_value = value.strip().replace(",", ".")
        weight = float(clean_value)

        # Check weight range (30-300 kg)
        if weight < 30:
            return False, None, "Вес должен быть не менее 30 кг"
        if weight > 300:
            return False, None, "Вес должен быть не более 300 кг"

        return True, weight, None
    except ValueError:
        return False, None, "Пожалуйста, введите число"
