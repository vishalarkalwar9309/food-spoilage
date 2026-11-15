"""
test_api.py
Automated integration tests for Flask REST endpoints.
Verifies payloads, validation rules, risk calculation endpoints, alert escalation, and simulator operations.
"""

import os
import tempfile
import pytest
import sys
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import database
from app import app, simulator


@pytest.fixture
def client():
    # Use temporary isolated database for tests
    fd, path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    database.init_db(path)

    # Patch app.DB_PATH
    import app as app_module
    old_db = app_module.DB_PATH
    app_module.DB_PATH = path
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        yield test_client

    # Cleanup
    simulator.stop()
    app_module.DB_PATH = old_db
    if os.path.exists(path):
        os.remove(path)


def test_health_endpoint(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "online"
    assert data["database"] == "connected"


def test_food_profiles_endpoint(client):
    res = client.get("/api/food-profiles")
    assert res.status_code == 200
    data = res.get_json()
    assert data["count"] >= 4
    names = [p["name"] for p in data["profiles"]]
    assert "Tomatoes" in names
    assert "Bananas" in names


def test_session_lifecycle_api(client):
    # Start session
    res = client.post("/api/sessions/start", json={
        "food_profile_id": "tomatoes",
        "session_name": "API Test Session"
    })
    assert res.status_code == 201
    s_data = res.get_json()
    assert s_data["status"] == "session_started"
    assert s_data["session"]["food_profile_id"] == "tomatoes"

    # Verify active session
    res_list = client.get("/api/sessions")
    assert res_list.status_code == 200
    list_data = res_list.get_json()
    assert list_data["active_session"] is not None
    assert list_data["active_session"]["session_name"] == "API Test Session"

    # End session
    res_end = client.post("/api/sessions/end")
    assert res_end.status_code == 200
    assert res_end.get_json()["status"] == "session_ended"


def test_sensor_data_validation(client):
    # Empty payload
    res = client.post("/api/sensor-data", json={})
    assert res.status_code == 422

    # Missing fields
    res = client.post("/api/sensor-data", json={"temperature": 20.0})
    assert res.status_code == 422

    # Invalid range: temperature 120°C
    res = client.post("/api/sensor-data", json={
        "temperature": 120.0,
        "humidity": 50.0,
        "gas": 200.0,
        "device_id": "ESP32_01"
    })
    assert res.status_code == 422


def test_sensor_data_nan_inf_validation(client):
    """Verify NaN and Infinity values are strictly rejected."""
    # NaN
    res_nan = client.post("/api/sensor-data", json={
        "temperature": float("nan"),
        "humidity": 85.0,
        "gas": 200.0,
        "device_id": "ESP32_01"
    })
    assert res_nan.status_code == 422

    # Infinity
    res_inf = client.post("/api/sensor-data", json={
        "temperature": 20.0,
        "humidity": float("inf"),
        "gas": 200.0,
        "device_id": "ESP32_01"
    })
    assert res_inf.status_code == 422


def test_sensor_data_ingestion_and_risk(client):
    # Start session for tomatoes
    client.post("/api/sessions/start", json={"food_profile_id": "tomatoes"})

    # Send optimal conditions: 13.5°C, 88% RH, 185 ADC gas
    res = client.post("/api/sensor-data", json={
        "temperature": 13.5,
        "humidity": 88.0,
        "gas": 185.0,
        "device_id": "ESP32_PROD",
        "source": "esp32"
    })
    assert res.status_code == 201
    body = res.get_json()
    assert body["status"] == "success"
    assert body["risk"]["category"] == "Low"
    assert body["risk"]["composite_score"] <= 30.0
    assert body["risk"]["components"]["temp_score"] == 0.0
    assert body["risk"]["components"]["humidity_score"] == 0.0

    # Now query /api/latest
    latest_res = client.get("/api/latest")
    assert latest_res.status_code == 200
    latest_data = latest_res.get_json()
    assert latest_data["has_data"] is True
    assert latest_data["reading"]["temperature"] == 13.5


def test_alert_escalation_logic(client):
    """Alert must trigger on risk category increase and not duplicate identical severity cycles."""
    client.post("/api/sessions/start", json={"food_profile_id": "tomatoes"})

    # 1. Optimal reading (Low risk) -> No alert
    client.post("/api/sensor-data", json={"temperature": 13.5, "humidity": 88.0, "gas": 180.0, "device_id": "D1"})
    alerts = client.get("/api/alerts").get_json()["alerts"]
    assert len(alerts) == 0

    # 2. Elevated reading (High risk) -> Alert triggers
    res2 = client.post("/api/sensor-data", json={"temperature": 28.0, "humidity": 65.0, "gas": 420.0, "device_id": "D1"})
    assert res2.get_json()["new_alert"] is not None

    alerts2 = client.get("/api/alerts").get_json()["alerts"]
    assert len(alerts2) == 1

    # 3. Second reading with SAME high severity -> No duplicate alert
    res3 = client.post("/api/sensor-data", json={"temperature": 28.2, "humidity": 64.5, "gas": 418.0, "device_id": "D1"})
    assert res3.get_json()["new_alert"] is None
    alerts3 = client.get("/api/alerts").get_json()["alerts"]
    assert len(alerts3) == 1  # Unchanged count!


def test_alert_recovery_and_re_escalation(client):
    """
    Critical Test: Low -> High (Alert 1) -> Low (Recovery) -> High (Alert 2).
    Verifies that when environmental stress subsides and escalates again,
    the second escalation is not falsely suppressed!
    """
    client.post("/api/sessions/start", json={"food_profile_id": "tomatoes"})

    # Phase 1: High stress -> Alert #1
    res1 = client.post("/api/sensor-data", json={"temperature": 28.0, "humidity": 65.0, "gas": 420.0, "device_id": "D1"})
    assert res1.get_json()["new_alert"] is not None
    assert len(client.get("/api/alerts").get_json()["alerts"]) == 1

    # Phase 2: Conditions restored to Low (cooling repaired) -> No alert
    res2 = client.post("/api/sensor-data", json={"temperature": 13.5, "humidity": 88.0, "gas": 180.0, "device_id": "D1"})
    assert res2.get_json()["new_alert"] is None
    assert len(client.get("/api/alerts").get_json()["alerts"]) == 1

    # Phase 3: Secondary failure -> High stress -> Alert #2 MUST trigger!
    res3 = client.post("/api/sensor-data", json={"temperature": 29.0, "humidity": 62.0, "gas": 430.0, "device_id": "D1"})
    assert res3.get_json()["new_alert"] is not None
    assert len(client.get("/api/alerts").get_json()["alerts"]) == 2


def test_session_isolation_no_exposure_leak(client):
    """Ensure starting a new session starts with 0.0 effective exposure hours and does not leak prior session hours."""
    # Session 1: simulate stress and duration
    s1 = client.post("/api/sessions/start", json={"food_profile_id": "tomatoes", "session_name": "Batch 1"}).get_json()["session"]
    client.post("/api/sensor-data", json={
        "temperature": 28.0,
        "humidity": 65.0,
        "gas": 400.0,
        "device_id": "D1",
        "timestamp": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
    })
    client.post("/api/sensor-data", json={
        "temperature": 28.0,
        "humidity": 65.0,
        "gas": 400.0,
        "device_id": "D1",
        "timestamp": datetime.now(timezone.utc).isoformat()
    })

    # End Session 1 and start Session 2
    client.post("/api/sessions/end")
    s2 = client.post("/api/sessions/start", json={"food_profile_id": "bananas", "session_name": "Batch 2"}).get_json()["session"]

    latest = client.get("/api/latest").get_json()
    # Active session must have 0 accumulated hours
    assert latest["active_session"]["accumulated_effective_hours"] == 0.0
    assert latest["risk"]["effective_exposure_hours"] == 0.0
    assert latest["active_session"]["session_name"] == "Batch 2"


def test_acknowledge_alert_validation(client):
    # Non-integer alert_id
    res_bad = client.post("/api/alerts/acknowledge", json={"alert_id": "invalid"})
    assert res_bad.status_code == 422

    # Non-existent alert_id
    res_missing = client.post("/api/alerts/acknowledge", json={"alert_id": 99999})
    assert res_missing.status_code == 404


def test_simulator_controls_and_step(client):
    # Set mode
    res_mode = client.post("/api/simulator/mode", json={"mode": "high_temp"})
    assert res_mode.status_code == 200
    assert res_mode.get_json()["mode"] == "high_temp"

    # Step simulation
    res_step = client.post("/api/simulator/step")
    assert res_step.status_code == 200
    step_data = res_step.get_json()
    assert step_data["source"] == "simulator"
    assert step_data["temperature"] > 15.0  # In high_temp mode, temperature is elevated

    # Start and stop background simulator
    res_start = client.post("/api/simulator/start", json={"interval_seconds": 1.0})
    assert res_start.status_code == 200
    assert res_start.get_json()["status"] == "running"

    # Multiple start calls should not create multiple threads
    res_start2 = client.post("/api/simulator/start", json={"interval_seconds": 1.0})
    assert res_start2.status_code == 200

    res_stop = client.post("/api/simulator/stop")
    assert res_stop.status_code == 200
    assert res_stop.get_json()["status"] == "stopped"


def test_history_hours_filtering(client):
    """Verify that ?range=1h filters historical records based on temporal cutoff."""
    now = datetime.now(timezone.utc)
    old_time = (now - timedelta(hours=3)).isoformat()
    recent_time = (now - timedelta(minutes=10)).isoformat()

    # Old reading (3 hours ago)
    client.post("/api/sensor-data", json={"temperature": 13.0, "humidity": 88.0, "gas": 180.0, "device_id": "D1", "timestamp": old_time})
    # Recent reading (10 min ago)
    client.post("/api/sensor-data", json={"temperature": 13.5, "humidity": 88.0, "gas": 185.0, "device_id": "D1", "timestamp": recent_time})

    # Range 1h should only return the recent reading (1 item)
    hist_1h = client.get("/api/history?range=1h").get_json()
    assert hist_1h["count"] == 1

    # Range 24h should return both readings (2 items)
    hist_24h = client.get("/api/history?range=24h").get_json()
    assert hist_24h["count"] == 2


def test_system_mode_and_hardware_status(client):
    """Verify querying and toggling between simulation and hardware operating modes."""
    # GET initial mode
    res = client.get("/api/system/mode")
    assert res.status_code == 200
    data = res.get_json()
    assert "system_mode" in data
    assert "hardware" in data
    assert "lan_ip" in data["hardware"]
    assert "lan_endpoint" in data["hardware"]

    # POST switch to hardware
    res_hw = client.post("/api/system/mode", json={"mode": "hardware"})
    assert res_hw.status_code == 200
    assert res_hw.get_json()["system_mode"] == "hardware"

    # POST switch back to simulation
    res_sim = client.post("/api/system/mode", json={"mode": "simulation"})
    assert res_sim.status_code == 200
    assert res_sim.get_json()["system_mode"] == "simulation"

    # Invalid mode rejection
    res_invalid = client.post("/api/system/mode", json={"mode": "unknown_mode"})
    assert res_invalid.status_code == 400


def test_esp32_telemetry_switches_mode_and_stops_simulator(client):
    """Verify that incoming ESP32 telemetry activates hardware mode and stops simulator."""
    # 1. Start background simulator
    client.post("/api/system/mode", json={"mode": "simulation"})
    res_start = client.post("/api/simulator/start", json={"interval_seconds": 2.0})
    assert res_start.status_code == 200

    # 2. Ingest packet from physical ESP32
    esp32_payload = {
        "temperature": 14.2,
        "humidity": 88.5,
        "gas": 210.0,
        "device_id": "ESP32-UNIT-TEST",
        "source": "esp32"
    }
    res_post = client.post("/api/sensor-data", json=esp32_payload)
    assert res_post.status_code == 201
    post_data = res_post.get_json()
    assert post_data["source"] == "esp32"
    assert post_data["device_id"] == "ESP32-UNIT-TEST"

    # 3. Verify latest state reflects ESP32 online hardware status and stopped simulator
    latest = client.get("/api/latest").get_json()
    assert latest["system_mode"] == "hardware"
    assert latest["hardware"]["is_connected"] is True
    assert latest["hardware"]["status"] == "online"
    assert latest["hardware"]["device_id"] == "ESP32-UNIT-TEST"
    assert latest["simulator"]["is_running"] is False

