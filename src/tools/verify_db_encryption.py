#!/usr/bin/env python
"""
Скрипт для проверки шифрования базы данных SQLCipher.
Проверяет, что файл базы данных зашифрован и его нельзя открыть обычным
SQLite без пароля.
"""
import argparse
import os
import sqlite3
import sys
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.event import listen

# Импортируем модуль для регистрации диалекта SQLCipher
import src.core.utils.sqlcipher_dialect  # noqa
from src.config.settings import DATABASE_SECRET_KEY


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Verify database encryption")
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path("data") / "database.db"),
        help="Path to the database file",
    )
    parser.add_argument(
        "--secret-key",
        type=str,
        default=DATABASE_SECRET_KEY,
        help="Secret key for database encryption",
    )
    return parser.parse_args()


def check_regular_sqlite(db_path):
    """Try to open the database with regular SQLite."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master")
        tables = cursor.fetchall()
        conn.close()
        return True, tables
    except Exception as e:
        return False, str(e)


def check_sqlcipher(db_path, secret_key):
    """Try to open the database with SQLCipher."""
    try:
        # Create the database engine with SQLCipher
        db_url = f"sqlite+pysqlcipher3://:{secret_key}@/{db_path}"
        engine = create_engine(db_url)

        # Настраиваем шифрование для соединения
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute(f"PRAGMA key='{secret_key}'")
            cursor.close()

        listen(engine, "connect", set_sqlite_pragma)

        with engine.connect() as conn:
            result = conn.execute(text("SELECT name FROM sqlite_master"))
            tables = result.fetchall()
        return True, tables
    except Exception as e:
        return False, str(e)


def main():
    """Verify database encryption."""
    args = parse_args()

    if not os.path.exists(args.db_path):
        print(f"Ошибка: База данных не найдена по пути {args.db_path}")
        sys.exit(1)

    print(f"Проверка базы данных: {args.db_path}")

    # Проверка открытия обычным SQLite
    success, result = check_regular_sqlite(args.db_path)
    if success:
        print("ВНИМАНИЕ: База данных может быть открыта обычным SQLite!")
        print(f"Найденные таблицы: {result}")
        print("База данных НЕ зашифрована или ключ шифрования отсутствует.")
    else:
        print("OK: База данных не может быть открыта обычным SQLite.")
        print(f"Ошибка доступа: {result}")
        print("Это признак того, что база данных зашифрована.")

    # Проверка открытия с SQLCipher и паролем
    print("\nПроверка доступа с SQLCipher и паролем...")
    success, result = check_sqlcipher(args.db_path, args.secret_key)
    if success:
        print("OK: База данных успешно открыта с SQLCipher и ключом.")
        print(f"Найденные таблицы: {result}")
        print("Шифрование базы данных работает корректно.")
    else:
        print("ОШИБКА: Не удалось открыть базу данных с SQLCipher.")
        print(f"Ошибка: {result}")
        print("Возможно, указан неверный ключ или база повреждена.")


if __name__ == "__main__":
    main()
