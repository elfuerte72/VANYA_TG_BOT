"""
Database service for managing database connections and operations.
"""
import os
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from src.core.models.user import Base


class DatabaseService:
    """
    Service for managing database connections and operations.
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the database service.

        Args:
            db_path: Path to the database file. If None, a default path is used.
        """
        if db_path is None:
            # Default path to the database file
            db_path = str(Path("data") / "database.db")

        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Create database URL
        # Используем SQLite. Данные будут шифроваться внутри EncryptedString
        self.db_url = f"sqlite:///{db_path}"
        self.engine: Optional[Engine] = None
        self.session_factory = None

    def initialize(self) -> None:
        """
        Initialize the database, creating tables if they don't exist.
        """
        self.engine = create_engine(self.db_url)
        Base.metadata.create_all(self.engine)
        self.session_factory = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """
        Get a new database session.

        Returns:
            SQLAlchemy session for database operations.
        """
        if self.session_factory is None:
            self.initialize()
        assert self.session_factory is not None
        return self.session_factory()
