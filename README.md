# Telegram-бот расчёта КБЖУ

Бот для расчета персональных показателей КБЖУ (калории, белки, жиры, углеводы) на основе пользовательских данных.

## Функциональность

- Проверка подписки пользователя на канал
- Сбор данных через диалог (пол, возраст, рост, вес, уровень активности)
- Расчет КБЖУ по формуле Харриса-Бенедикта
- Распределение по приемам пищи
- Сохранение данных пользователя в базе данных
- Однократный расчет для каждого пользователя

## Установка

### Предварительные требования

- Python 3.10 или выше
- Poetry (менеджер пакетов)

### Установка зависимостей

1. Клонировать репозиторий:
```bash
git clone <ссылка на репозиторий>
cd vanyba_telegramm
```

2. Установить зависимости с помощью Poetry:
```bash
poetry install
```

3. Создать файл `.env` с необходимыми переменными окружения:
```
BOT_TOKEN=ваш_токен_бота
DB_PATH=./data/users.db
LOG_LEVEL=INFO
```

## Запуск

Для запуска бота используйте:

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

```bash
poetry run pytest
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
