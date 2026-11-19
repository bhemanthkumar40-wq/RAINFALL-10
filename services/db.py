"""
Database management service for Rainfall Analysis.
Provides SQLite persistence for:
1. User accounts with RBAC (admin/user), activation status, last login.
2. Login attempt audit logs.
3. Managed datasets (default and uploaded custom datasets).
4. Machine learning model benchmark metrics.
5. User prediction history with strict ownership isolation.
"""

import os
import json
import sqlite3
from contextlib import contextmanager
from typing import Optional, List, Dict, Any, Tuple
from werkzeug.security import generate_password_hash

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
    """Context manager that guarantees transaction commit, rollback on error, and connection closing."""
    db_path = get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=15)
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
    """Initializes tables, applies schema migrations, and seeds default records."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        # 1. Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                is_active INTEGER DEFAULT 1,
                last_login TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Migration: Ensure role, is_active, last_login exist on users table
        cursor.execute("PRAGMA table_info(users)")
        user_cols = [col[1] for col in cursor.fetchall()]
        if "role" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        if "is_active" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 1")
        if "last_login" not in user_cols:
            cursor.execute("ALTER TABLE users ADD COLUMN last_login TIMESTAMP")
            
        # 2. Login Logs Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                ip_address TEXT,
                status TEXT NOT NULL,
                reason TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # 3. Datasets Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS datasets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                filename TEXT NOT NULL,
                filepath TEXT NOT NULL,
                rows_count INTEGER DEFAULT 0,
                cols_count INTEGER DEFAULT 0,
                target_col TEXT DEFAULT 'ANNUAL',
                features_json TEXT,
                uploaded_by INTEGER,
                is_default INTEGER DEFAULT 0,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (uploaded_by) REFERENCES users(id) ON DELETE SET NULL
            )
        """)
        
        # 4. Model Benchmark Metrics Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS model_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dataset_name TEXT NOT NULL,
                model_name TEXT NOT NULL,
                r2_score REAL NOT NULL,
                mae REAL NOT NULL,
                mse REAL NOT NULL,
                rmse REAL NOT NULL,
                mape REAL NOT NULL,
                training_time REAL NOT NULL,
                is_best INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 5. Predictions Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                dataset_name TEXT DEFAULT 'Subdivision Rainfall (1901-2015)',
                region TEXT NOT NULL,
                season TEXT NOT NULL,
                temperature_c REAL DEFAULT 0.0,
                humidity_pct REAL DEFAULT 0.0,
                cloud_cover_pct REAL DEFAULT 0.0,
                wind_speed_kmh REAL DEFAULT 0.0,
                atmospheric_pressure_hpa REAL DEFAULT 1013.25,
                soil_moisture_pct REAL DEFAULT 0.0,
                soil_type TEXT DEFAULT 'Alluvial',
                model_used TEXT NOT NULL,
                predicted_rain INTEGER DEFAULT 0,
                predicted_rainfall_mm REAL DEFAULT 0.0,
                rain_probability REAL DEFAULT 0.0,
                rainfall_category TEXT DEFAULT 'Moderate Rain',
                confidence_pct REAL DEFAULT 90.0,
                advisory TEXT DEFAULT 'Normal agricultural and seasonal advisory.',
                inputs_json TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        
        # Migration: Ensure new prediction columns exist
        cursor.execute("PRAGMA table_info(predictions)")
        pred_cols = [col[1] for col in cursor.fetchall()]
        if "dataset_name" not in pred_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN dataset_name TEXT DEFAULT 'Subdivision Rainfall (1901-2015)'")
        if "predicted_rainfall_mm" not in pred_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN predicted_rainfall_mm REAL DEFAULT 0.0")
        if "confidence_pct" not in pred_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN confidence_pct REAL DEFAULT 90.0")
        if "advisory" not in pred_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN advisory TEXT")
        if "inputs_json" not in pred_cols:
            cursor.execute("ALTER TABLE predictions ADD COLUMN inputs_json TEXT")

        # Indexes for ultra-fast queries
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_user_id ON predictions(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_predictions_created_at ON predictions(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_login_logs_created_at ON login_logs(created_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_model_metrics_dataset ON model_metrics(dataset_name)")

        # Seed Default Admin Account
        cursor.execute("SELECT id FROM users WHERE email = 'admin@rainfall.org'")
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO users (email, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, 'admin', 1)
            """, ('admin@rainfall.org', generate_password_hash('Admin@1234'), 'System Administrator'))

        # Ensure existing bhemanthkumar40 is marked admin
        cursor.execute("UPDATE users SET role = 'admin' WHERE email LIKE 'bhemanthkumar40%'")

        # Seed Default Datasets
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ds1_path = os.path.join(base_dir, "data", "district_wise_rainfall_normal.csv")
        ds2_path = os.path.join(base_dir, "data", "rainfall_in_india_1901_2015.csv")

        months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
        
        if os.path.exists(ds1_path):
            cursor.execute("SELECT id FROM datasets WHERE name = 'India District-Wise Normal Rainfall'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO datasets (name, filename, filepath, rows_count, cols_count, target_col, features_json, is_default)
                    VALUES (?, ?, ?, 641, 19, 'ANNUAL', ?, 1)
                """, ('India District-Wise Normal Rainfall', 'district_wise_rainfall_normal.csv', ds1_path, json.dumps(months)))

        if os.path.exists(ds2_path):
            cursor.execute("SELECT id FROM datasets WHERE name = 'Subdivision Rainfall (1901-2015)'")
            if not cursor.fetchone():
                cursor.execute("""
                    INSERT INTO datasets (name, filename, filepath, rows_count, cols_count, target_col, features_json, is_default)
                    VALUES (?, ?, ?, 4116, 19, 'ANNUAL', ?, 1)
                """, ('Subdivision Rainfall (1901-2015)', 'rainfall_in_india_1901_2015.csv', ds2_path, json.dumps(months)))


# --- User Management ---

def create_user(email: str, password_hash: str, full_name: str, role: str = "user") -> Optional[int]:
    """Creates a new user record. Returns new user ID or None on conflict."""
    try:
        with db_session() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (email, password_hash, full_name, role, is_active) VALUES (?, ?, ?, ?, 1)",
                (email.lower().strip(), password_hash, full_name.strip(), role)
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Retrieves user by case-insensitive email."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, password_hash, full_name, role, is_active, last_login, created_at FROM users WHERE email = ?",
            (email.lower().strip(),)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Retrieves user by primary key ID."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, email, full_name, role, is_active, last_login, created_at FROM users WHERE id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

def update_user_last_login(user_id: int) -> None:
    """Updates user last login timestamp."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))

def update_user_profile(user_id: int, full_name: str) -> bool:
    """Updates full name for given user."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET full_name = ? WHERE id = ?", (full_name.strip(), user_id))
        return cursor.rowcount > 0

def update_user_password(user_id: int, new_password_hash: str) -> bool:
    """Updates password hash for given user."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = ? WHERE id = ?", (new_password_hash, user_id))
        return cursor.rowcount > 0

def get_all_users() -> List[Dict[str, Any]]:
    """Retrieves all users for Admin Dashboard."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.id, u.email, u.full_name, u.role, u.is_active, u.last_login, u.created_at,
                   COUNT(p.id) AS prediction_count
            FROM users u
            LEFT JOIN predictions p ON u.id = p.user_id
            GROUP BY u.id
            ORDER BY u.created_at DESC
        """)
        return [dict(row) for row in cursor.fetchall()]

def toggle_user_active_status(user_id: int) -> Optional[int]:
    """Toggles active/inactive status. Returns new status or None."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_active FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        if not row:
            return None
        new_status = 0 if row["is_active"] == 1 else 1
        cursor.execute("UPDATE users SET is_active = ? WHERE id = ?", (new_status, user_id))
        return new_status

def set_user_role(user_id: int, role: str) -> bool:
    """Updates user role (e.g. 'admin' or 'user')."""
    if role not in ("admin", "user"):
        return False
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        return cursor.rowcount > 0

def delete_user(user_id: int) -> bool:
    """Deletes a user and cascades deletion to predictions."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
        return cursor.rowcount > 0


# --- Login Attempt Audit Logs ---

def log_login_attempt(email: str, status: str, ip_address: str = "127.0.0.1", reason: Optional[str] = None) -> None:
    """Logs an authentication attempt (success or failure)."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO login_logs (email, ip_address, status, reason)
            VALUES (?, ?, ?, ?)
        """, (email.lower().strip() if email else "unknown", ip_address, status, reason))

def get_recent_login_logs(limit: int = 50) -> List[Dict[str, Any]]:
    """Retrieves recent login attempt audit logs."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, email, ip_address, status, reason, created_at
            FROM login_logs
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(row) for row in cursor.fetchall()]


