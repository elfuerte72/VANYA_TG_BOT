from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard(
    show_calculation: bool = True, show_subscription: bool = True
) -> InlineKeyboardMarkup:
    """
    Keyboard for the start command with subscription check and calculation buttons

    Args:
        show_calculation: Флаг для отображения кнопки запуска расчета
        show_subscription: Флаг для отображения кнопки подписки

    Returns:
        InlineKeyboardMarkup: Клавиатура с кнопками
    """
    builder = InlineKeyboardBuilder()

    if show_subscription:
        builder.add(
            InlineKeyboardButton(text="Подписаться", callback_data="check_subscription")
        )

    if show_calculation:
        builder.add(
            InlineKeyboardButton(
                text="▶️ Запустить расчёт", callback_data="start_calculation"
            )
        )

    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_gender_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for gender selection"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="Мужской", callback_data="gender:male"),
        InlineKeyboardButton(text="Женский", callback_data="gender:female"),
    )
    builder.adjust(2)  # Two buttons in a row
    return builder.as_markup()


def get_activity_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for activity level selection"""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="Низкий", callback_data="activity:low"),
        InlineKeyboardButton(text="Средний", callback_data="activity:medium"),
        InlineKeyboardButton(text="Высокий", callback_data="activity:high"),
    )

    builder.adjust(3)  # Three buttons in a row
    return builder.as_markup()


def get_goal_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for goal selection"""
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text="Похудение", callback_data="goal:weightloss"),
        InlineKeyboardButton(
            text="Набор мышечной массы", callback_data="goal:musclegain"
        ),
        InlineKeyboardButton(text="Рекомпозиция", callback_data="goal:recomp"),
    )

    builder.adjust(1)  # One button per row
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for confirming user data"""
    builder = InlineKeyboardBuilder()

    # Only confirm button
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))

    builder.adjust(1)  # One button per row
    return builder.as_markup()
