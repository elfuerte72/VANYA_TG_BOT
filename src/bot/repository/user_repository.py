from datetime import datetime
from typing import Any, Dict, Optional


class UserRepository:
    """Repository for user data storage and retrieval"""

    def __init__(self, db_connector):
        """Initialize with db connector"""
        self.db = db_connector

    async def get_user(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """
        Get user data by telegram_id

        Args:
            telegram_id: Telegram user ID

        Returns:
            Optional[Dict]: User data or None if not found
        """
        # This is a placeholder - actual implementation depends on DB
        query = "SELECT * FROM users WHERE telegram_id = ?"
        result = await self.db.fetch_one(query, telegram_id)
        return dict(result) if result else None

    async def user_exists(self, telegram_id: int) -> bool:
        """Check if user exists in database"""
        query = "SELECT EXISTS(SELECT 1 FROM users WHERE telegram_id = ?)"
        result = await self.db.fetch_val(query, telegram_id)
        return bool(result)

    async def is_calculated(self, telegram_id: int) -> bool:
        """Check if user has already calculated KBJU"""
        query = """
            SELECT calculated
            FROM users
            WHERE telegram_id = ?
        """
        result = await self.db.fetch_val(query, telegram_id)
        return bool(result)

    async def create_user(self, telegram_id: int) -> None:
        """Create new user record"""
        query = """
            INSERT INTO users (telegram_id, calculated)
            VALUES (?, ?)
        """
        await self.db.execute(query, telegram_id, False)

    async def update_user_data(self, telegram_id: int, data: Dict[str, Any]) -> None:
        """
        Update user data

        Args:
            telegram_id: Telegram user ID
            data: Dictionary with user data to update
        """
        # Building the SET part of the query dynamically
        set_fields = []
        params = []

        for key, value in data.items():
            set_fields.append(f"{key} = ?")
            params.append(value)

        # Add telegram_id to params
        params.append(telegram_id)

        query = f"""
            UPDATE users
            SET {', '.join(set_fields)}
            WHERE telegram_id = ?
        """

        await self.db.execute(query, *params)

    async def mark_calculated(self, telegram_id: int) -> None:
        """Mark user as having calculated KBJU"""
        query = """
            UPDATE users
            SET calculated = ?, calculated_at = ?
            WHERE telegram_id = ?
        """
        now = datetime.now()
        await self.db.execute(query, True, now, telegram_id)
