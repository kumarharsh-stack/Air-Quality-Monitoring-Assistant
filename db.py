"""
All SQLite access lives here, so the rest of the app never writes raw SQL.
Uses Python's built-in sqlite3 module - no extra install needed.
"""

import sqlite3
import os
from datetime import datetime

# The .db file is created inside the data/ folder, next to this project.
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "air_quality.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["pm2_5"]
    return conn


def init_db():
    """Creates the readings table if it doesn't already exist. Safe to call every startup."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            location TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            us_aqi REAL,
            pm2_5 REAL,
            pm10 REAL,
            ozone REAL,
            no2 REAL,
            recorded_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def insert_reading(location, latitude, longitude, us_aqi, pm2_5, pm10, ozone, no2):
    conn = get_connection()
    conn.execute(
        """
        INSERT INTO readings (location, latitude, longitude, us_aqi, pm2_5, pm10, ozone, no2, recorded_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (location, latitude, longitude, us_aqi, pm2_5, pm10, ozone, no2, datetime.utcnow().isoformat()),
    )
    conn.commit()
    conn.close()


def get_history(location: str, limit: int = 50):
    """Returns the most recent `limit` readings for a location, oldest first (good for charting)."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT location, us_aqi, pm2_5, pm10, ozone, no2, recorded_at
        FROM readings
        WHERE location = ?
        ORDER BY recorded_at DESC
        LIMIT ?
        """,
        (location, limit),
    ).fetchall()
    conn.close()

    # We fetched newest-first (to apply LIMIT correctly), now reverse to oldest-first for the chart.
    return [dict(row) for row in reversed(rows)]


def get_latest_reading(location: str):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT location, us_aqi, pm2_5, pm10, ozone, no2, recorded_at
        FROM readings
        WHERE location = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (location,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
