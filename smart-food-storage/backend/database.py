"""
database.py
SQLite persistence layer for Smart Food Storage Spoilage Predictor.
Manages food_storage.db with parameterized queries and WAL mode.
"""

import os
import sqlite3
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from food_profiles import DEFAULT_FOOD_PROFILES

DEFAULT_DB_PATH = os.path.join(os.path.dirname(__file__), "food_storage.db")


def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a database connection with dictionary row factory and WAL mode."""
    conn = sqlite3.connect(db_path, timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize database tables and seed predefined food profiles if empty."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    # 1. Food Profiles
    cur.execute("""
    CREATE TABLE IF NOT EXISTS food_profiles (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        scientific_name TEXT,
        category TEXT,
        temp_min REAL NOT NULL,
        temp_max REAL NOT NULL,
        temp_crit REAL NOT NULL,
        temp_freeze REAL NOT NULL,
        humidity_min REAL NOT NULL,
        humidity_max REAL NOT NULL,
        ideal_shelf_life_hours REAL NOT NULL,
        gas_baseline REAL NOT NULL,
        gas_threshold REAL NOT NULL,
        weight_temp REAL NOT NULL,
        weight_humidity REAL NOT NULL,
        weight_gas REAL NOT NULL,
        weight_duration REAL NOT NULL,
        stress_multiplier_alpha REAL NOT NULL,
        description TEXT,
        icon TEXT,
        created_at TEXT NOT NULL
    );
    """)

    # 2. Storage Sessions
    cur.execute("""
    CREATE TABLE IF NOT EXISTS storage_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_name TEXT NOT NULL,
        food_profile_id TEXT NOT NULL,
        start_time TEXT NOT NULL,
        end_time TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        last_reading_time TEXT,
        accumulated_effective_hours REAL NOT NULL DEFAULT 0.0,
        total_readings_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (food_profile_id) REFERENCES food_profiles (id)
    );
    """)

    # 3. Sensor Readings
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sensor_readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        device_id TEXT NOT NULL,
        source TEXT NOT NULL,
        temperature REAL NOT NULL,
        humidity REAL NOT NULL,
        gas REAL NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (session_id) REFERENCES storage_sessions (id)
    );
    """)

    # 4. Risk History
    cur.execute("""
    CREATE TABLE IF NOT EXISTS risk_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reading_id INTEGER,
        session_id INTEGER,
        food_profile_id TEXT NOT NULL,
        temp_score REAL NOT NULL,
        humidity_score REAL NOT NULL,
        gas_score REAL NOT NULL,
        duration_score REAL NOT NULL,
        composite_risk REAL NOT NULL,
        risk_category TEXT NOT NULL,
        recommendation TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (reading_id) REFERENCES sensor_readings (id),
        FOREIGN KEY (session_id) REFERENCES storage_sessions (id),
        FOREIGN KEY (food_profile_id) REFERENCES food_profiles (id)
    );
    """)

    # 5. Alerts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER,
        severity TEXT NOT NULL,
        message TEXT NOT NULL,
        risk_score REAL NOT NULL,
        previous_severity TEXT,
        timestamp TEXT NOT NULL,
        acknowledged INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (session_id) REFERENCES storage_sessions (id)
    );
    """)

    # Indexes for performance
    cur.execute("CREATE INDEX IF NOT EXISTS idx_readings_timestamp ON sensor_readings(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_risk_timestamp ON risk_history(timestamp);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_sessions_active ON storage_sessions(is_active);")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(timestamp);")

    # Seed predefined food profiles if table is empty
    cur.execute("SELECT COUNT(*) as cnt FROM food_profiles;")
    row = cur.fetchone()
    if row and row["cnt"] == 0:
        now_iso = datetime.now(timezone.utc).isoformat()
        for p in DEFAULT_FOOD_PROFILES.values():
            cur.execute("""
            INSERT INTO food_profiles (
                id, name, scientific_name, category, temp_min, temp_max, temp_crit, temp_freeze,
                humidity_min, humidity_max, ideal_shelf_life_hours, gas_baseline, gas_threshold,
                weight_temp, weight_humidity, weight_gas, weight_duration, stress_multiplier_alpha,
                description, icon, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                p["id"], p["name"], p.get("scientific_name", ""), p.get("category", ""),
                p["temp_min"], p["temp_max"], p["temp_crit"], p["temp_freeze"],
                p["humidity_min"], p["humidity_max"], p["ideal_shelf_life_hours"],
                p["gas_baseline"], p["gas_threshold"], p["weight_temp"], p["weight_humidity"],
                p["weight_gas"], p["weight_duration"], p["stress_multiplier_alpha"],
                p.get("description", ""), p.get("icon", ""), now_iso
            ))

    conn.commit()
    conn.close()


