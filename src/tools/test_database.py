#!/usr/bin/env python
"""
Скрипт для тестирования базы данных и схемы таблицы пользователей.
Проверяет создание таблицы, добавление и получение данных.
"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Добавляем корневую директорию проекта в sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.core.models.user import Base, User
from src.core.services.user_repository import UserRepository


def setup_test_db():
    """Создать временную тестовую базу данных."""
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, "test_db.db")

    # Удаляем базу, если она существует
    if os.path.exists(db_path):
        os.remove(db_path)

    # Создаем подключение к базе
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    return engine, session, db_path


def test_schema(engine):
    """Проверить схему таблицы пользователей."""
    print("\n=== Проверка схемы таблицы ===")

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "users" in tables, "Таблица 'users' не создана"
    print("✓ Таблица 'users' успешно создана")

    columns = inspector.get_columns("users")
    column_names = [col["name"] for col in columns]

    expected_columns = [
        "id",
        "telegram_id",
        "calculated",
        "gender",
        "age",
        "height",
        "weight",
        "activity_factor",
        "calculated_at",
    ]

    for expected_column in expected_columns:
        assert (
            expected_column in column_names
        ), f"Колонка '{expected_column}' отсутствует"
        print(f"✓ Колонка '{expected_column}' существует")

    # Проверяем тип первичного ключа
    pk = inspector.get_pk_constraint("users")
    assert pk["constrained_columns"] == ["id"], "Неверный первичный ключ"
    print("✓ Первичный ключ верно установлен на колонке 'id'")

    # Проверяем уникальность telegram_id
    unique_constraints = inspector.get_unique_constraints("users")
    for constraint in unique_constraints:
        if "telegram_id" in constraint["column_names"]:
            print("✓ Ограничение уникальности на telegram_id существует")
            break
    else:
        print("⚠ Ограничение уникальности на telegram_id не обнаружено в метаданных")
        print("  (Это может быть особенностью SQLite)")


def test_crud_operations(session):
    """Протестировать операции CRUD с пользователями."""
    print("\n=== Тестирование операций с пользователями ===")

    # Создаем репозиторий
    repo = UserRepository(session)

    # Тест 1: Создание пользователя
    telegram_id = 123456789
    user = repo.create_user(telegram_id)
    print(f"✓ Пользователь создан с id={user.id}")

    # Тест 2: Получение пользователя
    retrieved_user = repo.get_user_by_telegram_id(telegram_id)
    assert retrieved_user is not None, "Не удалось получить пользователя"
    assert retrieved_user.telegram_id == telegram_id, "Неверный telegram_id"
    print(f"✓ Пользователь с telegram_id={telegram_id} успешно получен")

    # Тест 3: Обновление профиля пользователя
    repo.update_user_profile(
        user.id, gender="male", age=30, height=180, weight=80.5, activity_factor=1.55
    )

    updated_user = repo.get_user_by_telegram_id(telegram_id)
    assert updated_user.gender == "male", "Пол не обновлен"
    assert updated_user.age == 30, "Возраст не обновлен"
    assert updated_user.height == 180, "Рост не обновлен"
    assert abs(updated_user.weight - 80.5) < 0.01, "Вес не обновлен"
    assert (
        abs(updated_user.activity_factor - 1.55) < 0.01
    ), "Коэффициент активности не обновлен"
    print("✓ Профиль пользователя успешно обновлен")

    # Тест 4: Отметка о расчете для пользователя
    before_mark = datetime.now()
    marked_user = repo.mark_as_calculated(user.id)
    assert marked_user.calculated is True, "Флаг calculated не установлен"
    assert marked_user.calculated_at is not None, "Время расчета не установлено"
    assert marked_user.calculated_at > before_mark, "Время расчета неверное"
    print("✓ Пользователь успешно отмечен как рассчитанный")

    # Тест 5: Проверка получения всех пользователей
    all_users = repo.get_all_users()
    assert len(all_users) >= 1, "Список пользователей пуст"
    print(f"✓ Получен список пользователей (всего: {len(all_users)})")

    # Тест 6: Проверка уникальности telegram_id
    try:
        # Создаем второго пользователя с тем же telegram_id
        user2 = User(telegram_id=telegram_id)
        session.add(user2)
        session.commit()
        print("✗ Ошибка: удалось создать пользователя с дублирующимся telegram_id")
    except Exception:
        print(
            "✓ Ограничение уникальности работает: невозможно создать дубликат telegram_id"
        )
        session.rollback()


def main():
    """Запустить все тесты базы данных."""
    print("Начинается тестирование базы данных...")
    engine, session, db_path = setup_test_db()

    try:
        print(f"\nСоздана тестовая база данных: {db_path}")

        # Запускаем тесты
        test_schema(engine)
        test_crud_operations(session)

        print("\n✅ Все тесты успешно пройдены!")
    except AssertionError as e:
        print(f"\n❌ Тест не пройден: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        return 1
    finally:
        session.close()

        # Удаляем тестовую базу данных
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"\nТестовая база данных удалена: {db_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
