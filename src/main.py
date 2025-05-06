import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from src.bot.db.connection import get_db_connection
from src.bot.handlers.user_dialog import router as dialog_router
from src.bot.middlewares.repository import RepositoryMiddleware
from src.bot.repository.user_repository import UserRepository
from src.core.logger import error_logger, main_logger

# Load environment variables
load_dotenv()


async def main():
    """Main function to start the bot"""
    # Get token from environment variable
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        error_logger.error("No BOT_TOKEN provided in .env file")
        return

    # Initialize database connection
    db_connector = await get_db_connection()

    # Create repository factory
    def user_repo_factory():
        return UserRepository(db_connector)

    # Set up the bot and dispatcher
    bot = Bot(token=bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Add middleware to router
    repo_middleware = RepositoryMiddleware(user_repo_factory)
    dialog_router.message.outer_middleware(repo_middleware)
    dialog_router.callback_query.outer_middleware(
        RepositoryMiddleware(user_repo_factory)
    )

    # Register routers
    dp.include_router(dialog_router)

    # Start polling
    main_logger.info("Starting bot")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        main_logger.info("Bot stopped")
    except Exception as e:
        error_msg = f"Unexpected error: {e}"
        error_logger.error(error_msg, exc_info=True)
