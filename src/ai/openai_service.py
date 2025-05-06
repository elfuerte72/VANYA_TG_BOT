"""Модуль для работы с OpenAI API.

Этот модуль предоставляет классы и функции для взаимодействия
с ChatGPT 4.1 nano через OpenAI API.
"""

import json
import time
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Union

import openai
from loguru import logger
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from pydantic import BaseModel, Field, SecretStr

# Константы
DEFAULT_MODEL = "gpt-4.1-nano"  # Модель ChatGPT 4.1 nano
MAX_RETRIES = 3  # Максимальное количество повторных попыток при ошибке
BASE_RETRY_DELAY = 1  # Начальная задержка перед повторной попыткой (в секундах)

# Значения по умолчанию для конфигурации
DEFAULT_TEMPERATURE = 0.3
DEFAULT_MAX_TOKENS = 1000
DEFAULT_TOP_P = 1.0
DEFAULT_FREQUENCY_PENALTY = 0.0
DEFAULT_PRESENCE_PENALTY = 0.0


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
    temperature: float = Field(
        DEFAULT_TEMPERATURE, description="Температура генерации (0.0-1.0)"
    )
    max_tokens: int = Field(
        DEFAULT_MAX_TOKENS, description="Максимальное количество токенов в ответе"
    )
    top_p: float = Field(DEFAULT_TOP_P, description="Top-p для семплирования")
    frequency_penalty: float = Field(
        DEFAULT_FREQUENCY_PENALTY, description="Штраф за повторение частоты"
    )
    presence_penalty: float = Field(
        DEFAULT_PRESENCE_PENALTY, description="Штраф за присутствие"
    )


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
        self.config = OpenAIConfig(
            api_key=SecretStr(api_key),
            model=model,
            temperature=DEFAULT_TEMPERATURE,
            max_tokens=DEFAULT_MAX_TOKENS,
            top_p=DEFAULT_TOP_P,
            frequency_penalty=DEFAULT_FREQUENCY_PENALTY,
            presence_penalty=DEFAULT_PRESENCE_PENALTY,
        )
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
        # Если ответ уже в виде словаря, используем его напрямую
        if isinstance(response, dict):
            self._cache[cache_key] = response
            logger.debug("Ответ сохранен в кэш")
            return

        try:
            # Преобразуем ответ-объект в словарь для кэширования
            if hasattr(response, "model_dump"):
                # Новый API: используем model_dump() если доступен (pydantic v2)
                self._cache[cache_key] = response.model_dump()
                logger.debug("Ответ сохранен в кэш через model_dump")
                return
            elif hasattr(response, "dict"):
                # Pydantic v1 или другие объекты с методом dict()
                self._cache[cache_key] = response.dict()
                logger.debug("Ответ сохранен в кэш через dict")
                return
            elif hasattr(response, "__dict__"):
                # Обычные объекты с __dict__
                self._cache[cache_key] = response.__dict__
                logger.debug("Ответ сохранен в кэш через __dict__")
                return

            # Если ничего не подходит, делаем собственную сериализацию
            cache_data = {
                "id": getattr(response, "id", ""),
                "object": getattr(response, "object", ""),
                "created": getattr(response, "created", 0),
                "model": getattr(response, "model", ""),
                "choices": [],
                "usage": {},
            }

            # Обработка choices
            choices = getattr(response, "choices", [])
            for choice in choices:
                message = getattr(choice, "message", None)
                choice_data = {
                    "message": {
                        "role": getattr(message, "role", "assistant")
                        if message
                        else "assistant",
                        "content": getattr(message, "content", "") if message else "",
                    },
                    "finish_reason": getattr(choice, "finish_reason", ""),
                    "index": getattr(choice, "index", 0),
                }
                cache_data["choices"].append(choice_data)

            # Обработка usage
            usage = getattr(response, "usage", None)
            if usage:
                cache_data["usage"] = {
                    "prompt_tokens": getattr(usage, "prompt_tokens", 0),
                    "completion_tokens": getattr(usage, "completion_tokens", 0),
                    "total_tokens": getattr(usage, "total_tokens", 0),
                }

            self._cache[cache_key] = cache_data
            logger.debug("Ответ сохранен в кэш с ручной сериализацией")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в кэш: {e}")
            # В случае ошибки сериализации просто не кэшируем

    def chat_completion(
        self,
        messages: Sequence[Union[Dict[str, str], Message]],
        use_cache: bool = True,
        **kwargs,
    ) -> ChatCompletion:
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
        normalized_messages: List[ChatCompletionMessageParam] = [
            msg.model_dump() if isinstance(msg, Message) else msg for msg in messages
        ]

        # Проверяем кэш, если включено кэширование
        if use_cache:
            cache_key = self._generate_cache_key(normalized_messages, **kwargs)
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                return ChatCompletion(**cached_result)

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
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    messages=normalized_messages, **request_params
                )
                # Кэшируем результат, если включено кэширование
                if use_cache:
                    self._save_to_cache(cache_key, response)
                # Возвращаем результат в виде словаря
                return response
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

        # Возвращаем пустой ответ в случае, если все попытки не удались
        return {
            "id": "error",
            "created": int(time.time()),
            "model": self.config.model,
            "choices": [
                {
                    "message": {
                        "role": "assistant",
                        "content": "Произошла ошибка при обработке запроса.",
                    },
                    "finish_reason": "error",
                }
            ],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        }

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
        try:
            # Проверяем, является ли ответ объектом или словарем
            if hasattr(response, "choices") and len(response.choices) > 0:
                # Для нового API (объекты)
                return str(response.choices[0].message.content)
            elif (
                isinstance(response, dict)
                and response.get("choices")
                and len(response["choices"]) > 0
            ):
                # Для старого API (словари)
                return str(response["choices"][0]["message"]["content"])
            # Если ответ некорректный, возвращаем сообщение об ошибке
            return "Не удалось получить ответ от модели."
        except Exception as e:
            logger.error(f"Ошибка извлечения ответа: {e}")
            return "Не удалось получить ответ от модели из-за ошибки обработки."


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
