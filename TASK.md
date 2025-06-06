## Задачи для разработки Telegram-бота расчёта КБЖУ

Ниже приведён подробный список задач, разбитых по этапам и модулям. Каждая задача — самостоятельная единица работы для разработчика.

---

### 1. Подготовительный этап

1.1. **Инициализация репозитория и окружения**
- [x] Создать Git-репозиторий.
- [x] Настроить менеджер пакетов (Poetry/PDM) и файл `pyproject.toml`.
- [x] Добавить `.gitignore` для исключения виртуальных окружений, логов, файла базы данных.

1.2. **Конфигурация окружения**
- [x] Создать шаблон `.env.example` с полями: `BOT_TOKEN`, `OPENAI_API_KEY`, `DB_PATH`, `LOG_LEVEL`.
- [x] Настроить загрузку переменных из `.env` через `python-dotenv`.

1.3. **Установка зависимостей**
- [x] Установить библиотеку `aiogram` для работы с Telegram API.
- [x] Установить `openai` для интеграции с OpenAI API.
- [x] Установить необходимые дополнительные пакеты (`pytest`, `sqlalchemy` и др.).

1.4. **Структура проекта**
- [x] Спроектировать файловую структуру:
  - [x] `src/bot/` — модули бота (handlers, services, utils).
  - [x] `data/` — файл базы данных `users.db`.
  - [x] `tests/` — тесты.
  - [x] `logs/` — файлы логов.
  - [x] `config/` — конфигурационные файлы.

---

### 2. Проектирование и архитектура

2.1. **Определение слоёв приложения**
- [x] `handlers/` — обработчики команд и сообщений.
- [x] `services/` — бизнес-логика (проверка подписки, расчёт КБЖУ, генерация плана).
- [x] `repository/` — доступ к БД (CRUD для пользователей).
- [x] `utils/` — вспомогательные функции (валидация, конвертации).
- [x] `core/` — общие настройки (логирование, подключение к Telegram API и OpenAI API).

2.2. **Интеграция с OpenAI API**
- [x] Создать класс для работы с OpenAI API (ChatGPT 4.1 nano).
- [x] Реализовать обработку ошибок при запросах к API.
- [x] Создать механизм кэширования ответов для экономии запросов.

2.3. **Схема БД**
- [x] Таблица `users`:
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `telegram_id` BIGINT UNIQUE NOT NULL
  - `calculated` BOOLEAN DEFAULT FALSE
  - `gender` TEXT
  - `age` INTEGER
  - `height` INTEGER
  - `weight` REAL
  - `activity_factor` REAL
  - `calculated_at` TIMESTAMP
- [x] Убедиться в шифровании файла БД (использовать SQLCipher или аналог).

2.4. **Диаграмма состояний диалога**
- [x] START → CHECK_SUBSCRIPTION → STATE: `await_gender` → `await_age` → `await_height` → `await_weight` → `await_activity` → CONFIRMATION → CALCULATION → FINISH.
- [x] Определить состояния Finite State Machine (aiogram FSM).

---

### 3. Реализация функциональности бота

#### 3.1 Проверка доступа

3.1.1. **Метод проверки подписки**
- [x] Реализовать вызов Telegram API для проверки, состоит ли пользователь в заданном канале.
- [x] Обработать возможные ошибки (бот не администратор, приватный канал).

3.1.2. **Логика отказа**
- [x] При неуспешной проверке отправлять сообщение с инструкцией подписаться.
- [x] Блокировать дальнейшие сообщения до подтверждения подписки.

#### 3.2 Процедура единожды расчёта

3.2.1. **Фиксация флага расчёта**
- [x] После первого расчёта устанавливать `calculated = true` и записывать `calculated_at` (текущая дата/время).
- [x] При последующих обращениях проверять этот флаг и отправлять сообщение: «Вы уже получили расчёт КБЖУ».

3.2.2. **Обновление модели**
- [x] При изменении параметров до расчёта сохранять их в БД временно.

#### 3.3 Диалоговый сценарий и сбор параметров

3.3.1. **Команда `/start`**
- [x] Реализовать хэндлер для запуска FSM.
- [x] Кнопка "▶️ Запустить расчёт" для интерактивного старта.

3.3.2. **Сбор данных**
- [x] Хэндлеры для каждого параметра:
  - Пол (кнопки: «Мужской», «Женский»)
  - Возраст (числовой ввод, полных лет)
  - Рост (числовой ввод, см)
  - Вес (числовой ввод, кг)
  - Уровень активности (кнопки: «Низкий», «Средний», «Высокий»)
- [x] Валидация введённых значений:
  - Возраст: допустимый диапазон 12-100 лет
  - Рост: допустимый диапазон 100-250 см
  - Вес: допустимый диапазон 30-300 кг
- [x] При пропуске выбора активности автоматически использовать значение 1.55 (Средний).

3.3.3. **Подтверждение данных**
- [x] Отправить сводную карточку с введёнными параметрами.
- [x] Кнопки «Изменить» (возврат к нужному шагу) и «Подтвердить».

#### 3.4 Реализация алгоритма расчёта

