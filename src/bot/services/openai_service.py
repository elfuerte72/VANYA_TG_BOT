"""Модуль для работы с OpenAI API.

Этот модуль предоставляет классы и функции для взаимодействия
с ChatGPT 4.1 nano через OpenAI API.
"""

import json
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Union

import openai
from loguru import logger
from openai.types.chat import ChatCompletion
from pydantic import BaseModel, Field, SecretStr

# Константы
DEFAULT_MODEL = "gpt-4-1106-nano"  # Модель ChatGPT 4.1 nano
MAX_RETRIES = 3  # Максимальное количество повторных попыток при ошибке
BASE_RETRY_DELAY = 1  # Начальная задержка перед повторной попыткой (в секундах)


class OpenAIException(Exception):
    """Базовый класс для исключений связанных с OpenAI API."""

    pass


class OpenAIConnectionError(OpenAIException):
    """Ошибка соединения с OpenAI API."""

    pass


class OpenAIRequestError(OpenAIException):
    """Ошибка запроса к OpenAI API."""

    pass


class OpenAIRateLimitError(OpenAIException):
    """Ошибка превышения лимита запросов к OpenAI API."""

    pass


class Message(BaseModel):
    """Модель сообщения для API OpenAI."""

    role: str = Field(
        ..., description="Роль отправителя сообщения (system, user, assistant)"
    )
    content: str = Field(..., description="Содержание сообщения")


class OpenAIConfig(BaseModel):
    """Конфигурация для клиента OpenAI."""

    api_key: SecretStr = Field(..., description="API ключ для OpenAI")
    model: str = Field(DEFAULT_MODEL, description="Модель OpenAI для использования")
    temperature: float = Field(0.7, description="Температура генерации (0.0-1.0)")
    max_tokens: int = Field(
        1000, description="Максимальное количество токенов в ответе"
    )
    top_p: float = Field(1.0, description="Top-p для семплирования")
    frequency_penalty: float = Field(0.0, description="Штраф за повторение частоты")
    presence_penalty: float = Field(0.0, description="Штраф за присутствие")


