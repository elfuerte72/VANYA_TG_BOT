import asyncio
import os
import sqlite3
from typing import Any


class AsyncDBConnector:
    """Async wrapper for SQLite database operations"""

    def __init__(self, db_path: str):
        """
        Initialize with database path

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._connection = None

    async def _get_connection(self) -> sqlite3.Connection:
        """Get SQLite connection (create if not exists)"""
        if self._connection is None:
            # Use loop.run_in_executor for non-blocking operations
            loop = asyncio.get_event_loop()
            self._connection = await loop.run_in_executor(
                None, lambda: sqlite3.connect(self.db_path)
            )
            # Enable row factory for dict-like access
            self._connection.row_factory = sqlite3.Row

        return self._connection

    async def execute(self, query: str, *params) -> None:
        """
        Execute SQL query with parameters

        Args:
            query: SQL query with placeholders
            *params: Query parameters
        """
        conn = await self._get_connection()

        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, lambda: conn.execute(query, params).connection.commit()
        )

    async def fetch_one(self, query: str, *params) -> Any:
        """
        Fetch one record from database

        Args:
            query: SQL query with placeholders
            *params: Query parameters

        Returns:
            Optional[sqlite3.Row]: Record or None if not found
        """
        conn = await self._get_connection()

        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: conn.execute(query, params).fetchone()
        )

        return result

    async def fetch_all(self, query: str, *params) -> list:
        """
        Fetch all records from database

        Args:
            query: SQL query with placeholders
            *params: Query parameters

        Returns:
            List[sqlite3.Row]: List of records
        """
        conn = await self._get_connection()

        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: conn.execute(query, params).fetchall()
        )

        return result

    async def fetch_val(self, query: str, *params) -> Any:
        """
        Fetch single value from database

        Args:
            query: SQL query with placeholders
            *params: Query parameters

        Returns:
            Any: First column of first row or None
        """
        conn = await self._get_connection()

        # Run in executor to avoid blocking event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None, lambda: conn.execute(query, params).fetchone()
        )

        return result[0] if result else None

    async def close(self) -> None:
        """Close database connection if open"""
        if self._connection is not None:
            # Run in executor to avoid blocking event loop
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, lambda: self._connection.close())
            self._connection = None


async def get_db_connection() -> AsyncDBConnector:
    """
    Get database connection

    Returns:
        AsyncDBConnector: Database connector instance
    """
    # Get database path from environment variable or use default
    db_path = os.getenv("DB_PATH", "data/users.db")

    # Create database directory if it doesn't exist
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)

    # Initialize database connector
    db = AsyncDBConnector(db_path)

    # Create tables if they don't exist
    await _create_tables(db)

    return db


async def _create_tables(db: AsyncDBConnector) -> None:
    """Create database tables if they don't exist"""
    # User table
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE NOT NULL,
            calculated BOOLEAN DEFAULT FALSE,
            gender TEXT,
            age INTEGER,
            height INTEGER,
            weight REAL,
            activity_factor REAL,
            calculated_at TIMESTAMP,
            goal TEXT
        )
    """
    )