# --- Dataset Management ---

def register_dataset(name: str, filename: str, filepath: str, rows: int, cols: int,
                     target_col: str, features: List[str], uploaded_by: Optional[int] = None) -> int:
    """Registers a new or uploaded dataset in database."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO datasets (name, filename, filepath, rows_count, cols_count, target_col, features_json, uploaded_by, is_default)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(name) DO UPDATE SET
                filename = excluded.filename,
                filepath = excluded.filepath,
                rows_count = excluded.rows_count,
                cols_count = excluded.cols_count,
                target_col = excluded.target_col,
                features_json = excluded.features_json
        """, (name, filename, filepath, rows, cols, target_col, json.dumps(features), uploaded_by))
        return cursor.lastrowid

def get_all_datasets() -> List[Dict[str, Any]]:
    """Returns all registered datasets."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT d.id, d.name, d.filename, d.filepath, d.rows_count, d.cols_count,
                   d.target_col, d.features_json, d.is_default, d.uploaded_at,
                   u.full_name AS uploaded_by_name
            FROM datasets d
            LEFT JOIN users u ON d.uploaded_by = u.id
            ORDER BY d.is_default DESC, d.uploaded_at DESC
        """)
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["features"] = json.loads(d["features_json"]) if d["features_json"] else []
            result.append(d)
        return result

