import dotenv
from pydantic import BaseModel, Field

# Загружаем переменные окружения из .env файла
dotenv.load_dotenv()


class Settings(BaseModel):
    """
    Настройки приложения.
    Загружает и проверяет переменные окружения.
    """
    # Telegram Bot токен
    bot_token: str = Field(..., env="BOT_TOKEN")
    # OpenAI API ключ
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    # Путь к файлу базы данных
    db_path: str = Field("./data/users.db", env="DB_PATH")
    # Уровень логирования
    log_level: str = Field("INFO", env="LOG_LEVEL")
    
    class Config:
        """
        Конфигурация для Pydantic.
        """
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


# Создаем экземпляр настроек
settings = Settings()


def get_settings() -> Settings:
    """
    Возвращает экземпляр настроек приложения.
    Returns:
        Settings: Объект настроек с переменными окружения.
    """
    return settings
