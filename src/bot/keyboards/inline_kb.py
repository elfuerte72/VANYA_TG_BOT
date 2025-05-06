from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_start_keyboard() -> InlineKeyboardMarkup:
    """Keyboard for the start command with a button to launch calculation"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="▶️ Запустить расчёт", callback_data="start_calculation"
        )
    )
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
    """Keyboard for confirming user data or returning to edit"""
    builder = InlineKeyboardBuilder()

    # Confirm button
    builder.add(InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"))

    # Edit buttons
    builder.add(
        InlineKeyboardButton(text="🔄 Изменить пол", callback_data="edit:gender"),
        InlineKeyboardButton(text="🔄 Изменить возраст", callback_data="edit:age"),
        InlineKeyboardButton(text="🔄 Изменить рост", callback_data="edit:height"),
        InlineKeyboardButton(text="🔄 Изменить вес", callback_data="edit:weight"),
        InlineKeyboardButton(
            text="🔄 Изменить активность", callback_data="edit:activity"
        ),
        InlineKeyboardButton(text="🔄 Изменить цель", callback_data="edit:goal"),
    )

    # One button per row
    builder.adjust(1)
    return builder.as_markup()