def get_dataset_by_name(name: str) -> Optional[Dict[str, Any]]:
    """Gets dataset details by name."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, filename, filepath, rows_count, cols_count, target_col, features_json, is_default, uploaded_at
            FROM datasets WHERE name = ?
        """, (name,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["features"] = json.loads(d["features_json"]) if d["features_json"] else []
        return d

def get_dataset_by_id(dataset_id: int) -> Optional[Dict[str, Any]]:
    """Gets dataset details by ID."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, filename, filepath, rows_count, cols_count, target_col, features_json, is_default, uploaded_at
            FROM datasets WHERE id = ?
        """, (dataset_id,))
        row = cursor.fetchone()
        if not row:
            return None
        d = dict(row)
        d["features"] = json.loads(d["features_json"]) if d["features_json"] else []
        return d


# --- Model Metrics Persistence ---

def save_model_metrics(dataset_name: str, metrics_list: List[Dict[str, Any]]) -> None:
    """Saves benchmark metrics for models trained on a specific dataset."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM model_metrics WHERE dataset_name = ?", (dataset_name,))
        
        # Determine best model by highest R2 score
        best_r2 = -float("inf")
        best_name = None
        for m in metrics_list:
            if m.get("r2_score", -999) > best_r2:
                best_r2 = m.get("r2_score")
                best_name = m.get("model_name")
                
        for m in metrics_list:
            cursor.execute("""
                INSERT INTO model_metrics (
                    dataset_name, model_name, r2_score, mae, mse, rmse, mape, training_time, is_best
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                dataset_name,
                m.get("model_name"),
                float(m.get("r2_score", 0.0)),
                float(m.get("mae", 0.0)),
                float(m.get("mse", 0.0)),
                float(m.get("rmse", 0.0)),
                float(m.get("mape", 0.0)),
                float(m.get("training_time", 0.0)),
                1 if m.get("model_name") == best_name else 0
            ))

def get_model_metrics(dataset_name: str) -> List[Dict[str, Any]]:
    """Retrieves saved model metrics for a dataset."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT model_name, r2_score, mae, mse, rmse, mape, training_time, is_best, created_at
            FROM model_metrics
            WHERE dataset_name = ?
            ORDER BY r2_score DESC
        """, (dataset_name,))
        return [dict(r) for r in cursor.fetchall()]


# --- Prediction History Management ---

