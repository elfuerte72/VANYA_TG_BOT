from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.keyboards.inline_kb import (
    get_activity_keyboard,
    get_confirmation_keyboard,
    get_gender_keyboard,
    get_goal_keyboard,
    get_start_keyboard,
)
from src.bot.models.state import UserForm
from src.bot.repository.user_repository import UserRepository
from src.bot.services.calculation import CalculationService
from src.bot.services.subscription import SubscriptionService
from src.bot.utils.formatters import format_kbju_result, format_user_data_summary
from src.bot.utils.validators import validate_age, validate_height, validate_weight
from src.config.settings import ADMIN_USER_IDS
from src.core.logger import error_logger, user_logger

# Initialize router
router = Router()

# Configuration
REQUIRED_CHANNEL = "@ivanfit_health"


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
            error_logger.warning(f"Failed to edit message: {e!s}. Sending new message.")
            await message.answer(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )


# Helper function to check subscription
async def check_subscription_status(bot: Bot, user_id: int) -> bool:
    """Проверяет подписку пользователя на обязательный канал."""
    is_subscribed = await SubscriptionService.is_subscribed(
        bot, user_id, REQUIRED_CHANNEL
    )
    user_logger.info(
        f"User {user_id} subscription to {REQUIRED_CHANNEL}: "
        f"{'subscribed' if is_subscribed else 'not subscribed'}"
    )
    return is_subscribed


# Command handlers
@router.message(CommandStart())
async def command_start(message: Message, bot: Bot):
    """Обработчик команды /start."""
    user_id = message.from_user.id if message.from_user else "unknown"
    user_logger.info(f"User {user_id} started the bot with /start")

    if message.from_user:
        is_subscribed = await check_subscription_status(bot, message.from_user.id)
        if not is_subscribed:
            await message.answer(
                (
                    f"👋 Привет! Для использования бота, пожалуйста, подпишитесь "
                    f"на наш канал: {REQUIRED_CHANNEL}\n\n"
                    f'После подписки нажмите кнопку "🔄 Я подписался, проверить".'
                ),
                reply_markup=get_start_keyboard(
                    show_calculation=False, show_subscription_flow=True
                ),
            )
            return

        await message.answer(
            (
                "🎉 Отлично! Вы уже подписаны на канал.\n\n"
                "Добро пожаловать в бот для расчёта КБЖУ! "
                "Нажмите кнопку ниже, чтобы начать."
            ),
            reply_markup=get_start_keyboard(
                show_calculation=True, show_subscription_flow=False
            ),
        )
    else:
        # Случай, если message.from_user отсутствует (теоретически)
        await message.answer(
            "Не удалось определить пользователя. Попробуйте перезапустить бота командой /start."
        )


