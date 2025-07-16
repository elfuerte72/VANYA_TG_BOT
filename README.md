# Telegram-бот расчёта КБЖУ

Бот для расчета персональных показателей КБЖУ (калории, белки, жиры, углеводы) на основе пользовательских данных.

## Функциональность

- Проверка подписки пользователя на канал
- Сбор данных через диалог (пол, возраст, рост, вес, уровень активности)
- Расчет КБЖУ по формуле Харриса-Бенедикта
- Распределение по приемам пищи
- Сохранение данных пользователя в базе данных
- Однократный расчет для каждого пользователя

## Установка и запуск

### 🐳 Docker (Рекомендуется)

#### Предварительные требования

- Docker 20.10+
- Docker Compose 2.0+

#### Быстрый старт

1. **Клонировать репозиторий:**
```bash
git clone <ссылка на репозиторий>
cd vanya_tg_bot
```

2. **Настроить переменные окружения:**
```bash
# Создать .env файл из шаблона
cp .env.docker.example .env

# Отредактировать .env файл
nano .env
```

3. **Запустить бота:**
```bash
# Для разработки
./deploy.sh development

# Для продакшена
./deploy.sh production

# Или используя Makefile
make setup  # Создает .env из шаблона
make dev    # Запуск в dev режиме
make prod   # Запуск в prod режиме
```

#### Управление Docker контейнерами

```bash
# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down

# Перезапуск
make restart

# Статус контейнеров
make status

# Очистка неиспользуемых ресурсов
make clean
```

#### Структура Docker файлов

- `Dockerfile` - основной образ приложения
- `docker-compose.yml` - конфигурация для разработки
- `docker-compose.prod.yml` - конфигурация для продакшена
- `deploy.sh` - скрипт автоматического деплоя
- `Makefile` - удобные команды для управления
- `healthcheck.py` - проверка здоровья контейнера

### 🐍 Локальная установка

#### Предварительные требования

- Python 3.10 или выше
- Poetry (менеджер пакетов)

#### Установка зависимостей

1. **Клонировать репозиторий:**
```bash
git clone <ссылка на репозиторий>
cd vanya_tg_bot
```

2. **Установить зависимости с помощью Poetry:**
```bash
poetry install
```

3. **Создать файл `.env` с необходимыми переменными окружения:**
```bash
cp .env.example .env
# Отредактировать .env файл
```

#### Локальный запуск

```bash
# Запуск через скрипт
./run.py

# или
python run.py

# или с использованием Poetry
poetry run python run.py
```

## Архитектура

- `src/bot/models/` - FSM состояния и модели данных
- `src/bot/handlers/` - обработчики команд и сообщений бота
- `src/bot/services/` - бизнес-логика (расчеты, проверка подписки)
- `src/bot/repository/` - работа с базой данных
- `src/bot/keyboards/` - клавиатуры для взаимодействия с ботом
- `src/bot/utils/` - вспомогательные функции
- `src/bot/db/` - подключение к базе данных
- `src/app_logging/` - настройка логирования

## Команды бота

- `/start` - начать диалог с ботом и запустить процедуру расчета КБЖУ

## Технологический стек

- **Язык программирования:** Python 3.10+
- **Фреймворк для бота:** aiogram 3.x
- **База данных:** SQLAlchemy + SQLModel (SQLite)
- **Генерация рекомендаций:** OpenAI API (GPT-4.1 nano)
- **Другие инструменты:**
  - pydantic для валидации данных
  - python-dotenv для управления конфигурацией
  - loguru для логирования

## Структура проекта

```
├── src/                    # Исходный код
│   ├── __init__.py
│   ├── main.py             # Точка входа
│   ├── config.py           # Конфигурация из .env
│   ├── bot/                # Логика бота
│   ├── db/                 # Модели данных и взаимодействие с БД
│   ├── services/           # Бизнес-логика и внешние сервисы
│   └── utils/              # Вспомогательные функции
├── tests/                  # Тесты
├── .env.example            # Шаблон переменных окружения
├── pyproject.toml          # Конфигурация Poetry и инструментов
├── run.py                  # Скрипт запуска
└── README.md               # Документация проекта
```

## Тестирование

### Локальное тестирование
```bash
poetry run pytest
```

### Тестирование в Docker
```bash
# Запуск тестов в контейнере
docker-compose exec vanya_tg_bot python -m pytest

# Проверка здоровья контейнера
docker-compose exec vanya_tg_bot python healthcheck.py
```

## Лицензия