3.4.1. **Функция расчёта BMR**
- [x] Вынести в `services/calculation.py` функции по формуле Бенедикта:
  - `calc_bmr_male(weight, height, age)`: BMR = 66.47 + 13.75 × вес(кг) + 5.0 × рост(см) – 6.76 × возраст(лет)
  - `calc_bmr_female(weight, height, age)`: BMR = 655.1 + 9.56 × вес(кг) + 1.85 × рост(см) – 4.68 × возраст(лет)

3.4.2. **Учет активности**
- [x] Применить коэффициент активности:
  - Низкий — 1.2
  - Средний — 1.55
  - Высокий — 1.725
- [x] Значение по умолчанию — 1.55.

3.4.3. **Распределение приёмов пищи**
- [x] В зависимости от `calories`:
  - `< 2000` — 3 приёма.
  - `>= 2000` — 4 приёма.

3.4.4. **Расчёт макронутриентов**
- [x] Доли макро (пока статично):
  - Белки 20% калорий → граммы: `calories * 0.20 / 4`.
  - Жиры 25% калорий → граммы: `calories * 0.25 / 9`.
  - Углеводы 55% калорий → граммы: `calories * 0.55 / 4`.

#### 3.5 Формирование и отправка результата

3.5.1. **Шаблон сообщения**
- [x] Использовать MarkdownV2 или HTML для форматирования.
- [x] Включить секцию:
  - **Ккал/сутки:** `XXXXX`
  - **Белки:** `XX г` и т. д.

3.5.2. **План питания**
- [x] Разбивка КБЖУ по приёмам с динамическими кнопками или без.
- [x] Примерную таблицу цифр без конкретных продуктов.

3.5.3. **Опциональный комментарий**
- [x] Шаблон для целей похудения/набор массы.
- [x] Возможность расширения в будущем.

---

### 4. Нефункциональные задачи

4.1. **Логирование**
- [x] Настроить `logging` в `core/logger.py`.
- [x] Логи в файл `logs/bot.log` с ротацией (TimteRotatingFileHandler).
- [x] Логировать ошибки, входящие данные, ключевые шаги.

4.2. **Обработка ошибок и устойчивость**
- [ ] Глобальный хэндлер исключений (aiogram `on_error`).
- [ ] Игнорирование повторных запросов от одного юзера при активном FSM.

4.3. **Безопасность**
- [ ] Хранение токенов только в окружении.
- [ ] Шифрование SQLite (SQLCipher) или альтернативное решение.

4.4. **Производительность**
- [ ] Не более 3 сек отклика на любой запрос.
- [ ] Кеширование результатов расчёта для быстрого чтения.

---

### 5. Тестирование и CI/CD

5.1. **Модульные тесты**
- [ ] Тесты для функций расчёта BMR и макродолей.
- [ ] Тесты для FSM-состояний и хэндлеров (pytest + aiogram тестовые утилиты).

5.2. **Интеграционные тесты**
- [ ] Проверка полного сценария `/start` → расчёт → повторный запрос.

5.3. **Настройка CI**
- [ ] GitHub Actions:
  - `lint` (flake8/isort).
  - `test` (pytest).
  - `build` (проверка сборки Poetry).

5.4. **Code Review**
- [ ] Настроить правила ветвления: `main`, `develop`, `feature/*`.
- [ ] Pull Request шаблон с чек-листом.

---

### 6. Деплой и мониторинг

6.1. **Подготовка контейнера**
- [ ] Dockerfile для бота.
- [ ] docker-compose с сервисом `bot` и volume для БД.

6.2. **Развёртывание**
- [ ] Выкатка на VPS или Kubernetes (по согласованию).
- [ ] Настройка systemd / Deployment манифестов.

6.3. **Мониторинг и алерты**
- [ ] Простая проверка статуса (`healthcheck`) раз в минуту.
- [ ] Логи в централизованную систему (опционально).
- [ ] Уведомление в Telegram администратора при падении.

---

## Дополнительная информация о проекте

### Цель проекта
Разработать Telegram‑бота, который единожды для каждого подписчика фитнес‑канала рассчитывает персональные показатели КБЖУ.

### Технологический стек
- **Язык:** Python 3.x
- **Telegram‑бот:** aiogram
- **AI‑сервис:** OpenAI ChatGPT 4.1 nano через OpenAI API
- **Хранилище:** SQLite с шифрованием

### Нефункциональные требования
- **Время отклика:** ≤ 3 секунд на любой запрос.
- **Надёжность:** устойчивость к «бомбардировкам» запросами.

### Планы на будущее
- Порог 2000 ккал и макродоли могут быть изменены в будущих версиях.
- В планах адаптация под аллергенность и предпочтения.
- Соблюдение GDPR при расширении функционала.

---

*Конец списка задач — можете распределять между командой и оценивать время выполнения.*

### Инструкция по отметке задач

Когда задача выполнена, замените `[ ]` на `[x]` в соответствующем пункте. Например:

- [x] Задача выполнена
- [ ] Задача еще не выполнена

### Правила разработки

1. Следуйте принципам чистого кода из файла `rules/clean-code.mdc`.
2. Добавляйте комментарии к неочевидным частям кода на русском языке.
3. Создавайте модульные тесты для ключевых функций.
4. Для работы с ветками используйте схему: `main`, `develop`, `feature/*`.
5. При создании Pull Request требуйте код-ревью.