class OpenAIClient:
    """Клиент для работы с OpenAI API.

    Этот класс предоставляет методы для отправки запросов к OpenAI API
    с обработкой ошибок и кэшированием ответов.

    Attributes:
        config: Конфигурация клиента OpenAI.
        client: Экземпляр клиента OpenAI.
        cache: Словарь для кэширования ответов.
    """

    def __init__(self, api_key: str, model: str = DEFAULT_MODEL) -> None:
        """Инициализация клиента OpenAI.

        Args:
            api_key: API ключ для OpenAI.
            model: Модель OpenAI для использования (по умолчанию: ChatGPT 4.1 nano).
        """
        self.config = OpenAIConfig(api_key=SecretStr(api_key), model=model)
        self.client = openai.OpenAI(api_key=api_key)
        # Внутренний кэш запросов/ответов
        self._cache: Dict[str, Dict[str, Any]] = {}
        logger.info(f"Инициализирован OpenAI клиент с моделью {model}")

    def _generate_cache_key(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Генерирует ключ для кэширования на основе запроса.

        Args:
            messages: Список сообщений для отправки в API.
            **kwargs: Дополнительные параметры запроса.

        Returns:
            Строка-ключ для кэширования.
        """
        # Создаем копию параметров для сериализации
        cache_data = {"messages": messages, "params": kwargs}
        # Сериализуем в JSON и используем как ключ
        return json.dumps(cache_data, sort_keys=True)

    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Получает результат из кэша по ключу.

        Args:
            cache_key: Ключ кэша.

        Returns:
            Кэшированный результат или None, если кэш не найден.
        """
        cached_result = self._cache.get(cache_key)
        if cached_result:
            logger.debug("Найден кэшированный ответ для запроса")
            return cached_result
        return None

    def _save_to_cache(self, cache_key: str, response: Any) -> None:
        """Сохраняет результат в кэш.

        Args:
            cache_key: Ключ кэша.
            response: Ответ для кэширования.
        """

        # Вспомогательная функция для извлечения значения из объекта или словаря
        def _get_value(obj: Any, key: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        # Если ответ уже в виде словаря, используем его напрямую
        if isinstance(response, dict):
            self._cache[cache_key] = response
            logger.debug("Ответ сохранен в кэш")
            return

        # Преобразуем ответ-объект в словарь для кэширования
        cache_data = {
            "id": _get_value(response, "id"),
            "object": _get_value(response, "object"),
            "created": _get_value(response, "created"),
            "model": _get_value(response, "model"),
            "choices": [],
        }

        choices = _get_value(response, "choices", [])
        for choice in choices:
            choice_data = {
                "message": {
                    "role": _get_value(_get_value(choice, "message"), "role"),
                    "content": _get_value(_get_value(choice, "message"), "content"),
                },
                "finish_reason": _get_value(choice, "finish_reason"),
                "index": _get_value(choice, "index", 0),
            }
            cache_data["choices"].append(choice_data)

        usage = _get_value(response, "usage", {})
        cache_data["usage"] = {
            "prompt_tokens": _get_value(usage, "prompt_tokens", 0),
            "completion_tokens": _get_value(usage, "completion_tokens", 0),
            "total_tokens": _get_value(usage, "total_tokens", 0),
        }

        self._cache[cache_key] = cache_data
        logger.debug("Ответ сохранен в кэш")

    def chat_completion(
        self,
        messages: List[Union[Dict[str, str], Message]],
        use_cache: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """Отправляет запрос на создание ответа в чате.

        Args:
            messages: Список сообщений для отправки в API.
            use_cache: Использовать ли кэширование (по умолчанию: True).
            **kwargs: Дополнительные параметры запроса.

        Returns:
            Ответ от OpenAI API.

        Raises:
            OpenAIConnectionError: Если возникла ошибка соединения.
            OpenAIRequestError: Если возникла ошибка запроса.
            OpenAIRateLimitError: Если превышен лимит запросов.
        """
        # Нормализуем сообщения в формат словаря
        normalized_messages = [
            msg.dict() if isinstance(msg, Message) else msg for msg in messages
        ]

        # Проверяем кэш, если включено кэширование
        if use_cache:
            cache_key = self._generate_cache_key(normalized_messages, **kwargs)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return cached_result

        # Параметры для запроса с учетом конфигурации и переданных параметров
        request_params = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "top_p": self.config.top_p,
            "frequency_penalty": self.config.frequency_penalty,
            "presence_penalty": self.config.presence_penalty,
            **kwargs,
        }

        # Попытка выполнить запрос с повторными попытками
        # Вспомогательная функция для извлечения значения из объекта или словаря
        def _get_value(obj: Any, key: str, default: Any = None) -> Any:
            """Получает значение из объекта или словаря"""
            if isinstance(obj, dict):
                return obj.get(key, default)
            return getattr(obj, key, default)

        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    messages=normalized_messages, **request_params
                )
                # Кэшируем результат, если включено кэширование
                if use_cache:
                    self._save_to_cache(cache_key, response)
                # Возвращаем результат в виде словаря

                # Если response уже словарь, возвращаем его как есть
                if isinstance(response, dict):
                    return response

                # Формируем словарь для объектного ответа
                result = {
                    "id": _get_value(response, "id"),
                    "created": _get_value(response, "created"),
                    "model": _get_value(response, "model"),
                    "choices": [],
                }

                # Обрабатываем варианты ответов
                choices = _get_value(response, "choices", [])
                for choice in choices:
                    choice_result = {
                        "finish_reason": _get_value(choice, "finish_reason"),
                        "message": {},
                    }

                    # Обрабатываем сообщение
                    message = _get_value(choice, "message", {})
                    choice_result["message"] = {
                        "role": _get_value(message, "role"),
                        "content": _get_value(message, "content"),
                    }

                    result["choices"].append(choice_result)

                # Обрабатываем информацию о использовании токенов
                usage = _get_value(response, "usage", {})
                result["usage"] = {
                    "prompt_tokens": _get_value(usage, "prompt_tokens", 0),
                    "completion_tokens": _get_value(usage, "completion_tokens", 0),
                    "total_tokens": _get_value(usage, "total_tokens", 0),
                }

                return result
            except openai.APIConnectionError as e:
                logger.error(f"Ошибка соединения с OpenAI API: {e}")
                # Если это последняя попытка, возбуждаем исключение
                if attempt == MAX_RETRIES - 1:
                    raise OpenAIConnectionError(
                        f"Не удалось соединиться с OpenAI API: {e}"
                    )
            except openai.RateLimitError as e:
                logger.warning(f"Превышен лимит запросов к OpenAI API: {e}")
                # Если это последняя попытка, возбуждаем исключение
                if attempt == MAX_RETRIES - 1:
                    raise OpenAIRateLimitError(
                        f"Превышен лимит запросов к OpenAI API: {e}"
                    )
            except openai.APIError as e:
                logger.error(f"Ошибка API OpenAI: {e}")
                # Если это последняя попытка, возбуждаем исключение
                if attempt == MAX_RETRIES - 1:
                    raise OpenAIRequestError(f"Ошибка запроса к OpenAI API: {e}")
            # Экспоненциальная задержка перед следующей попыткой
            retry_delay = BASE_RETRY_DELAY * (2**attempt)
            logger.info(f"Повторная попытка через {retry_delay} секунд...")
            time.sleep(retry_delay)

    def get_completion(
        self,
        prompt: str,
        system_message: str = "Ты - полезный ассистент. Отвечай на русском языке.",
        use_cache: bool = True,
        **kwargs,
    ) -> str:
        """Упрощенный метод для получения текстового ответа на запрос.

        Args:
            prompt: Текстовый запрос пользователя.
            system_message: Системное сообщение, определяющее роль ассистента.
            use_cache: Использовать ли кэширование (по умолчанию: True).
            **kwargs: Дополнительные параметры запроса.

        Returns:
            Текстовый ответ от модели.

        Raises:
            OpenAIConnectionError: Если возникла ошибка соединения.
            OpenAIRequestError: Если возникла ошибка запроса.
            OpenAIRateLimitError: Если превышен лимит запросов.
        """
        # Формируем сообщения для запроса
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt},
        ]
        # Отправляем запрос (это не асинхронный вызов, т.к. мы обертываем асинхронный метод)
        response = self.chat_completion(messages, use_cache=use_cache, **kwargs)
        # Извлекаем текст ответа
        if response and response.get("choices") and len(response["choices"]) > 0:
            # Явно преобразуем в строку, чтобы соответствовать типу возврата
            return str(response["choices"][0]["message"]["content"])
        # Если ответ некорректный, возвращаем сообщение об ошибке
        return "Не удалось получить ответ от модели."


