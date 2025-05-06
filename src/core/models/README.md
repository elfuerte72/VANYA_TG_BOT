# Database Models

This directory contains SQLAlchemy models that define the database schema for the application.

## User Model

The `User` model represents a Telegram user with their personal information and fitness data.

### Schema

```sql
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  telegram_id BIGINT UNIQUE NOT NULL,
  calculated BOOLEAN DEFAULT FALSE,
  gender TEXT,
  age INTEGER,
  height INTEGER,
  weight REAL,
  activity_factor REAL,
  calculated_at TIMESTAMP
);
```

### Fields

- `id`: Primary key for the user.
- `telegram_id`: Telegram user ID, unique for each user.
- `calculated`: Whether the user's nutrition has been calculated.
- `gender`: User's gender.
- `age`: User's age.
- `height`: User's height.
- `weight`: User's weight.
- `activity_factor`: User's activity factor for calorie calculations.
- `calculated_at`: Timestamp when the user's nutrition was calculated.

## Database Initialization

To initialize the database, run the following command:

```bash
python -m src.tools.initialize_db
```

This will create the database file in the `data` directory and create all tables.
