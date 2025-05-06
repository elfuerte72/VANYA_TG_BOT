"""
User model and related database schema.
"""

from typing import Any

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer
from sqlalchemy.ext.declarative import declarative_base

from src.core.utils.encryption import EncryptedString

Base = declarative_base()


class User(Base):
    """
    Represents a user in the system with personal information and fitness data.
    """

    __tablename__ = "users"

    id: Any = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Any = Column(BigInteger, unique=True, nullable=False)
    calculated: Any = Column(Boolean, default=False)
    gender: Any = Column(EncryptedString(10))
    age: Any = Column(Integer)
    height: Any = Column(Integer)
    weight: Any = Column(Float)
    activity_factor: Any = Column(Float)
    calculated_at: Any = Column(DateTime)
    goal: Any = Column(EncryptedString(20))

    def __repr__(self) -> str:
        return (
            f"<User(telegram_id={self.telegram_id}, " f"calculated={self.calculated})>"
        )
