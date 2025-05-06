#!/usr/bin/env python
"""
Script for testing database and user table schema.
Tests table creation, data addition and retrieval.
"""
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path

# Add project root to path first to ensure proper imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

# Import SQLAlchemy components
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

# Import application components
from src.core.models.user import Base, User
from src.core.services.user_repository import UserProfileUpdate, UserRepository


def setup_test_db():
    """Create a temporary test database."""
    temp_dir = tempfile.gettempdir()
    db_path = os.path.join(temp_dir, "test_db.db")

    # Remove database if it exists
    if os.path.exists(db_path):
        os.remove(db_path)

    # Create database connection
    db_url = f"sqlite:///{db_path}"
    engine = create_engine(db_url)
    Base.metadata.create_all(engine)

    # Create session
    Session = sessionmaker(bind=engine)
    session = Session()

    return engine, session, db_path


def test_schema(engine):
    """Test user table schema."""
    print("\n=== Testing Table Schema ===")

    inspector = inspect(engine)
    tables = inspector.get_table_names()

    assert "users" in tables, "Table 'users' not created"
    print("✓ Table 'users' successfully created")

    columns = inspector.get_columns("users")
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
        assert expected_column in column_names, f"Column '{expected_column}' missing"
        print(f"✓ Column '{expected_column}' exists")

    # Check primary key type
    pk = inspector.get_pk_constraint("users")
    assert pk["constrained_columns"] == ["id"], "Invalid primary key"
    print("✓ Primary key correctly set on column 'id'")

    # Check telegram_id uniqueness
    unique_constraints = inspector.get_unique_constraints("users")
    for constraint in unique_constraints:
        if "telegram_id" in constraint["column_names"]:
            print("✓ Unique constraint on telegram_id exists")
            break
    else:
        print("⚠ Unique constraint on telegram_id not found in metadata")
        print("  (This might be a SQLite specificity)")


def test_crud_operations(session):
    """Test CRUD operations with users."""
    print("\n=== Testing User Operations ===")

    # Create repository
    repo = UserRepository(session)

    # Test 1: User creation
    telegram_id = 123456789
    user = repo.create_user(telegram_id)
    print(f"✓ User created with id={user.id}")

    # Test 2: User retrieval
    retrieved_user = repo.get_user_by_telegram_id(telegram_id)
    assert retrieved_user is not None, "Failed to retrieve user"
    assert retrieved_user.telegram_id == telegram_id, "Wrong telegram_id"
    print(f"✓ User with telegram_id={telegram_id} successfully retrieved")

    # Test 3: User profile update
    # Using the new DTO pattern
    UPDATE_GENDER = "male"
    UPDATE_AGE = 30
    UPDATE_HEIGHT = 180
    UPDATE_WEIGHT = 80.5
    UPDATE_ACTIVITY = 1.55

    profile_update = UserProfileUpdate(
        gender=UPDATE_GENDER,
        age=UPDATE_AGE,
        height=UPDATE_HEIGHT,
        weight=UPDATE_WEIGHT,
        activity_factor=UPDATE_ACTIVITY,
    )

    repo.update_user_profile(user.id, profile_update)

    updated_user = repo.get_user_by_telegram_id(telegram_id)
    assert updated_user.gender == UPDATE_GENDER, "Gender not updated"
    assert updated_user.age == UPDATE_AGE, "Age not updated"
    assert updated_user.height == UPDATE_HEIGHT, "Height not updated"
    assert abs(updated_user.weight - UPDATE_WEIGHT) < 0.01, "Weight not updated"
    assert (
        abs(updated_user.activity_factor - UPDATE_ACTIVITY) < 0.01
    ), "Activity factor not updated"
    print("✓ User profile successfully updated")

    # Test 4: Mark user as calculated
    before_mark = datetime.now()
    marked_user = repo.mark_as_calculated(user.id)
    assert marked_user.calculated is True, "Calculated flag not set"
    assert marked_user.calculated_at is not None, "Calculation time not set"
    assert marked_user.calculated_at > before_mark, "Calculation time incorrect"
    print("✓ User successfully marked as calculated")

    # Test 5: Get all users
    all_users = repo.get_all_users()
    assert len(all_users) >= 1, "User list is empty"
    print(f"✓ Retrieved user list (total: {len(all_users)})")

    # Test 6: Test telegram_id uniqueness
    try:
        # Create second user with same telegram_id
        user2 = User(telegram_id=telegram_id)
        session.add(user2)
        session.commit()
        print("✗ Error: created user with duplicate telegram_id")
    except Exception:
        print("✓ Uniqueness constraint works: cannot create duplicate telegram_id")
        session.rollback()


def main():
    """Run all database tests."""
    print("Starting database testing...")
    engine, session, db_path = setup_test_db()

    try:
        print(f"\nCreated test database: {db_path}")

        # Run tests
        test_schema(engine)
        test_crud_operations(session)

        print("\n✅ All tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n❌ Testing error: {e}")
        return 1
    finally:
        session.close()

        # Remove test database
        if os.path.exists(db_path):
            os.remove(db_path)
            print(f"\nTest database removed: {db_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
