"""
app.py
Modular Flask REST API Backend for Smart Food Storage Spoilage Predictor.
Integrates SQLite persistence, the mathematical spoilage risk engine,
session lifecycle management, and a live multi-mode sensor simulator.
"""

import os
import math
from datetime import datetime, timezone, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

import database
from food_profiles import get_default_profiles, get_profile_by_id
from risk_engine import (
    calculate_temperature_risk,
    calculate_humidity_risk,
    calculate_gas_risk,
    calculate_duration_risk,
    calculate_effective_duration_increment,
    calculate_composite_risk,
    classify_risk,
    generate_recommendations
)
from simulator import SensorSimulator, SIMULATION_MODES

# Configure App
app = Flask(__name__)
CORS(app)  # Enable CORS for local Vite development frontend

DB_PATH = os.path.join(os.path.dirname(__file__), "food_storage.db")

# Ensure DB initialized on module load
database.init_db(DB_PATH)


def get_local_lan_ip() -> str:
    """Detect the local machine's LAN IPv4 address for ESP32 configuration."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"


# System Operating State
system_state = {
    "mode": "simulation",  # 'simulation' or 'hardware'
    "last_hardware_reading": None,  # dict with timestamp, device_id, ip_address, reading_id
}


def get_hardware_status() -> dict:
    """Assess whether physical ESP32 telemetry is actively streaming, standby, or offline."""
    now_utc = datetime.now(timezone.utc)
    last_hw = system_state.get("last_hardware_reading")

    # If in-memory state is empty, check database for historical ESP32 packets
    if not last_hw:
        db_hw = database.get_latest_reading_by_source("esp32", DB_PATH)
        if db_hw:
            last_hw = {
                "timestamp": db_hw["timestamp"],
                "device_id": db_hw["device_id"],
                "ip_address": "lan",
                "reading_id": db_hw["id"]
            }

    lan_ip = get_local_lan_ip()
    status_info = {
        "status": "offline",
        "is_connected": False,
        "device_id": None,
        "last_seen": None,
        "seconds_ago": None,
        "lan_ip": lan_ip,
        "lan_endpoint": f"http://{lan_ip}:5000/api/sensor-data"
    }

    if last_hw and last_hw.get("timestamp"):
        try:
            last_dt = datetime.fromisoformat(last_hw["timestamp"].replace("Z", "+00:00"))
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
            seconds_ago = max(0.0, (now_utc - last_dt).total_seconds())
            status_info["last_seen"] = last_hw["timestamp"]
            status_info["device_id"] = last_hw.get("device_id", "ESP32-NODE")
            status_info["seconds_ago"] = round(seconds_ago, 1)

            # Active if received within 45 seconds (3x default 10s sampling interval)
            if seconds_ago <= 45.0:
                status_info["status"] = "online"
                status_info["is_connected"] = True
            else:
                status_info["status"] = "standby"
                status_info["is_connected"] = False
        except Exception:
            status_info["status"] = "standby"

    return status_info


def get_current_profile_dict() -> dict:
    """Helper to get current active session profile or fallback to tomatoes."""
    active_session = database.get_active_session(DB_PATH)
    if active_session and active_session.get("food_profile_id"):
        prof = database.get_food_profile(active_session["food_profile_id"], DB_PATH)
        if prof:
            return prof
    return get_profile_by_id("tomatoes") or list(get_default_profiles().values())[0]


def process_sensor_reading(payload: dict) -> dict:
    """
    Core data processing pipeline:
    Validates, calculates multi-parameter risk, manages duration accumulation,
    persists in SQLite, and evaluates alert trigger conditions.
    Can be called directly by ESP32 HTTP POST or by the internal Simulator.
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload must be a JSON dictionary.")

    # 1. Validation
    try:
        temp = float(payload.get("temperature"))
        humidity = float(payload.get("humidity"))
        gas = float(payload.get("gas"))
    except (TypeError, ValueError):
        raise ValueError("Invalid sensor values: temperature, humidity, and gas must be numeric.")

    if math.isnan(temp) or math.isinf(temp):
        raise ValueError("Temperature value cannot be NaN or Infinity.")
    if math.isnan(humidity) or math.isinf(humidity):
        raise ValueError("Humidity value cannot be NaN or Infinity.")
    if math.isnan(gas) or math.isinf(gas):
        raise ValueError("Gas ADC value cannot be NaN or Infinity.")

    if not (-40.0 <= temp <= 80.0):
        raise ValueError(f"Temperature {temp}°C out of realistic range (-40°C to 80°C).")
    if not (0.0 <= humidity <= 100.0):
        raise ValueError(f"Humidity {humidity}% out of valid range (0% to 100%).")
    if not (0.0 <= gas <= 4095.0):
        raise ValueError(f"Gas ADC {gas} out of valid ADC range (0 to 4095).")

    device_id = str(payload.get("device_id", "UNKNOWN_DEV")).strip() or "UNKNOWN_DEV"
    source = str(payload.get("source", "esp32")).strip().lower()
    if source not in ("esp32", "simulator"):
        source = "simulator" if "sim" in source else "esp32"

    timestamp_str = payload.get("timestamp")
    now_utc = datetime.now(timezone.utc)
    if not timestamp_str or not isinstance(timestamp_str, str):
        current_time = now_utc
        timestamp_str = now_utc.isoformat()
    else:
        try:
            current_time = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            if current_time.tzinfo is None:
                current_time = current_time.replace(tzinfo=timezone.utc)
            # Guard against future timestamps (>15 min ahead) to avoid skewing exposure time
            if current_time > now_utc + timedelta(minutes=15):
                current_time = now_utc
                timestamp_str = now_utc.isoformat()
            else:
                timestamp_str = current_time.isoformat()
        except Exception:
            current_time = now_utc
            timestamp_str = now_utc.isoformat()

    # 2. Get active session & profile
    active_session = database.get_active_session(DB_PATH)
    session_id = active_session["id"] if active_session else None

    if active_session and active_session.get("food_profile_id"):
        profile = database.get_food_profile(active_session["food_profile_id"], DB_PATH) or get_current_profile_dict()
    else:
        profile = get_current_profile_dict()

    profile_id = profile["id"]

    # 3. Calculate instantaneous component risks
    ts = calculate_temperature_risk(temp, profile)
    hs = calculate_humidity_risk(humidity, profile)
    gs = calculate_gas_risk(gas, profile)

    # 4. Duration accumulation
    ideal_shelf_life = float(profile.get("ideal_shelf_life_hours", 168.0))
    alpha = float(profile.get("stress_multiplier_alpha", 1.5))

    accumulated_hours = 0.0
    if active_session:
        last_time_str = active_session.get("last_reading_time")
        delta_hours = 0.0
        if last_time_str:
            try:
                last_time = datetime.fromisoformat(last_time_str.replace("Z", "+00:00"))
                if last_time.tzinfo is None:
                    last_time = last_time.replace(tzinfo=timezone.utc)
                delta_seconds = max(0.0, (current_time - last_time).total_seconds())
                delta_hours = delta_seconds / 3600.0
            except Exception:
                delta_hours = 0.0
        else:
            delta_hours = 0.0

        # Calculate stress-weighted exposure increment
        eff_inc = calculate_effective_duration_increment(delta_hours, ts, hs, alpha=alpha)
        database.update_session_duration(session_id, eff_inc, timestamp_str, DB_PATH)
        accumulated_hours = float(active_session.get("accumulated_effective_hours", 0.0)) + eff_inc

    ds = calculate_duration_risk(accumulated_hours, ideal_shelf_life)

    # 5. Calculate composite risk
    weights = {
        "weight_temp": profile.get("weight_temp", 0.30),
        "weight_humidity": profile.get("weight_humidity", 0.25),
        "weight_gas": profile.get("weight_gas", 0.25),
        "weight_duration": profile.get("weight_duration", 0.20),
    }
    composite_risk = calculate_composite_risk(ts, hs, gs, ds, weights)
    category, color_code = classify_risk(composite_risk)
    recommendation = generate_recommendations(category, profile, ts, hs, gs, ds, temp, humidity, gas)

    # 6. Alert management (based on previous evaluated risk category for this session)
    SEVERITY_ORDER = {"Low": 0, "Moderate": 1, "High": 2, "Critical": 3}
    prev_category = database.get_previous_risk_for_session(session_id, DB_PATH) or "Low"
    prev_order = SEVERITY_ORDER.get(prev_category, 0)
    current_order = SEVERITY_ORDER.get(category, 0)

    alert_created = None
    if current_order > prev_order and current_order > 0:
        alert_msg = f"Storage risk elevated to {category.upper()} ({composite_risk:.1f}%). {recommendation}"
        alert_id = database.insert_alert(
            severity=category,
            message=alert_msg,
            risk_score=composite_risk,
            previous_severity=prev_category,
            timestamp=timestamp_str,
            session_id=session_id,
            db_path=DB_PATH
        )
        alert_created = {
            "id": alert_id,
            "severity": category,
            "message": alert_msg,
            "risk_score": composite_risk,
            "timestamp": timestamp_str
        }

    # 7. Persist sensor reading and risk score
    reading_id = database.insert_sensor_reading(
        device_id=device_id,
        source=source,
        temperature=temp,
        humidity=humidity,
        gas=gas,
        timestamp=timestamp_str,
        session_id=session_id,
        db_path=DB_PATH
    )

    # Track hardware telemetry source and auto-stop simulator if hardware is active
    if source == "esp32":
        system_state["mode"] = "hardware"
        client_ip = "lan"
        try:
            if request and hasattr(request, "remote_addr"):
                client_ip = request.remote_addr or "lan"
        except Exception:
            client_ip = "lan"

        system_state["last_hardware_reading"] = {
            "timestamp": timestamp_str,
            "device_id": device_id,
            "ip_address": client_ip,
            "reading_id": reading_id
        }
        if simulator.is_running:
            simulator.stop()

    database.insert_risk_history(
        reading_id=reading_id,
        session_id=session_id,
        food_profile_id=profile_id,
        temp_score=ts,
        humidity_score=hs,
        gas_score=gs,
        duration_score=ds,
        composite_risk=composite_risk,
        risk_category=category,
        recommendation=recommendation,
        timestamp=timestamp_str,
        db_path=DB_PATH
    )

    return {
        "status": "success",
        "reading_id": reading_id,
        "temperature": temp,
        "humidity": humidity,
        "gas": gas,
        "source": source,
        "device_id": device_id,
        "timestamp": timestamp_str,
        "food_profile": {
            "id": profile["id"],
            "name": profile["name"],
            "temp_min": profile["temp_min"],
            "temp_max": profile["temp_max"],
            "humidity_min": profile["humidity_min"],
            "humidity_max": profile["humidity_max"],
        },
        "risk": {
            "composite_score": composite_risk,
            "category": category,
            "color": color_code,
            "components": {
                "temp_score": ts,
                "humidity_score": hs,
                "gas_score": gs,
                "duration_score": ds
            },
            "recommendation": recommendation,
            "effective_exposure_hours": round(accumulated_hours, 2),
            "ideal_shelf_life_hours": ideal_shelf_life
        },
        "session": {
            "session_id": session_id,
            "session_name": active_session.get("session_name") if active_session else "Unmanaged Default"
        },
        "new_alert": alert_created
    }


