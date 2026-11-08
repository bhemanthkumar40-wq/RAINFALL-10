"""
Database management service for Rainfall Analysis.
Provides SQLite persistence for user accounts and prediction history
with strict user ownership verification, safe error handling, and guaranteed connection cleanup.
"""

import os
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any

DEFAULT_DB_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "rainfall_app.db"
)

def get_db_path() -> str:
    """Returns the database path configured in environment or default."""
    return os.environ.get("DATABASE_PATH", DEFAULT_DB_PATH)

@contextmanager
def db_session():
    """Context manager that guarantees transaction commit and connection closing."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db() -> None:
    """Initializes tables and indexes if they do not exist."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Predictions table with foreign key and user ownership indexing
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                region TEXT NOT NULL,
                season TEXT NOT NULL,
                temperature_c REAL NOT NULL,
                humidity_pct REAL NOT NULL,
                cloud_cover_pct REAL NOT NULL,
                wind_speed_kmh REAL NOT NULL,
                atmospheric_pressure_hpa REAL NOT NULL,
                soil_moisture_pct REAL NOT NULL,
                soil_type TEXT NOT NULL,
                model_used TEXT NOT NULL,
                predicted_rain INTEGER NOT NULL,
                rain_probability REAL NOT NULL,
                rainfall_category TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)")

# --- User Management ---

def create_user(email: str, password_hash: str, full_name: str) -> Optional[int]:
    """Creates a new user record. Returns new user ID or None on conflict."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name) VALUES (?, ?, ?)",
                (email.lower().strip(), password_hash, full_name.strip())
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user by case-insensitive email."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, full_name, created_at FROM users WHERE email = ?",
            (email.lower().strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves user by primary key ID."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, full_name, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

# --- Prediction History with Strict Ownership Isolation ---

def save_prediction(user_id: int, prediction_data: Dict[str, Any]) -> int:
    """Saves an authenticated prediction entry under the specified user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO predictions (
                user_id, region, season, temperature_c, humidity_pct,
                cloud_cover_pct, wind_speed_kmh, atmospheric_pressure_hpa,
                soil_moisture_pct, soil_type, model_used, predicted_rain,
                rain_probability, rainfall_category
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            prediction_data.get("region", "Unknown"),
            prediction_data.get("season", "Unknown"),
            float(prediction_data.get("temperature_c", 0.0)),
            float(prediction_data.get("humidity_pct", 0.0)),
            float(prediction_data.get("cloud_cover_pct", 0.0)),
            float(prediction_data.get("wind_speed_kmh", 0.0)),
            float(prediction_data.get("atmospheric_pressure_hpa", 1013.25)),
            float(prediction_data.get("soil_moisture_pct", 0.0)),
            prediction_data.get("soil_type", "Unknown"),
            prediction_data.get("model_used", "Random Forest"),
            int(prediction_data.get("predicted_rain", 0)),
            float(prediction_data.get("rain_probability", 0.0)),
            prediction_data.get("rainfall_category", "No Rain")
        ))
        return cursor.lastrowid

def get_user_predictions(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    region: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Retrieves prediction history exclusively for the authenticated user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        if region:
            cursor.execute("""
                SELECT id, region, season, temperature_c, humidity_pct,
                       cloud_cover_pct, wind_speed_kmh, atmospheric_pressure_hpa,
                       soil_moisture_pct, soil_type, model_used, predicted_rain,
                       rain_probability, rainfall_category, created_at
                FROM predictions
                WHERE user_id = ? AND region = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, region, limit, offset))
        else:
            cursor.execute("""
                SELECT id, region, season, temperature_c, humidity_pct,
                       cloud_cover_pct, wind_speed_kmh, atmospheric_pressure_hpa,
                       soil_moisture_pct, soil_type, model_used, predicted_rain,
                       rain_probability, rainfall_category, created_at
                FROM predictions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]

def get_user_prediction_count(user_id: int, region: Optional[str] = None) -> int:
    """Returns the total number of predictions for the given user."""
    with db_session() as conn:
        cursor = conn.cursor()
        if region:
            cursor.execute(
                "SELECT COUNT(*) FROM predictions WHERE user_id = ? AND region = ?",
                (user_id, region)
            )
        else:
            cursor.execute(
                "SELECT COUNT(*) FROM predictions WHERE user_id = ?",
                (user_id,)
            )
        return cursor.fetchone()[0]

def delete_user_prediction(user_id: int, prediction_id: int) -> bool:
    """Deletes a prediction record strictly owned by user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM predictions WHERE id = ? AND user_id = ?",
            (prediction_id, user_id)
        )
        return cursor.rowcount > 0

def clear_user_predictions(user_id: int) -> int:
    """Clears all prediction records belonging strictly to user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM predictions WHERE user_id = ?",
            (user_id,)
        )
        return cursor.rowcount
