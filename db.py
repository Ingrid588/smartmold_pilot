"""
SmartMold Pilot V3 - Database Connection & Initialization
Handles SQLite setup, migrations, and async connection lifecycle.
"""

import os
from pathlib import Path
from tortoise import Tortoise


# Database configuration
DB_PATH = Path(__file__).parent / "smartmold.db"
TORTOISE_ORM_CONFIG = {
    "connections": {
        "default": {
            "engine": "tortoise.backends.sqlite",
            "credentials": {
                "file_path": str(DB_PATH),
                "journal_mode": "wal",  # Write-Ahead Logging for better concurrency
            },
        }
    },
    "apps": {
        "models": {
            "models": ["models"],
            "default_connection": "default",
        }
    },
}


async def init_db():
    """
    Initialize Tortoise ORM and create database tables.
    Call this once at application startup.
    """
    print(f"[DB] Initializing database at {DB_PATH}...")
    
    await Tortoise.init(config=TORTOISE_ORM_CONFIG)
    print("[DB] Tortoise initialized.")
    
    # Create tables
    await Tortoise.generate_schemas()
    print("[DB] Database schemas created/verified.")


async def close_db():
    """
    Close database connections gracefully.
    Call this at application shutdown.
    """
    print("[DB] Closing database connections...")
    await Tortoise.close_connections()
    print("[DB] Database closed.")


def get_db_path():
    """Return the database file path."""
    return str(DB_PATH)


def get_db_exists():
    """Check if database file exists."""
    return DB_PATH.exists()