# Instantiate Simulator with direct ingestion callback
simulator = SensorSimulator(callback=process_sensor_reading)


# --- REST API Endpoints ---

@app.route("/api/health", methods=["GET"])
def health():
    """Health status and system overview."""
    active_session = database.get_active_session(DB_PATH)
    return jsonify({
        "status": "online",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": "connected",
        "system_mode": system_state["mode"],
        "hardware": get_hardware_status(),
        "active_session": active_session,
        "simulator": {
            "is_running": simulator.is_running,
            "current_mode": simulator.get_mode(),
            "mode_label": SIMULATION_MODES.get(simulator.get_mode(), "Unknown"),
            "available_modes": SIMULATION_MODES
        }
    }), 200


@app.route("/api/sensor-data", methods=["POST"])
def sensor_data():
    """
    Ingest sensor readings from hardware (ESP32) or simulator.
    Expects JSON: {temperature, humidity, gas, device_id, timestamp?, source?}
    """
    payload = request.get_json(silent=True)
    if payload is None:
        return jsonify({"error": "Content-Type must be application/json with valid JSON body"}), 422

    if not isinstance(payload, dict):
        return jsonify({"error": "Payload must be a JSON object"}), 422

    required = ["temperature", "humidity", "gas"]
    missing = [f for f in required if f not in payload]
    if missing:
        return jsonify({"error": f"Missing required fields: {', '.join(missing)}"}), 422

    try:
        result = process_sensor_reading(payload)
        return jsonify(result), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 422
    except Exception as e:
        return jsonify({"error": f"Internal processing error: {str(e)}"}), 500