def get_all_food_profiles(db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve all food profiles."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM food_profiles ORDER BY name ASC;")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_food_profile(profile_id: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve a single food profile by ID."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM food_profiles WHERE id = ?;", (profile_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_active_session(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the current active storage session with profile metadata."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, p.name as food_name, p.temp_min, p.temp_max, p.humidity_min, p.humidity_max,
               p.ideal_shelf_life_hours, p.gas_baseline, p.gas_threshold, p.stress_multiplier_alpha
        FROM storage_sessions s
        JOIN food_profiles p ON s.food_profile_id = p.id
        WHERE s.is_active = 1
        ORDER BY s.id DESC LIMIT 1;
    """)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def start_session(food_profile_id: str, session_name: Optional[str] = None, db_path: str = DEFAULT_DB_PATH) -> Dict[str, Any]:
    """Start a new storage session and deactivate any previous active session."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()

    # Deactivate existing active sessions
    cur.execute("UPDATE storage_sessions SET is_active = 0, end_time = ? WHERE is_active = 1;", (now_iso,))

    name = session_name if session_name else f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    cur.execute("""
        INSERT INTO storage_sessions (
            session_name, food_profile_id, start_time, is_active,
            last_reading_time, accumulated_effective_hours, total_readings_count
        ) VALUES (?, ?, ?, 1, ?, 0.0, 0);
    """, (name, food_profile_id, now_iso, now_iso))

    session_id = cur.lastrowid
    conn.commit()
    conn.close()

    return get_active_session(db_path) or {"id": session_id, "session_name": name, "food_profile_id": food_profile_id}


def end_active_session(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """End all currently active storage sessions and return the most recently ended one."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute("SELECT id FROM storage_sessions WHERE is_active = 1 ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    if not row:
        conn.close()
        return None

    session_id = row["id"]
    cur.execute("UPDATE storage_sessions SET is_active = 0, end_time = ? WHERE is_active = 1;", (now_iso,))
    conn.commit()
    cur.execute("SELECT * FROM storage_sessions WHERE id = ?;", (session_id,))
    ended = dict(cur.fetchone())
    conn.close()
    return ended


def get_all_sessions(limit: int = 50, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve past and active storage sessions."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT s.*, p.name as food_name
        FROM storage_sessions s
        JOIN food_profiles p ON s.food_profile_id = p.id
        ORDER BY s.id DESC LIMIT ?;
    """, (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def update_session_duration(session_id: int, added_effective_hours: float, reading_time: str, db_path: str = DEFAULT_DB_PATH) -> None:
    """
    Update accumulated stress hours and reading count for a session.
    Guarantees last_reading_time is monotonically non-decreasing.
    """
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        UPDATE storage_sessions
        SET accumulated_effective_hours = accumulated_effective_hours + ?,
            last_reading_time = CASE
                WHEN last_reading_time IS NULL OR ? > last_reading_time THEN ?
                ELSE last_reading_time
            END,
            total_readings_count = total_readings_count + 1
        WHERE id = ?;
    """, (added_effective_hours, reading_time, reading_time, session_id))
    conn.commit()
    conn.close()


def insert_sensor_reading(
    device_id: str,
    source: str,
    temperature: float,
    humidity: float,
    gas: float,
    timestamp: str,
    session_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Insert a new sensor reading record."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO sensor_readings (session_id, device_id, source, temperature, humidity, gas, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    """, (session_id, device_id, source, temperature, humidity, gas, timestamp))
    reading_id = cur.lastrowid
    conn.commit()
    conn.close()
    return reading_id


def insert_risk_history(
    reading_id: int,
    session_id: Optional[int],
    food_profile_id: str,
    temp_score: float,
    humidity_score: float,
    gas_score: float,
    duration_score: float,
    composite_risk: float,
    risk_category: str,
    recommendation: str,
    timestamp: str,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Insert a calculated risk assessment record."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO risk_history (
            reading_id, session_id, food_profile_id, temp_score, humidity_score,
            gas_score, duration_score, composite_risk, risk_category, recommendation, timestamp
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (
        reading_id, session_id, food_profile_id, temp_score, humidity_score,
        gas_score, duration_score, composite_risk, risk_category, recommendation, timestamp
    ))
    risk_id = cur.lastrowid
    conn.commit()
    conn.close()
    return risk_id


def insert_alert(
    severity: str,
    message: str,
    risk_score: float,
    timestamp: str,
    previous_severity: Optional[str] = None,
    session_id: Optional[int] = None,
    db_path: str = DEFAULT_DB_PATH
) -> int:
    """Insert a new alert record."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO alerts (session_id, severity, message, risk_score, previous_severity, timestamp, acknowledged)
        VALUES (?, ?, ?, ?, ?, ?, 0);
    """, (session_id, severity, message, risk_score, previous_severity, timestamp))
    alert_id = cur.lastrowid
    conn.commit()
    conn.close()
    return alert_id


def get_latest_state(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent reading joined with its risk assessment and active session."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT r.id as reading_id, r.temperature, r.humidity, r.gas, r.device_id, r.source, r.timestamp,
               k.temp_score, k.humidity_score, k.gas_score, k.duration_score, k.composite_risk,
               k.risk_category, k.recommendation, k.food_profile_id,
               p.name as food_name, p.temp_min, p.temp_max, p.humidity_min, p.humidity_max,
               p.ideal_shelf_life_hours, p.gas_baseline, p.gas_threshold,
               s.id as session_id, s.session_name, s.start_time as session_start_time,
               s.accumulated_effective_hours, s.is_active as session_is_active
        FROM sensor_readings r
        LEFT JOIN risk_history k ON r.id = k.reading_id
        LEFT JOIN food_profiles p ON k.food_profile_id = p.id
        LEFT JOIN storage_sessions s ON r.session_id = s.id
        ORDER BY r.id DESC LIMIT 1;
    """)
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_reading_by_source(source: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent sensor reading matching the given source (e.g. 'esp32' or 'simulator')."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM sensor_readings WHERE source = ? ORDER BY id DESC LIMIT 1;
    """, (source,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_history(hours: Optional[float] = 24.0, limit: int = 500, session_id: Optional[int] = None, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """
    Retrieve historical sensor and risk telemetry within time horizon.
    Filters by timestamp cutoff if hours is provided.
    """
    from datetime import timedelta
    conn = get_db_connection(db_path)
    cur = conn.cursor()

    conditions = []
    params = []

    if hours is not None and hours > 0:
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
        conditions.append("r.timestamp >= ?")
        params.append(cutoff)

    if session_id is not None:
        conditions.append("r.session_id = ?")
        params.append(session_id)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    query = f"""
        SELECT r.id, r.timestamp, r.temperature, r.humidity, r.gas, r.source,
               k.temp_score, k.humidity_score, k.gas_score, k.duration_score,
               k.composite_risk, k.risk_category, k.food_profile_id,
               p.name as food_name
        FROM sensor_readings r
        LEFT JOIN risk_history k ON r.id = k.reading_id
        LEFT JOIN food_profiles p ON k.food_profile_id = p.id
        {where_clause}
        ORDER BY r.id DESC LIMIT ?;
    """
    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    # Return chronological order (oldest to newest for graphs)
    rows.reverse()
    return rows


def get_previous_risk_for_session(session_id: Optional[int], db_path: str = DEFAULT_DB_PATH) -> Optional[str]:
    """Retrieve the risk category of the most recent evaluation for this session or globally."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    if session_id is not None:
        cur.execute("SELECT risk_category FROM risk_history WHERE session_id = ? ORDER BY id DESC LIMIT 1;", (session_id,))
    else:
        cur.execute("SELECT risk_category FROM risk_history ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return row["risk_category"] if row else None


def get_alerts(limit: int = 50, db_path: str = DEFAULT_DB_PATH) -> List[Dict[str, Any]]:
    """Retrieve latest alert notifications."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT ?;", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_latest_alert(db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent alert for state tracking."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT * FROM alerts ORDER BY id DESC LIMIT 1;")
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_latest_reading_by_source(source: str, db_path: str = DEFAULT_DB_PATH) -> Optional[Dict[str, Any]]:
    """Retrieve the most recent sensor reading matching the given source (e.g. 'esp32' or 'simulator')."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM sensor_readings WHERE source = ? ORDER BY id DESC LIMIT 1;
    """, (source,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def acknowledge_alert(alert_id: int, db_path: str = DEFAULT_DB_PATH) -> bool:
    """Mark an alert as acknowledged."""
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("UPDATE alerts SET acknowledged = 1 WHERE id = ?;", (alert_id,))
    updated = cur.rowcount > 0
    conn.commit()
    conn.close()
    return updated
