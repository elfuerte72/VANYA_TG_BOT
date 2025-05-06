from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline_kb import (
    get_activity_keyboard,
    get_confirmation_keyboard,
    get_gender_keyboard,
    get_start_keyboard,
)
from src.bot.models.state import UserForm
from src.bot.repository.user_repository import UserRepository
from src.bot.services.calculation import CalculationService
from src.bot.services.subscription import SubscriptionService
from src.bot.utils.formatters import format_kbju_result, format_user_data_summary
from src.bot.utils.validators import validate_age, validate_height, validate_weight
from src.config.settings import ADMIN_USER_IDS

# Initialize router
router = Router()

# Configuration - обновлено на правильный ID канала
REQUIRED_CHANNEL = "https://t.me/+6lrBYf4y9DlmOTQy"


# Вспомогательная функция для безопасного изменения сообщения
async def safe_edit_message(message, text, reply_markup=None, parse_mode=None):
    """
    Безопасно изменяет сообщение, обрабатывая исключение TelegramBadRequest
    """
    try:
        await message.edit_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            # Игнорируем ошибку, если сообщение не изменилось
            pass
        else:
            # Если другая ошибка BadRequest, пробуем отправить новое сообщение
            await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )


# Helper function to check subscription
async def check_subscription(bot: Bot, user_id: int) -> bool:
    """Check if user is subscribed to the required channel"""
    return await SubscriptionService.is_subscribed(bot, user_id, REQUIRED_CHANNEL)


# Command handlers
@router.message(CommandStart())
async def command_start(message: Message, bot: Bot):
    """Handler for /start command"""
    # Check if user is subscribed to the channel
    if message.from_user and not await check_subscription(bot, message.from_user.id):
        await message.answer(
            "Для использования бота необходимо подписаться на канал: "
            f"{REQUIRED_CHANNEL}",
            reply_markup=get_start_keyboard(),
        )
        return

    # Send welcome message with start button
    await message.answer(
        "Добро пожаловать в бот расчета КБЖУ! "
        "Нажмите кнопку ниже, чтобы начать расчет.",
        reply_markup=get_start_keyboard(),
    )


# Callback query handlers
@router.callback_query(F.data == "start_calculation")
async def start_calculation(
    callback: CallbackQuery, state: FSMContext, bot: Bot, user_repo: UserRepository
):
    """Handle start calculation button click"""
    if not callback.from_user:
        return

    user_id = callback.from_user.id

    # Check if user is subscribed to the channel
    if not await check_subscription(bot, user_id):
        await safe_edit_message(
            callback.message,
            "Для использования бота необходимо подписаться на канал: "
            f"{REQUIRED_CHANNEL}",
            reply_markup=get_start_keyboard(),
        )
        return

    # Check if user has already calculated KBJU
    if await user_repo.user_exists(user_id):
        # Проверяем, рассчитаны ли уже КБЖУ и не является ли пользователь админом
        if await user_repo.is_calculated(user_id) and user_id not in ADMIN_USER_IDS:
            await safe_edit_message(
                callback.message,
                "Вы уже получили расчет КБЖУ. "
                "На данный момент повторный расчет недоступен.",
            )
            return
    else:
        # Create new user if not exists
        await user_repo.create_user(user_id)

    # Start the dialog - ask for gender
    await state.set_state(UserForm.await_gender)
    await safe_edit_message(
        callback.message, "Укажите ваш пол:", reply_markup=get_gender_keyboard()
    )


