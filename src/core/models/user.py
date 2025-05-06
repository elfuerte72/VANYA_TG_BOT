"""
User model and related database schema.
"""

from sqlalchemy import BigInteger, Boolean, Column, DateTime, Float, Integer, String
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """
    Represents a user in the system with personal information and fitness data.
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    calculated = Column(Boolean, default=False)
    gender = Column(String)
    age = Column(Integer)
    height = Column(Integer)
    weight = Column(Float)
    activity_factor = Column(Float)
    calculated_at = Column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<User(telegram_id={self.telegram_id}, " f"calculated={self.calculated})>"
        )
