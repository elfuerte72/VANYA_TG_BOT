#!/usr/bin/env python
"""
Демонстрационный скрипт для работы с шифрованием полей в модели пользователя.
Создает тестовых пользователей и показывает как данные хранятся в базе данных.
"""
import os
import sqlite3
from datetime import datetime

from sqlalchemy import select

from src.core.models.user import User
from src.core.services.database import DatabaseService


def print_header(title):
    """Print a section header."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print(f"{'=' * 50}")


def main():
    """Run the demo."""
    # Инициализация базы данных
    db_service = DatabaseService()
    db_service.initialize()

    # Получение сессии
    session = db_service.get_session()

    # Путь к базе данных
    db_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "data",
        "database.db",
    )

    print_header("Демонстрация шифрования полей в модели User")
    print(f"База данных: {db_path}")

    # Создаем тестового пользователя с конфиденциальными данными
    user = User(
        telegram_id=123456789,
        gender="Мужской",  # Это поле будет зашифровано
        age=30,
        height=180,
        weight=75.5,
        activity_factor=1.55,
        calculated=True,
        calculated_at=datetime.now(),
    )

    # Добавляем пользователя в базу данных
    session.add(user)
    session.commit()

    print(f"Создан пользователь с ID: {user.id}")

    # Получаем пользователя через ORM
    orm_user = session.execute(select(User).where(User.id == user.id)).scalar_one()

    print_header("Данные через ORM")
    print(f"ID: {orm_user.id}")
    print(f"Telegram ID: {orm_user.telegram_id}")
    print(f"Пол: {orm_user.gender}")  # Поле автоматически расшифровано
    print(f"Возраст: {orm_user.age}")
    print(f"Рост: {orm_user.height}")
    print(f"Вес: {orm_user.weight}")

    # Проверяем как данные хранятся напрямую в базе данных
    print_header("Данные напрямую из БД (SQLite)")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, telegram_id, gender, age, height, weight FROM users WHERE id = {user.id}"
    )
    row = cursor.fetchone()

    print(f"ID: {row[0]}")
    print(f"Telegram ID: {row[1]}")
    print(f"Пол (зашифрован): '{row[2]}'")  # Это зашифрованное значение
    print(f"Возраст: {row[3]}")
    print(f"Рост: {row[4]}")
    print(f"Вес: {row[5]}")

    # Проверяем, что зашифрованное поле действительно зашифровано
    is_encrypted = row[2] != "Мужской"

    print_header("Результат проверки")
    if is_encrypted:
        print("УСПЕХ: Поле 'gender' корректно зашифровано в базе данных.")
        print("Шифрование в модели User работает корректно.")
    else:
        print("ОШИБКА: Поле 'gender' не зашифровано в базе данных.")

    # Закрываем соединения
    conn.close()
    session.close()


if __name__ == "__main__":
    main()
