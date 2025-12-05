import psycopg2
import os
from typing import Optional


def get_connection():
    """
    Get a database connection using environment variables or defaults.
    """
    return psycopg2.connect(
        dbname=os.getenv("DB_NAME", "restaurant_db"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "user@123"),
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5434"),
    )