@app.route("/api/latest", methods=["GET"])
def get_latest():
    """Get the most recent sensor reading, risk scores, and active session status."""
    latest = database.get_latest_state(DB_PATH)
    active_session = database.get_active_session(DB_PATH)
    current_profile = get_current_profile_dict()

    effective_hours = round(active_session["accumulated_effective_hours"], 2) if active_session else (round(latest.get("accumulated_effective_hours", 0.0) or 0.0, 2) if latest else 0.0)
    ideal_shelf_life = float(active_session["ideal_shelf_life_hours"]) if active_session else float(current_profile.get("ideal_shelf_life_hours", 168.0))

    if not latest:
        # Return fallback empty state with profile information
        return jsonify({
            "has_data": False,
            "system_mode": system_state["mode"],
            "hardware": get_hardware_status(),
            "reading": None,
            "risk": None,
            "active_session": active_session,
            "active_profile": current_profile,
            "simulator": {
                "is_running": simulator.is_running,
                "current_mode": simulator.get_mode(),
                "mode_label": SIMULATION_MODES.get(simulator.get_mode(), "Unknown")
            }
        }), 200

    # Format structured output
    category, color_code = classify_risk(latest.get("composite_risk", 0.0))
    return jsonify({
        "has_data": True,
        "system_mode": system_state["mode"],
        "hardware": get_hardware_status(),
        "reading": {
            "id": latest["reading_id"],
            "temperature": latest["temperature"],
            "humidity": latest["humidity"],
            "gas": latest["gas"],
            "device_id": latest["device_id"],
            "source": latest["source"],
            "timestamp": latest["timestamp"]
        },
        "risk": {
            "composite_score": latest["composite_risk"],
            "category": latest["risk_category"] or category,
            "color": color_code,
            "components": {
                "temp_score": latest["temp_score"],
                "humidity_score": latest["humidity_score"],
                "gas_score": latest["gas_score"],
                "duration_score": latest["duration_score"]
            },
            "recommendation": latest["recommendation"],
            "effective_exposure_hours": effective_hours,
            "ideal_shelf_life_hours": ideal_shelf_life
        },
        "active_session": active_session,
        "active_profile": current_profile,
        "simulator": {
            "is_running": simulator.is_running,
            "current_mode": simulator.get_mode(),
            "mode_label": SIMULATION_MODES.get(simulator.get_mode(), "Unknown")
        }
    }), 200


