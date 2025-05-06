"""
Repository for user database operations.
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.core.models.user import User


class UserRepository:
    """
    Repository for user database operations.
    """

    def __init__(self, session: Session):
        """
        Initialize the repository with a database session.

        Args:
            session: SQLAlchemy session for database operations.
        """
        self.session = session

    def create_user(self, telegram_id: int) -> User:
        """
        Create a new user.

        Args:
            telegram_id: Telegram user ID.

        Returns:
            Created user.
        """
        user = User(telegram_id=telegram_id)
        self.session.add(user)
        self.session.commit()
        return user

    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """
        Get a user by Telegram ID.

        Args:
            telegram_id: Telegram user ID.

        Returns:
            User if found, None otherwise.
        """
        return self.session.query(User).filter(User.telegram_id == telegram_id).first()

    def get_all_users(self) -> List[User]:
        """
        Get all users.

        Returns:
            List of all users.
        """
        return self.session.query(User).all()

    def update_user_profile(
        self,
        user_id: int,
        gender: Optional[str] = None,
        age: Optional[int] = None,
        height: Optional[int] = None,
        weight: Optional[float] = None,
        activity_factor: Optional[float] = None,
    ) -> Optional[User]:
        """
        Update user profile information.

        Args:
            user_id: User ID.
            gender: User gender.
            age: User age.
            height: User height.
            weight: User weight.
            activity_factor: User activity factor.

        Returns:
            Updated user if found, None otherwise.
        """
        user = self.session.query(User).filter(User.id == user_id).first()
        if user is None:
            return None

        if gender is not None:
            user.gender = gender
        if age is not None:
            user.age = age
        if height is not None:
            user.height = height
        if weight is not None:
            user.weight = weight
        if activity_factor is not None:
            user.activity_factor = activity_factor

        self.session.commit()
        return user

    def mark_as_calculated(self, user_id: int) -> Optional[User]:
        """
        Mark a user as having their nutrition calculated.

        Args:
            user_id: User ID.

        Returns:
            Updated user if found, None otherwise.
        """
        user = self.session.query(User).filter(User.id == user_id).first()
        if user is None:
            return None

        user.calculated = True
        user.calculated_at = datetime.now()
        self.session.commit()
        return user