# Создаем декорированную функцию для кэширования в памяти
@lru_cache(maxsize=128)
def get_cached_completion(prompt: str, system_message: str, model: str) -> str:
    """Кэшированная функция для получения ответов от OpenAI API.
    Использует декоратор lru_cache для кэширования ответов в памяти.
    Args:
        prompt: Текстовый запрос пользователя.
        system_message: Системное сообщение, определяющее роль ассистента.
        model: Модель OpenAI для использования.
        Returns:
        Текстовый ответ от модели.
    """
    # Этот метод будет автоматически кэшироваться через lru_cache
    # Фактическая реализация будет вызываться только при отсутствии в кэше
    client = get_openai_client()
    return client.get_completion(prompt, system_message, model=model)


# Синглтон для клиента OpenAI
_openai_client_instance = None


def get_openai_client() -> OpenAIClient:
    """Получает единственный экземпляр клиента OpenAI (синглтон).
    Returns:
        Экземпляр OpenAIClient.
    Raises:
        ValueError: Если API ключ не настроен или некорректен.
    """
    global _openai_client_instance
    if _openai_client_instance is None:
        from os import environ

        api_key = environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "API ключ OpenAI не найден. Установите переменную окружения OPENAI_API_KEY."
            )
        _openai_client_instance = OpenAIClient(api_key=api_key)
    return _openai_client_instance