@app.route("/api/history", methods=["GET"])
def get_history_telemetry():
    """
    Get historical sensor and risk telemetry.
    Supports ?range=1h | 24h | 7d | all, ?limit=500, and optional ?session_id=1
    """
    range_param = request.args.get("range", "24h").lower()
    limit = int(request.args.get("limit", 300))
    session_id_arg = request.args.get("session_id")
    session_id = int(session_id_arg) if session_id_arg and session_id_arg.isdigit() else None

    if range_param == "1h":
        hours = 1.0
    elif range_param == "7d":
        hours = 168.0
    elif range_param == "all":
        hours = None
    else:  # default 24h
        hours = 24.0

    history = database.get_history(hours=hours, limit=limit, session_id=session_id, db_path=DB_PATH)
    return jsonify({
        "range": range_param,
        "count": len(history),
        "data": history
    }), 200


@app.route("/api/alerts", methods=["GET"])
def get_alerts_list():
    """Retrieve historical alert events."""
    limit = int(request.args.get("limit", 50))
    alerts = database.get_alerts(limit=limit, db_path=DB_PATH)
    return jsonify({
        "count": len(alerts),
        "alerts": alerts
    }), 200


@app.route("/api/alerts/acknowledge", methods=["POST"])
def acknowledge_alert_endpoint():
    """Acknowledge a specific alert."""
    payload = request.get_json(silent=True) or {}
    raw_id = payload.get("alert_id")
    if raw_id is None:
        return jsonify({"error": "Missing alert_id"}), 400

    try:
        alert_id = int(raw_id)
    except (TypeError, ValueError):
        return jsonify({"error": "alert_id must be an integer"}), 422

    success = database.acknowledge_alert(alert_id, db_path=DB_PATH)
    if not success:
        return jsonify({"error": f"Alert {alert_id} not found"}), 404
    return jsonify({"success": True, "alert_id": alert_id}), 200


@app.route("/api/food-profiles", methods=["GET"])
def food_profiles_list():
    """Retrieve all available food commodity storage profiles."""
    profiles = database.get_all_food_profiles(DB_PATH)
    return jsonify({
        "count": len(profiles),
        "profiles": profiles
    }), 200