# Callback query handlers
@router.callback_query(F.data == "start_calculation")
async def start_calculation_callback(
    callback: CallbackQuery, state: FSMContext, bot: Bot, user_repo: UserRepository
):
    """Обрабатывает нажатие кнопки начала расчета."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user_logger.info(f"User {user_id} clicked 'start_calculation'")

    if not await check_subscription_status(bot, user_id):
        await safe_edit_message(
            callback.message,
            (
                f"Пожалуйста, сначала подпишитесь на канал {REQUIRED_CHANNEL}\n\n"
                f'Затем нажмите кнопку "🔄 Я подписался, проверить".'
            ),
            reply_markup=get_start_keyboard(
                show_calculation=False, show_subscription_flow=True
            ),
        )
        return

    if await user_repo.user_exists(user_id):
        if await user_repo.is_calculated(user_id) and user_id not in ADMIN_USER_IDS:
            user_logger.info(
                f"User {user_id} tried to recalculate but already has results"
            )
            await safe_edit_message(
                callback.message,
                "Вы уже получили расчет КБЖУ. "
                "Повторный расчет на данный момент недоступен.",
            )
            return
    else:
        user_logger.info(f"Creating new user: {user_id}")
        await user_repo.create_user(user_id)

    await state.set_state(UserForm.await_gender)
    user_logger.info(f"User {user_id} moved to UserForm.await_gender")
    await safe_edit_message(
        callback.message, "Укажите ваш пол:", reply_markup=get_gender_keyboard()
    )


# Gender selection handler
@router.callback_query(StateFilter(UserForm.await_gender), F.data.startswith("gender:"))
async def process_gender(callback: CallbackQuery, state: FSMContext):
    """Process gender selection"""
    if not callback.data or not callback.from_user:
        return

    user_id = callback.from_user.id
    # Extract gender from callback data
    gender = callback.data.split(":")[1]  # "gender:male" -> "male"
    user_logger.info(f"User {user_id} selected gender: {gender}")

    # Save gender to state
    await state.update_data(gender=gender)

    # Move to next state - ask for age
    await state.set_state(UserForm.await_age)
    user_logger.info(f"User {user_id} moved to age input")
    await safe_edit_message(callback.message, "Укажите ваш возраст (полных лет):")


# Age input handler
@router.message(StateFilter(UserForm.await_age))
async def process_age(message: Message, state: FSMContext):
    """Process age input"""
    if not message.text or not message.from_user:
        await message.answer("Пожалуйста, введите число.")
        return

    user_id = message.from_user.id
    # Validate age
    is_valid, age_value, error_msg = validate_age(message.text)

    if not is_valid and error_msg:
        user_logger.warning(
            f"User {user_id} entered invalid age: {message.text}. Error: {error_msg}"
        )
        await message.answer(error_msg)
        return

    user_logger.info(f"User {user_id} entered age: {age_value}")

    # Save age to state
    await state.update_data(age=age_value)

    # Move to next state - ask for height
    await state.set_state(UserForm.await_height)
    user_logger.info(f"User {user_id} moved to height input")
    await message.answer("Укажите ваш рост (в сантиметрах):")


# Height input handler
@router.message(StateFilter(UserForm.await_height))
async def process_height(message: Message, state: FSMContext):
    """Process height input"""
    if not message.text or not message.from_user:
        await message.answer("Пожалуйста, введите число.")
        return

    user_id = message.from_user.id
    # Validate height
    is_valid, height_value, error_msg = validate_height(message.text)

    if not is_valid and error_msg:
        user_logger.warning(
            f"User {user_id} entered invalid height: {message.text}. Error: {error_msg}"
        )
        await message.answer(error_msg)
        return

    user_logger.info(f"User {user_id} entered height: {height_value}")

    # Save height to state
    await state.update_data(height=height_value)

    # Move to next state - ask for weight
    await state.set_state(UserForm.await_weight)
    user_logger.info(f"User {user_id} moved to weight input")
    await message.answer("Укажите ваш вес (в килограммах):")


# Weight input handler
@router.message(StateFilter(UserForm.await_weight))
async def process_weight(message: Message, state: FSMContext):
    """Process weight input"""
    if not message.text or not message.from_user:
        await message.answer("Пожалуйста, введите число.")
        return

    user_id = message.from_user.id
    # Validate weight
    is_valid, weight_value, error_msg = validate_weight(message.text)

    if not is_valid and error_msg:
        user_logger.warning(
            f"User {user_id} entered invalid weight: {message.text}. Error: {error_msg}"
        )
        await message.answer(error_msg)
        return

    user_logger.info(f"User {user_id} entered weight: {weight_value}")

    # Save weight to state
    await state.update_data(weight=weight_value)

    # Move to next state - ask for activity level
    await state.set_state(UserForm.await_activity)
    user_logger.info(f"User {user_id} moved to activity selection")
    await message.answer(
        "Выберите уровень вашей физической активности:\n\n"
        "• Низкий — если вы работаете за компьютером, почти не ходите пешком и не занимаетесь спортом.\n"
        "• Средний — если вы ходите пешком хотя бы 30–60 минут в день или делаете лёгкие тренировки 1–3 раза в неделю.\n"
        "• Высокий — если вы занимаетесь спортом 3–5 раз в неделю или у вас физическая работа.",
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

    # Move to next state - ask for goal
    await state.set_state(UserForm.await_goal)
    await safe_edit_message(
        callback.message,
        "Какая у вас цель?",
        reply_markup=get_goal_keyboard(),
    )


# Goal selection handler
@router.callback_query(StateFilter(UserForm.await_goal), F.data.startswith("goal:"))
async def process_goal(callback: CallbackQuery, state: FSMContext):
    """Process goal selection"""
    if not callback.data:
        return

    # Extract goal from callback data
    goal = callback.data.split(":")[1]  # "goal:weightloss" -> "weightloss"

    # Save goal to state
    await state.update_data(goal=goal)

    # Move to confirmation state
    await state.set_state(UserForm.confirmation)

    # Show confirmation keyboard with user data summary
    user_data = await state.get_data()
    message_text = (
        format_user_data_summary(user_data)
        .replace(
            "Если все данные верны, нажмите кнопку «Подтвердить».\n"
            "Если хотите что-то изменить, воспользуйтесь соответствующими кнопками.",
            "",
        )
        .strip()
    )
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
            "Выберите уровень вашей физической активности:\n\n"
            "(Если весь день сидите — выбирайте низкий. "
            "Если двигаетесь или тренируетесь — выбирайте средний или высокий.)",
            reply_markup=get_activity_keyboard(),
        )
    elif field == "goal":
        await state.set_state(UserForm.await_goal)
        await safe_edit_message(
            callback.message,
            "Какая у вас цель?",
            reply_markup=get_goal_keyboard(),
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
        "goal": user_data.get("goal"),
    }

    # Получаем цель пользователя
    goal = user_data.get("goal", "default")

    # Calculate KBJU
    result = CalculationService.calculate_kbju(
        gender=user_data["gender"],
        weight=user_data["weight"],
        height=user_data["height"],
        age=user_data["age"],
        activity=user_data["activity"],
        goal=goal,
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


# Subscription check handler
@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback_handler(callback: CallbackQuery, bot: Bot):
    """Обрабатывает нажатие кнопки проверки подписки."""
    if not callback.from_user or not callback.message:
        return

    user_id = callback.from_user.id
    user_logger.info(f"User {user_id} clicked 'check_subscription'")
    is_subscribed = await check_subscription_status(bot, user_id)

    if not is_subscribed:
        await safe_edit_message(
            callback.message,
            (
                f"❌ Вы все еще не подписаны на канал {REQUIRED_CHANNEL}.\n\n"
                f"Пожалуйста, сначала подпишитесь, "
                f"затем нажмите кнопку проверки снова."
            ),
            reply_markup=get_start_keyboard(
                show_calculation=False, show_subscription_flow=True
            ),
        )
        await callback.answer(
            "Подписка не найдена. Попробуйте еще раз после подписки.", show_alert=True
        )
        return

    await safe_edit_message(
        callback.message,
        (
            "🎉 Отлично! Вы подписаны на канал.\n\n"
            "Теперь вы можете начать расчет КБЖУ. "
            "Нажмите кнопку ниже."
        ),
        reply_markup=get_start_keyboard(
            show_calculation=True, show_subscription_flow=False
        ),
    )
    await callback.answer("Подписка подтверждена!", show_alert=False)
