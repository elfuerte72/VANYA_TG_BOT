# Docker Files

Эта папка содержит различные Docker файлы для разных сценариев развёртывания.

## Файлы

### `Dockerfile.local`
Основной Dockerfile для локальной разработки с полным функционалом:
- Поддержка шифрования базы данных (SQLCipher)
- Все зависимости включены
- Для использования: `docker build -f docker/Dockerfile.local -t vanya-tg-bot .`

### `Dockerfile.poetry`
Dockerfile для сборки с Poetry:
- Использует Poetry для управления зависимостями
- Подходит для разработки
- Для использования: `docker build -f docker/Dockerfile.poetry -t vanya-tg-bot-poetry .`

### `docker-compose.yml`
Конфигурация для локальной разработки:
- Включает volume для логов
- Переменные окружения из `.env`
- Для использования: `docker-compose -f docker/docker-compose.yml up`

### `docker-compose.prod.yml`
Конфигурация для продакшена:
- Оптимизирована для production
- Включает healthcheck
- Для использования: `docker-compose -f docker/docker-compose.prod.yml up`

## Основные файлы в корне

### `Dockerfile`
Основной Dockerfile для Railway deployment:
- Упрощённая версия без SQLCipher
- Использует `requirements.railway.txt`
- Автоматически используется Railway

### `requirements.railway.txt`
Зависимости для Railway без SQLCipher и с совместимыми версиями. 