# Gender selection handler
@router.callback_query(StateFilter(UserForm.await_gender), F.data.startswith("gender:"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Process gender selection"""
    if not callback.data:
        return

    # Extract gender from callback data
    gender = callback.data.split(":")[1]  # "gender:male" -> "male"

    # Save gender to state
    await state.update_data(gender=gender)

    # Move to next state - ask for age
    await state.set_state(UserForm.await_age)
    await safe_edit_message(callback.message, "Укажите ваш возраст (полных лет):")


# Age input handler
@router.message(StateFilter(UserForm.await_age))
async def process_age(message: Message, state: FSMContext):
    """Process age input"""
    if not message.text:
        await message.answer("Пожалуйста, введите число.")
        return

    # Validate age
    is_valid, age_value, error_msg = validate_age(message.text)

    if not is_valid and error_msg:
        await message.answer(error_msg)
        return

    # Save age to state
    await state.update_data(age=age_value)

    # Move to next state - ask for height
    await state.set_state(UserForm.await_height)
    await message.answer("Укажите ваш рост (в сантиметрах):")


# Height input handler
@router.message(StateFilter(UserForm.await_height))
async def process_height(message: Message, state: FSMContext):
    """Process height input"""
    if not message.text:
        await message.answer("Пожалуйста, введите число.")
        return

    # Validate height
    is_valid, height_value, error_msg = validate_height(message.text)

    if not is_valid and error_msg:
        await message.answer(error_msg)
        return

    # Save height to state
    await state.update_data(height=height_value)

    # Move to next state - ask for weight
    await state.set_state(UserForm.await_weight)
    await message.answer("Укажите ваш вес (в килограммах):")


# Weight input handler
@router.message(StateFilter(UserForm.await_weight))
async def process_weight(message: Message, state: FSMContext):
    """Process weight input"""
    if not message.text:
        await message.answer("Пожалуйста, введите число.")
        return

    # Validate weight
    is_valid, weight_value, error_msg = validate_weight(message.text)

    if not is_valid and error_msg:
        await message.answer(error_msg)
        return

    # Save weight to state
    await state.update_data(weight=weight_value)

    # Move to next state - ask for activity level
    await state.set_state(UserForm.await_activity)
    await message.answer(
        "Укажите ваш уровень физической активности:",
        reply_markup=get_activity_keyboard(),
    )


# Activity level selection handler
@router.callback_query(
    StateFilter(UserForm.await_activity), F.data.startswith("activity:")
)
async def process_activity(callback: CallbackQuery, state: FSMContext):
    """Process activity level selection"""
    if not callback.data:
        return

    # Extract activity level from callback data
    activity = callback.data.split(":")[1]  # "activity:low" -> "low"

    # Save activity level to state
    await state.update_data(activity=activity)

    # Move to confirmation state
    await state.set_state(UserForm.confirmation)

    # Get all collected data
    user_data = await state.get_data()

    # Format data for confirmation message
    message_text = format_user_data_summary(user_data)

    # Send confirmation message with keyboard for editing
    await safe_edit_message(
        callback.message,
        message_text,
        reply_markup=get_confirmation_keyboard(),
        parse_mode="HTML",
    )


# Edit data handlers
@router.callback_query(StateFilter(UserForm.confirmation), F.data.startswith("edit:"))
async def process_edit(callback: CallbackQuery, state: FSMContext):
    """Process edit button clicks"""
    if not callback.data:
        return

    # Extract field to edit from callback data
    field = callback.data.split(":")[1]  # "edit:gender" -> "gender"

    if field == "gender":
        await state.set_state(UserForm.await_gender)
        await safe_edit_message(
            callback.message, "Укажите ваш пол:", reply_markup=get_gender_keyboard()
        )
    elif field == "age":
        await state.set_state(UserForm.await_age)
        await safe_edit_message(callback.message, "Укажите ваш возраст (полных лет):")
    elif field == "height":
        await state.set_state(UserForm.await_height)
        await safe_edit_message(callback.message, "Укажите ваш рост (в сантиметрах):")
    elif field == "weight":
        await state.set_state(UserForm.await_weight)
        await safe_edit_message(callback.message, "Укажите ваш вес (в килограммах):")
    elif field == "activity":
        await state.set_state(UserForm.await_activity)
        await safe_edit_message(
            callback.message,
            "Укажите ваш уровень физической активности:",
            reply_markup=get_activity_keyboard(),
        )


# Confirmation handler
@router.callback_query(StateFilter(UserForm.confirmation), F.data == "confirm")
async def process_confirm(
    callback: CallbackQuery, state: FSMContext, user_repo: UserRepository
):
    """Process confirmation button click"""
    if not callback.from_user:
        return

    # Set calculation state
    await state.set_state(UserForm.calculation)

    # Get user data from state
    user_data = await state.get_data()

    # Преобразовать поле activity в activity_factor
    activity_values = {"low": 1.2, "medium": 1.55, "high": 1.725}
    activity = user_data.get("activity", "medium")
    activity_factor = activity_values.get(activity, 1.55)

    # Создаем словарь с данными для сохранения в БД
    db_data = {
        "gender": user_data.get("gender"),
        "age": user_data.get("age"),
        "height": user_data.get("height"),
        "weight": user_data.get("weight"),
        "activity_factor": activity_factor,
    }

    # Calculate KBJU
    result = CalculationService.calculate_kbju(
        gender=user_data["gender"],
        weight=user_data["weight"],
        height=user_data["height"],
        age=user_data["age"],
        activity=user_data["activity"],
    )

    # Format result message
    message_text = format_kbju_result(result)

    # Send result
    await safe_edit_message(callback.message, message_text, parse_mode="HTML")

    # Save user data to database
    user_id = callback.from_user.id
    await user_repo.update_user_data(user_id, db_data)

    # Mark user as calculated
    await user_repo.mark_calculated(user_id)

    # Finish the dialog
    await state.set_state(UserForm.finish)
    await state.clear()


# Handle messages during active dialog
@router.message(~StateFilter(None), ~F.text.startswith("/"))
async def process_unknown_message(message: Message):
    """Handle any messages during active dialog that don't match other handlers"""
    await message.answer(
        "Пожалуйста, следуйте инструкциям или используйте кнопки для ответа."
    )
