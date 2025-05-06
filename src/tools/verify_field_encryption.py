#!/usr/bin/env python
"""
Скрипт для проверки шифрования полей в базе данных.
Создает временную таблицу с зашифрованными полями и проверяет их шифрование.
"""
import argparse
import os
import sqlite3
import tempfile

from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from src.core.utils.encryption import EncryptedString

# Создаём базовый класс для тестовой модели
TestBase = declarative_base()


class TestModel(TestBase):
    """Тестовая модель для проверки шифрования полей."""

    __tablename__ = "encryption_test"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plain_text = Column(String(100), nullable=False)
    encrypted_text = Column(EncryptedString(100), nullable=False)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Verify encrypted fields in database")
    parser.add_argument(
        "--test-text",
        type=str,
        default="Секретный текст для проверки шифрования",
        help="Text to test encryption",
    )
    return parser.parse_args()


def main():
    """Run field encryption verification."""
    args = parse_args()

    # Создаем временную базу данных для тестирования
    temp_db_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
    db_url = f"sqlite:///{temp_db_file}"

    print(f"Создаем временную тестовую базу данных: {temp_db_file}")

    # Создаем движок и таблицы
    engine = create_engine(db_url)
    TestBase.metadata.create_all(engine)

    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()

    # Создаем тестовую запись
    test_text = args.test_text
    test_record = TestModel(plain_text=test_text, encrypted_text=test_text)

    session.add(test_record)
    session.commit()

    print(f"Создана тестовая запись с текстом: '{test_text}'")

    # Проверяем, что данные сохранены и могут быть прочитаны через ORM
    record = session.execute(
        select(TestModel).where(TestModel.id == test_record.id)
    ).scalar_one()

    print("\nПроверка через ORM SQLAlchemy:")
    print(f"ID: {record.id}")
    print(f"Обычный текст: '{record.plain_text}'")
    print(f"Расшифрованный текст: '{record.encrypted_text}'")

    # Закрываем сессию
    session.close()

    # Проверяем данные напрямую из SQLite
    print("\nПроверка содержимого базы данных напрямую через SQLite:")

    conn = sqlite3.connect(temp_db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT id, plain_text, encrypted_text FROM encryption_test")
    row = cursor.fetchone()

    print(f"ID: {row[0]}")
    print(f"Обычный текст: '{row[1]}'")
    print(f"Зашифрованный текст (в БД): '{row[2]}'")

    # Проверяем, что зашифрованный текст не совпадает с оригиналом
    is_encrypted = row[2] != test_text

    if is_encrypted:
        print("\nУСПЕХ: Данные корректно зашифрованы в базе данных.")
        print("Шифрование полей с типом EncryptedString работает корректно.")
    else:
        print("\nОШИБКА: Данные не зашифрованы в базе данных.")
        print("Шифрование полей с типом EncryptedString не работает.")

    # Закрываем соединение и удаляем временную базу
    conn.close()
    os.unlink(temp_db_file)


if __name__ == "__main__":
    main()
