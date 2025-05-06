from aiogram.fsm.state import State, StatesGroup


class UserForm(StatesGroup):
    """FSM states for user dialog flow to calculate KBJU"""

    # Initial states
    await_gender = State()
    await_age = State()
    await_height = State()
    await_weight = State()
    await_activity = State()

    # Confirmation and final states
    confirmation = State()
    calculation = State()
    finish = State()
