#!/usr/bin/env python
"""
Script to initialize the database and create all tables.
"""
import argparse
import os
from pathlib import Path

from sqlalchemy import create_engine

from src.core.models.user import Base


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Initialize database tables")
    parser.add_argument(
        "--db-path",
        type=str,
        default=str(Path("data") / "database.db"),
        help="Path to the database file",
    )
    return parser.parse_args()


def main():
    """Initialize the database."""
    args = parse_args()

    # Ensure the directory exists
    os.makedirs(os.path.dirname(args.db_path), exist_ok=True)

    # Create the database engine with SQLite
    db_url = f"sqlite:///{args.db_path}"
    engine = create_engine(db_url)

    # Create all tables
    Base.metadata.create_all(engine)

    print(f"Database initialized at: {args.db_path}")
    print("Tables created:")
    for table in Base.metadata.tables:
        print(f"- {table}")
    print("Поля типа EncryptedString будут автоматически")
    print("шифроваться в базе данных.")


if __name__ == "__main__":
    main()
