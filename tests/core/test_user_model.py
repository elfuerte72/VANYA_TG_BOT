"""
Tests for User model and database functionality.
"""
import os
import tempfile
import uuid
from datetime import datetime

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from src.core.models.user import Base, User
from src.core.services.user_repository import UserProfileUpdate, UserRepository


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    temp_dir = tempfile.gettempdir()
    temp_file = os.path.join(temp_dir, f"test_db_{uuid.uuid4()}.db")
    yield temp_file
    if os.path.exists(temp_file):
        os.remove(temp_file)


@pytest.fixture
def db_engine(temp_db_path):
    """Create a test database engine."""
    db_url = f"sqlite:///{temp_db_path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)


@pytest.fixture
def db_session(db_engine):
    """Create a test database session."""
    Session = sessionmaker(bind=db_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def user_repository(db_session):
    """Create a user repository for testing."""
    return UserRepository(db_session)


def test_create_user(user_repository):
    """Test creating a user."""
    telegram_id = 12345678
    user = user_repository.create_user(telegram_id)

    assert user is not None
    assert user.telegram_id == telegram_id
    assert user.calculated is False
    assert user.id is not None


def test_get_user_by_telegram_id(user_repository):
    """Test getting a user by Telegram ID."""
    telegram_id = 98765432
    user_repository.create_user(telegram_id)

    user = user_repository.get_user_by_telegram_id(telegram_id)

    assert user is not None
    assert user.telegram_id == telegram_id


def test_update_user_profile(user_repository):
    """Test updating a user's profile."""
    telegram_id = 11112222
    user = user_repository.create_user(telegram_id)

    update_data = UserProfileUpdate(
        gender="male",
        age=30,
        height=180,
        weight=75.5,
        activity_factor=1.55,
    )
    updated_user = user_repository.update_user_profile(user.id, update_data)

    assert updated_user is not None
    assert updated_user.gender == "male"
    assert updated_user.age == 30
    assert updated_user.height == 180
    assert updated_user.weight == 75.5
    assert updated_user.activity_factor == 1.55
    assert updated_user.calculated is False


def test_update_user_profile_legacy(user_repository):
    """Test updating a user's profile using legacy method."""
    telegram_id = 22223333
    user = user_repository.create_user(telegram_id)

    updated_user = user_repository.update_user_profile_legacy(
        user.id,
        gender="female",
        age=25,
        height=165,
        weight=55.0,
        activity_factor=1.2,
    )

    assert updated_user is not None
    assert updated_user.gender == "female"
    assert updated_user.age == 25
    assert updated_user.height == 165
    assert updated_user.weight == 55.0
    assert updated_user.activity_factor == 1.2
    assert updated_user.calculated is False


def test_mark_as_calculated(user_repository):
    """Test marking a user as calculated."""
    telegram_id = 33334444
    user = user_repository.create_user(telegram_id)

    before_calculation = datetime.now()
    updated_user = user_repository.mark_as_calculated(user.id)

    assert updated_user is not None
    assert updated_user.calculated is True
    assert updated_user.calculated_at is not None
    assert updated_user.calculated_at > before_calculation


def test_get_all_users(user_repository):
    """Test getting all users."""
    # Create several users
    telegram_ids = [111, 222, 333]
    for telegram_id in telegram_ids:
        user_repository.create_user(telegram_id)

    users = user_repository.get_all_users()

    assert len(users) >= len(telegram_ids)
    assert all(user.id is not None for user in users)


def test_user_unique_constraint(db_session):
    """Test unique constraint on telegram_id."""
    telegram_id = 55556666

    # Create a user
    user1 = User(telegram_id=telegram_id)
    db_session.add(user1)
    db_session.commit()

    # Try to create another user with the same telegram_id
    user2 = User(telegram_id=telegram_id)
    db_session.add(user2)

    # Expect an IntegrityError because of the unique constraint
    with pytest.raises(Exception) as exc_info:
        db_session.commit()

    # Make sure the exception is related to integrity error
    error_msg = str(exc_info.value)
    assert "UNIQUE constraint failed" in error_msg or "IntegrityError" in error_msg

    # Rollback the failed transaction
    db_session.rollback()


def test_table_schema(db_engine):
    """Test the table schema."""
    # Get the table definition from SQLAlchemy
    inspector = inspect(db_engine)
    columns = inspector.get_columns("users")

    # Check column names
    column_names = [col["name"] for col in columns]
    expected_columns = [
        "id",
        "telegram_id",
        "calculated",
        "gender",
        "age",
        "height",
        "weight",
        "activity_factor",
        "calculated_at",
    ]

    for expected_column in expected_columns:
        assert expected_column in column_names

    # Check column types
    column_map = {col["name"]: col for col in columns}

    assert "INTEGER" in str(column_map["id"]["type"]).upper()
    assert "INT" in str(column_map["telegram_id"]["type"]).upper()
    assert (
        "BOOL" in str(column_map["calculated"]["type"]).upper()
        or "INT" in str(column_map["calculated"]["type"]).upper()
    )
    assert (
        "VARCHAR" in str(column_map["gender"]["type"]).upper()
        or "TEXT" in str(column_map["gender"]["type"]).upper()
    )
    assert "INT" in str(column_map["age"]["type"]).upper()
    assert "INT" in str(column_map["height"]["type"]).upper()
    assert (
        "REAL" in str(column_map["weight"]["type"]).upper()
        or "FLOAT" in str(column_map["weight"]["type"]).upper()
    )
    assert (
        "REAL" in str(column_map["activity_factor"]["type"]).upper()
        or "FLOAT" in str(column_map["activity_factor"]["type"]).upper()
    )


if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main(["-v", __file__]))
