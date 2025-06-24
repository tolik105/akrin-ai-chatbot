"""
Database factory to switch between SQLite and PostgreSQL
"""

import os
from typing import Union

from src.core.sqlite_db import SQLiteDatabase, get_sqlite_db
from src.core.postgres_db import PostgresDatabase, get_postgres_db
from src.utils.logging import setup_logging

logger = setup_logging("akrin.database")


def get_database() -> Union[SQLiteDatabase, PostgresDatabase]:
    """
    Get database instance based on DATABASE_URL
    
    If DATABASE_URL starts with 'postgres://' or 'postgresql://', use PostgreSQL
    Otherwise, use SQLite
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./akrin_chatbot.db")
    
    if database_url.startswith(("postgres://", "postgresql://")):
        logger.info("Using PostgreSQL database (Supabase)")
        return get_postgres_db()
    else:
        logger.info("Using SQLite database")
        return get_sqlite_db()


# Export the get_database function as the main interface
__all__ = ['get_database']