def save_prediction(user_id: int, prediction_data: Dict[str, Any]) -> int:
    """Saves an authenticated prediction entry under user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        pred_mm = float(prediction_data.get("predicted_rainfall_mm", prediction_data.get("predicted_rain", 0.0)))
        prob = float(prediction_data.get("rain_probability", min(100.0, pred_mm / 15.0 * 10.0)))
        
        cursor.execute("""
            INSERT INTO predictions (
                user_id, dataset_name, region, season, temperature_c, humidity_pct,
                cloud_cover_pct, wind_speed_kmh, atmospheric_pressure_hpa,
                soil_moisture_pct, soil_type, model_used, predicted_rain,
                predicted_rainfall_mm, rain_probability, rainfall_category,
                confidence_pct, advisory, inputs_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            prediction_data.get("dataset_name", "Subdivision Rainfall (1901-2015)"),
            prediction_data.get("region", "India Central"),
            prediction_data.get("season", "Monsoon"),
            float(prediction_data.get("temperature_c", 28.5)),
            float(prediction_data.get("humidity_pct", 75.0)),
            float(prediction_data.get("cloud_cover_pct", 60.0)),
            float(prediction_data.get("wind_speed_kmh", 14.0)),
            float(prediction_data.get("atmospheric_pressure_hpa", 1010.0)),
            float(prediction_data.get("soil_moisture_pct", 45.0)),
            prediction_data.get("soil_type", "Alluvial"),
            prediction_data.get("model_used", "Random Forest Regressor"),
            int(1 if pred_mm > 2.5 else 0),
            pred_mm,
            prob,
            prediction_data.get("rainfall_category", "Moderate Rain"),
            float(prediction_data.get("confidence_pct", 92.5)),
            prediction_data.get("advisory", "Favorable conditions for agricultural operations."),
            json.dumps(prediction_data.get("inputs", {}))
        ))
        return cursor.lastrowid

def get_user_predictions(user_id: int, limit: int = 50, offset: int = 0, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves prediction history exclusively for the authenticated user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        if region:
            cursor.execute("""
                SELECT id, dataset_name, region, season, temperature_c, humidity_pct,
                       cloud_cover_pct, wind_speed_kmh, atmospheric_pressure_hpa,
                       soil_moisture_pct, soil_type, model_used, predicted_rain,
                       predicted_rainfall_mm, rain_probability, rainfall_category,
                       confidence_pct, advisory, inputs_json, created_at
                FROM predictions
                WHERE user_id = ? AND region LIKE ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, f"%{region}%", limit, offset))
        else:
            cursor.execute("""
                SELECT id, dataset_name, region, season, temperature_c, humidity_pct,
                       cloud_cover_pct, wind_speed_kmh, atmospheric_pressure_hpa,
                       soil_moisture_pct, soil_type, model_used, predicted_rain,
                       predicted_rainfall_mm, rain_probability, rainfall_category,
                       confidence_pct, advisory, inputs_json, created_at
                FROM predictions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        rows = cursor.fetchall()
        result = []
        for r in rows:
            d = dict(r)
            d["inputs"] = json.loads(d["inputs_json"]) if d.get("inputs_json") else {}
            # Ensure predicted_rainfall_mm has non-zero fallback
            if d.get("predicted_rainfall_mm", 0.0) == 0.0 and d.get("rain_probability", 0.0) > 0.0:
                d["predicted_rainfall_mm"] = round(d["rain_probability"] * 1.5, 1)
            result.append(d)
        return result

def get_user_prediction_count(user_id: int) -> int:
    """Returns total prediction count for user."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE user_id = ?", (user_id,))
        return cursor.fetchone()[0]

def get_all_predictions(limit: int = 100) -> List[Dict[str, Any]]:
    """Retrieves system-wide predictions for Admin Dashboard."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.dataset_name, p.region, p.season, p.model_used,
                   p.predicted_rainfall_mm, p.rainfall_category, p.confidence_pct,
                   p.created_at, u.full_name AS user_name, u.email AS user_email
            FROM predictions p
            JOIN users u ON p.user_id = u.id
            ORDER BY p.created_at DESC
            LIMIT ?
        """, (limit,))
        return [dict(r) for r in cursor.fetchall()]

def delete_user_prediction(user_id: int, prediction_id: int) -> bool:
    """Deletes a prediction record strictly owned by user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions WHERE id = ? AND user_id = ?", (prediction_id, user_id))
        return cursor.rowcount > 0

def clear_user_predictions(user_id: int) -> int:
    """Clears all prediction records belonging strictly to user_id."""
    with db_session() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM predictions WHERE user_id = ?", (user_id,))
        return cursor.rowcount

def get_platform_stats() -> Dict[str, Any]:
    """Retrieves overall platform statistics for Dashboard and Admin."""
    with db_session() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
        active_users = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total_predictions = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM datasets")
        total_datasets = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT predicted_rainfall_mm, rainfall_category, model_used, region, created_at
            FROM predictions ORDER BY created_at DESC LIMIT 1
        """)
        latest_pred = cursor.fetchone()
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "total_predictions": total_predictions,
            "total_datasets": total_datasets,
            "latest_prediction": dict(latest_pred) if latest_pred else None
        }
