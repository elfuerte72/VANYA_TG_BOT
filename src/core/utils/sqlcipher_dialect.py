"""
Модуль для регистрации диалекта SQLCipher в SQLAlchemy.
"""
from sqlalchemy.dialects import registry

# Регистрируем диалект SQLCipher
registry.register(
    "sqlite.pysqlcipher3", "sqlalchemy.dialects.sqlite.pysqlcipher", "dialect"
)
