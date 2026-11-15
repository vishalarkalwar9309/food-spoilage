"""
test_database.py
Automated persistence tests for SQLite database operations.
Tests initialization, isolation, session management, restart persistence, and out-of-order timestamp safety.
"""

import os
import tempfile
import pytest
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database


@pytest.fixture
def temp_db():
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.init_db(path)
    yield path
    if os.path.exists(path):
        os.remove(path)


def test_init_db_and_profiles(temp_db):
    """Verify tables exist and 4 default profiles are seeded."""
    profiles = database.get_all_food_profiles(temp_db)
    assert len(profiles) >= 4
    profile_ids = [p["id"] for p in profiles]
    assert "tomatoes" in profile_ids
    assert "bananas" in profile_ids
    assert "apples" in profile_ids
    assert "leafy_vegetables" in profile_ids


def test_session_lifecycle(temp_db):
    """Test starting, tracking, and ending storage sessions."""
    # Initially no active session
    assert database.get_active_session(temp_db) is None

    # Start session
    session = database.start_session("tomatoes", "Test Batch 001", temp_db)
    assert session["id"] is not None
    assert session["food_profile_id"] == "tomatoes"
    assert session["is_active"] == 1

    active = database.get_active_session(temp_db)
    assert active is not None
    assert active["id"] == session["id"]

    # End session
    ended = database.end_active_session(temp_db)
    assert ended["is_active"] == 0
    assert database.get_active_session(temp_db) is None


def test_sensor_reading_and_risk_persistence(temp_db):
    """Test inserting reading and linked risk history."""
    session = database.start_session("bananas", "Banana Test", temp_db)
    now_iso = datetime.now(timezone.utc).isoformat()
    reading_id = database.insert_sensor_reading(
        device_id="ESP32_HEADSPACE",
        source="esp32",
        temperature=14.5,
        humidity=90.0,
        gas=210.0,
        timestamp=now_iso,
        session_id=session["id"],
        db_path=temp_db
    )
    assert reading_id > 0

    risk_id = database.insert_risk_history(
        reading_id=reading_id,
        session_id=session["id"],
        food_profile_id="bananas",
        temp_score=0.0,
        humidity_score=0.0,
        gas_score=15.0,
        duration_score=5.0,
        composite_risk=4.75,
        risk_category="Low",
        recommendation="Conditions optimal.",
        timestamp=now_iso,
        db_path=temp_db
    )
    assert risk_id > 0

    # Query latest state
    latest = database.get_latest_state(temp_db)
    assert latest is not None
    assert latest["reading_id"] == reading_id
    assert latest["temperature"] == 14.5
    assert latest["composite_risk"] == 4.75

    # Query history
    history = database.get_history(hours=24.0, limit=10, db_path=temp_db)
    assert len(history) == 1
    assert history[0]["id"] == reading_id


def test_persistence_across_restart(temp_db):
    """Historical data remains intact across connection re-opens (simulating app restart)."""
    session = database.start_session("apples", "Apple Winter Store", temp_db)
    now_iso = datetime.now(timezone.utc).isoformat()
    database.insert_sensor_reading(
        device_id="DEV_01",
        source="simulator",
        temperature=2.5,
        humidity=92.0,
        gas=180.0,
        timestamp=now_iso,
        session_id=session["id"],
        db_path=temp_db
    )

    # Re-initialize should NOT wipe existing records
    database.init_db(temp_db)
    sessions = database.get_all_sessions(db_path=temp_db)
    assert len(sessions) >= 1
    history = database.get_history(hours=24.0, limit=10, db_path=temp_db)
    assert len(history) >= 1


def test_alerts_logging_and_ack(temp_db):
    """Test inserting and acknowledging alerts."""
    session = database.start_session("leafy_vegetables", "Greens Test", temp_db)
    now_iso = datetime.now(timezone.utc).isoformat()
    alert_id = database.insert_alert(
        severity="High",
        message="Critical humidity drop",
        risk_score=75.5,
        timestamp=now_iso,
        previous_severity="Moderate",
        session_id=session["id"],
        db_path=temp_db
    )
    assert alert_id > 0

    alerts = database.get_alerts(limit=10, db_path=temp_db)
    assert len(alerts) == 1
    assert alerts[0]["acknowledged"] == 0

    # Acknowledge
    assert database.acknowledge_alert(alert_id, db_path=temp_db) is True
    updated_alerts = database.get_alerts(limit=10, db_path=temp_db)
    assert updated_alerts[0]["acknowledged"] == 1


def test_out_of_order_timestamp_handling(temp_db):
    """Verify last_reading_time does not wind backwards when receiving out-of-order timestamps."""
    session = database.start_session("tomatoes", "Test Batch", temp_db)
    sid = session["id"]

    t1 = "2026-11-15T10:00:00+00:00"
    t2 = "2026-11-15T10:05:00+00:00"
    t_older = "2026-11-15T09:50:00+00:00"

    database.update_session_duration(sid, 0.08, t1, temp_db)
    database.update_session_duration(sid, 0.08, t2, temp_db)

    active = database.get_active_session(temp_db)
    assert active["last_reading_time"] == t2

    # Now an out-of-order reading arrives with older timestamp
    database.update_session_duration(sid, 0.0, t_older, temp_db)

    # last_reading_time MUST remain t2, not wind back to t_older
    active_after = database.get_active_session(temp_db)
    assert active_after["last_reading_time"] == t2


def test_get_previous_risk_for_session(temp_db):
    """Verify tracking of session-specific risk history for alert transitions."""
    s1 = database.start_session("tomatoes", "Batch A", temp_db)
    s2 = database.start_session("bananas", "Batch B", temp_db)

    # Initial risk for s2 is None
    assert database.get_previous_risk_for_session(s2["id"], temp_db) is None

    # Insert risk for s2
    rid = database.insert_sensor_reading("D1", "esp32", 14.0, 90.0, 200.0, "2026-11-15T12:00:00Z", s2["id"], temp_db)
    database.insert_risk_history(rid, s2["id"], "bananas", 0.0, 0.0, 10.0, 0.0, 2.5, "Low", "Optimal", "2026-11-15T12:00:00Z", temp_db)

    assert database.get_previous_risk_for_session(s2["id"], temp_db) == "Low"

    # Insert High risk for s2
    rid2 = database.insert_sensor_reading("D1", "esp32", 28.0, 60.0, 400.0, "2026-11-15T12:05:00Z", s2["id"], temp_db)
    database.insert_risk_history(rid2, s2["id"], "bananas", 80.0, 50.0, 100.0, 1.0, 61.7, "High", "Stress", "2026-11-15T12:05:00Z", temp_db)

    assert database.get_previous_risk_for_session(s2["id"], temp_db) == "High"


def test_empty_database_state_safety(temp_db):
    """Empty database state must return graceful null/empty responses without exception."""
    latest = database.get_latest_state(temp_db)
    assert latest is None

    history = database.get_history(db_path=temp_db)
    assert history == []

    alerts = database.get_alerts(db_path=temp_db)
    assert alerts == []