Данный проект предназначен для использования только владельцем фитнес-канала и распространяется согласно условиям лицензии, указанной в файле LICENSE.

## Безопасность данных

В проекте реализовано шифрование конфиденциальных данных пользователей в базе данных.

### Подход к шифрованию

Для обеспечения безопасности хранения данных в базе используется следующий подход:

1. **Шифрование на уровне полей**: вместо шифрования всей базы данных, что может приводить к проблемам совместимости, реализовано шифрование отдельных чувствительных полей.

2. **Использование AES-256**: для шифрования используется алгоритм AES в режиме CBC с размером ключа 256 бит.

3. **Прозрачное шифрование/дешифрование**: реализовано с помощью собственного типа SQLAlchemy `EncryptedString`, который автоматически шифрует данные перед сохранением в базу и дешифрует при чтении.

4. **Защита парольной фразой**: ключ шифрования генерируется из секретной парольной фразы, хранящейся в переменных окружения.

### Использование шифрования

Для шифрования полей в модели достаточно использовать тип `EncryptedString` вместо обычного `String`:

```python
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from src.core.utils.encryption import EncryptedString

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    public_data = Column(String)  # Обычные данные
    secret_data = Column(EncryptedString)  # Зашифрованные данные
```

### Проверка шифрования

Для демонстрации работы шифрования можно использовать:

```bash
# Проверка шифрования полей
python -m src.tools.verify_field_encryption

# Демонстрация шифрования в модели пользователя
python -m src.tools.demo_user_encryption
```

### Безопасность ключа шифрования

Ключ шифрования (`DATABASE_SECRET_KEY`) должен храниться в переменных окружения и не должен попадать в систему контроля версий. В файле `.env` необходимо установить:

```
DATABASE_SECRET_KEY=ваш_надежный_секретный_ключ
```

## 🚀 Деплой на продакшен

### Railway (рекомендуется)

Railway - это платформа для деплоя приложений с автоматической настройкой и масштабированием.

1. **Подготовка к деплою:**
```bash
# Подготовка файлов для Railway
./deploy.railway.sh
```

2. **Создание проекта в Railway:**
   - Перейдите на [railway.app](https://railway.app)
   - Создайте новый проект
   - Подключите GitHub репозиторий

3. **Настройка переменных окружения в Railway Dashboard:**
```
BOT_TOKEN=ваш_токен_бота
OPENAI_API_KEY=ваш_ключ_openai
TELEGRAM_CHANNEL_ID=-1002504147240
LOG_LEVEL=INFO
DATABASE_SECRET_KEY=
```

4. **Деплой происходит автоматически** при push в main ветку

5. **Восстановление локальных файлов:**
```bash
# После деплоя
./restore.railway.sh
```

### VPS/Выделенный сервер

1. **Подготовка сервера:**
```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

2. **Клонирование проекта:**
```bash
git clone <ссылка на репозиторий>
cd vanya_tg_bot
```

3. **Настройка продакшен окружения:**
```bash
# Создание .env файла
cp .env.docker.example .env

# Редактирование конфигурации
nano .env
```

4. **Запуск в продакшене:**
```bash
# Автоматический деплой
./deploy.sh production

# Или вручную
docker-compose -f docker/docker-compose.prod.yml up --build -d
```

### Мониторинг и обслуживание

```bash
# Просмотр логов
docker-compose -f docker/docker-compose.prod.yml logs -f --tail=100

# Проверка статуса
docker-compose -f docker/docker-compose.prod.yml ps

# Перезапуск
docker-compose -f docker/docker-compose.prod.yml restart

# Обновление приложения
git pull
./deploy.sh production
```

### Автоматический запуск при рестарте сервера

```bash
# Создание systemd сервиса
sudo nano /etc/systemd/system/vanya-tg-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=Vanya Telegram Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/path/to/vanya_tg_bot
ExecStart=/usr/local/bin/docker-compose -f docker/docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker/docker-compose.prod.yml down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

```bash
# Активация сервиса
sudo systemctl enable vanya-tg-bot.service
sudo systemctl start vanya-tg-bot.service
```

### Резервное копирование

```bash
# Создание бэкапа базы данных
cp data/users.db data/users.db.backup.$(date +%Y%m%d_%H%M%S)

# Или автоматически через cron
# Добавить в crontab:
# 0 2 * * * /path/to/backup_script.sh
```

### Мониторинг ресурсов

```bash
# Просмотр использования ресурсов
docker stats vanya_tg_bot_prod

# Просмотр размера образов
docker images | grep vanya

# Очистка неиспользуемых ресурсов
docker system prune -a
```
