"""Тесты для модуля работы с OpenAI API.

Модуль тестирует работу класса OpenAIClient, обработку ошибок и механизм кэширования.
"""

from unittest.mock import MagicMock, patch

import pytest
from openai import APIConnectionError, RateLimitError
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.completion_usage import CompletionUsage

from src.ai.openai_service import (
    OpenAIClient,
    OpenAIConnectionError,
    OpenAIRateLimitError,
    OpenAIRequestError,
)


# Фикстура для создания мока ответа от OpenAI API
@pytest.fixture
def mock_openai_response():
    """Создает мок ответа от OpenAI API в виде словаря."""
    # Возвращаем словарь вместо MagicMock объекта, чтобы соответствовать ожиданиям кода
    return {
        "id": "chatcmpl-123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-4-1106-nano",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "Это тестовый ответ от модели.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
    }


# Фикстура для настройки тестового клиента OpenAI
@pytest.fixture
def openai_client():
    """Создает тестовый клиент OpenAI."""
    return OpenAIClient(api_key="test_api_key")


# Тест для успешного создания и настройки клиента
@pytest.mark.parametrize(
    "api_key,model",
    [("test_api_key", "gpt-4-1106-nano"), ("another_key", "different-model")],
)
def test_openai_client_initialization(api_key, model):
    """Тест проверяет корректную инициализацию клиента OpenAI."""
    # Создаем клиент с разными параметрами
    client = OpenAIClient(api_key=api_key, model=model)
    # Проверяем, что клиент корректно настроен
    assert client.config.api_key.get_secret_value() == api_key
    assert client.config.model == model
    assert isinstance(client._cache, dict)


# Тест успешного запроса к API
def test_chat_completion_success(openai_client, mock_openai_response):
    """Тест проверяет успешный запрос к API OpenAI."""
    # Напрямую мокируем метод create в клиенте OpenAI
    mock_create = MagicMock(return_value=mock_openai_response)
    openai_client.client.chat.completions.create = mock_create

    # Формируем запрос к API
    messages = [{"role": "user", "content": "Привет, как дела?"}]
    response = openai_client.chat_completion(messages)

    # Проверяем, что запрос был корректно сформирован
    mock_create.assert_called_once()

    # Проверяем структуру ответа
    assert response["id"] == "chatcmpl-123"
    assert response["model"] == "gpt-4-1106-nano"
    assert len(response["choices"]) == 1
    assert (
        response["choices"][0]["message"]["content"] == "Это тестовый ответ от модели."
    )


# Тест кэширования ответов
def test_chat_completion_caching(openai_client, mock_openai_response):
    """Тест проверяет механизм кэширования ответов."""
    # Напрямую мокируем метод create в клиенте OpenAI
    mock_create = MagicMock(return_value=mock_openai_response)
    openai_client.client.chat.completions.create = mock_create

    # Формируем запрос к API
    messages = [{"role": "user", "content": "Тестовое сообщение"}]

    # Первый запрос должен идти в API
    response1 = openai_client.chat_completion(messages)

    # Второй запрос должен браться из кэша
    response2 = openai_client.chat_completion(messages)

    # Проверяем, что запрос к API был выполнен только один раз
    mock_create.assert_called_once()

    # Проверяем, что ответы идентичны
    assert response1 == response2


# Тест обработки ошибки соединения
def test_handle_connection_error(openai_client):
    """Тест проверяет обработку ошибки соединения."""
    # Напрямую мокируем метод create в клиенте OpenAI
    mock_create = MagicMock(side_effect=OpenAIConnectionError("Ошибка соединения"))
    openai_client.client.chat.completions.create = mock_create

    # Формируем запрос, который должен вызвать ошибку
    messages = [{"role": "user", "content": "Тест ошибки"}]

    # Проверяем, что возникает нужное исключение
    with pytest.raises(OpenAIConnectionError):
        openai_client.chat_completion(messages)


# Тест обработки превышения лимита запросов
def test_handle_rate_limit_error(openai_client):
    """Тест проверяет обработку ошибки превышения лимита запросов."""
    # Напрямую мокируем метод create в клиенте OpenAI
    mock_create = MagicMock(side_effect=OpenAIRateLimitError("Превышен лимит запросов"))
    openai_client.client.chat.completions.create = mock_create

    # Формируем запрос, который должен вызвать ошибку
    messages = [{"role": "user", "content": "Тест ошибки лимита"}]

    # Проверяем, что возникает нужное исключение
    with pytest.raises(OpenAIRateLimitError):
        openai_client.chat_completion(messages)


# Тест упрощенного метода get_completion
@patch.object(OpenAIClient, "chat_completion")
def test_get_completion(mock_chat_completion, openai_client):
    """Тест проверяет работу упрощенного метода get_completion."""
    # Настраиваем мок для имитации ответа от chat_completion
    mock_chat_completion.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Упрощенный ответ"}}]
    }
    # Вызываем метод get_completion
    response = openai_client.get_completion("Простой запрос")
    # Проверяем результат
    assert response == "Упрощенный ответ"
    # Проверяем, что chat_completion был вызван с правильными параметрами
    mock_chat_completion.assert_called_once()
    args, _ = mock_chat_completion.call_args
    assert len(args[0]) == 2  # должно быть два сообщения (система и пользователь)
    assert args[0][0]["role"] == "system"
    assert args[0][1]["role"] == "user"
    assert args[0][1]["content"] == "Простой запрос"