@app.route("/api/sessions", methods=["GET"])
def sessions_list():
    """Retrieve all storage sessions (active and past)."""
    limit = int(request.args.get("limit", 50))
    sessions = database.get_all_sessions(limit=limit, db_path=DB_PATH)
    active = database.get_active_session(DB_PATH)
    return jsonify({
        "active_session": active,
        "sessions": sessions
    }), 200


@app.route("/api/sessions/start", methods=["POST"])
def start_storage_session():
    """
    Start a new storage session with a selected food profile.
    Payload: { food_profile_id: "tomatoes", session_name?: "Tomatoes Batch #1" }
    """
    payload = request.get_json() or {}
    profile_id = payload.get("food_profile_id")
    if not profile_id:
        return jsonify({"error": "Missing food_profile_id"}), 400

    profile = database.get_food_profile(profile_id, DB_PATH)
    if not profile:
        return jsonify({"error": f"Unknown food profile '{profile_id}'"}), 404

    session_name = payload.get("session_name")
    session = database.start_session(food_profile_id=profile_id, session_name=session_name, db_path=DB_PATH)

    return jsonify({
        "status": "session_started",
        "session": session
    }), 201


@app.route("/api/sessions/end", methods=["POST"])
def end_storage_session():
    """End the currently active storage session."""
    ended = database.end_active_session(DB_PATH)
    if not ended:
        return jsonify({"status": "no_active_session"}), 200

    return jsonify({
        "status": "session_ended",
        "session": ended
    }), 200


# --- System Operating Mode Endpoints ---

@app.route("/api/system/mode", methods=["GET", "POST"])
def system_mode_endpoint():
    """Get or toggle application operating mode ('simulation' vs 'hardware')."""
    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        req_mode = str(payload.get("mode", "")).strip().lower()
        if req_mode not in ("simulation", "hardware"):
            return jsonify({"error": "Invalid mode. Must be 'simulation' or 'hardware'."}), 400

        system_state["mode"] = req_mode
        if req_mode == "hardware" and simulator.is_running:
            simulator.stop()

    return jsonify({
        "status": "success",
        "system_mode": system_state["mode"],
        "hardware": get_hardware_status(),
        "simulator": {
            "is_running": simulator.is_running,
            "current_mode": simulator.get_mode(),
            "mode_label": SIMULATION_MODES.get(simulator.get_mode(), "Unknown")
        }
    }), 200


# --- Simulator Endpoints ---

@app.route("/api/simulator/mode", methods=["POST"])
def simulator_set_mode():
    """Set the simulation condition mode."""
    payload = request.get_json() or {}
    mode = payload.get("mode")
    if not mode:
        return jsonify({"error": "Missing mode"}), 400

    try:
        new_mode = simulator.set_mode(mode)
        return jsonify({
            "mode": new_mode,
            "label": SIMULATION_MODES.get(new_mode)
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 422


@app.route("/api/simulator/start", methods=["POST"])
def simulator_start():
    """Start automated periodic sensor generation."""
    payload = request.get_json(silent=True) or {}
    try:
        interval = float(payload.get("interval_seconds", 3.0))
        interval = max(1.0, min(60.0, interval))
    except (TypeError, ValueError):
        interval = 3.0

    system_state["mode"] = "simulation"
    simulator.start(get_active_profile_fn=get_current_profile_dict, interval_seconds=interval)
    return jsonify({
        "status": "running",
        "interval_seconds": simulator.interval_seconds,
        "mode": simulator.get_mode(),
        "mode_label": SIMULATION_MODES.get(simulator.get_mode()),
        "system_mode": system_state["mode"]
    }), 200


@app.route("/api/simulator/stop", methods=["POST"])
def simulator_stop():
    """Stop automated periodic sensor generation."""
    simulator.stop()
    return jsonify({
        "status": "stopped",
        "mode": simulator.get_mode()
    }), 200


@app.route("/api/simulator/step", methods=["POST"])
def simulator_step():
    """Generate and inject a single simulated reading immediately."""
    profile = get_current_profile_dict()
    payload = simulator.generate_single_payload(profile)
    result = process_sensor_reading(payload)
    return jsonify(result), 200


if __name__ == "__main__":
    # Ensure DB initialized
    database.init_db(DB_PATH)
    print("Starting Smart Food Storage Spoilage Predictor API on http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
