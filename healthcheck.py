#!/usr/bin/env python3
"""
Health check script for Docker container
Проверяет, что основные компоненты бота работают
"""
import sys
import os
import sqlite3
from pathlib import Path

def check_database():
    """Проверка доступности базы данных"""
    try:
        db_path = os.getenv('DB_PATH', '/app/data/users.db')
        
        # Проверяем, существует ли файл БД или можем ли создать его
        db_dir = Path(db_path).parent
        if not db_dir.exists():
            print(f"❌ Директория БД не существует: {db_dir}")
            return False
            
        # Проверяем права на запись
        if not os.access(db_dir, os.W_OK):
            print(f"❌ Нет прав на запись в директорию БД: {db_dir}")
            return False
            
        print("✅ База данных доступна")
        return True
    except Exception as e:
        print(f"❌ Ошибка проверки БД: {e}")
        return False

def check_environment():
    """Проверка критических переменных окружения"""
    required_vars = ['BOT_TOKEN', 'OPENAI_API_KEY', 'DATABASE_SECRET_KEY']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"❌ Отсутствуют переменные окружения: {', '.join(missing)}")
        return False
    
    print("✅ Переменные окружения настроены")
    return True

def check_imports():
    """Проверка, что основные модули импортируются"""
    try:
        import aiogram
        import openai
        import sqlalchemy
        import cryptography
        print("✅ Основные модули импортируются")
        return True
    except ImportError as e:
        print(f"❌ Ошибка импорта модулей: {e}")
        return False

def main():
    """Основная функция health check"""
    print("🔍 Запуск health check...")
    
    checks = [
        check_imports,
        check_environment,
        check_database,
    ]
    
    all_passed = True
    for check in checks:
        if not check():
            all_passed = False
    
    if all_passed:
        print("✅ Все проверки прошли успешно")
        sys.exit(0)
    else:
        print("❌ Некоторые проверки не прошли")
        sys.exit(1)

if __name__ == "__main__":
    main()