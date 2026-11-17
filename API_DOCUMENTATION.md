# REST API SPECIFICATION
## Smart Food Storage Spoilage Predictor - Backend Interface

**Base URL:** `http://<BACKEND_HOST>:5000/api`  
**Default Local URL:** `http://127.0.0.1:5000/api`  
**LAN IPv4 Example:** `http://192.168.0.101:5000/api`  
**Content-Type:** `application/json`  
**Version:** 1.0.0 (Production Release)

---

## 1. Overview & Architecture

The Smart Food Storage Spoilage Predictor backend provides a stateless RESTful interface over HTTP. It acts as the central ingestion point for edge IoT telemetry (from physical ESP32 nodes or internal sensor emulators), runs the mathematical spoilage risk engine, evaluates multi-tier alert thresholds, and manages storage session lifecycle states in a local SQLite database with Write-Ahead Logging (WAL).

---

## 2. Standard HTTP Status Codes

| Code | Status | Meaning |
|---|---|---|
| **200** | `OK` | Request succeeded; response contains requested data. |
| **201** | `Created` | Telemetry successfully ingested, risk computed, and persisted. |
| **400** | `Bad Request` | Malformed syntax or missing query parameters. |
| **404** | `Not Found` | Resource (e.g. food profile ID or alert ID) does not exist. |
| **409** | `Conflict` | State conflict (e.g. starting simulator while hardware mode is active). |
| **422** | `Unprocessable Entity` | Validation error (e.g. NaN/Inf values, out-of-range sensor readings). |
| **500** | `Internal Server Error` | Unhandled backend exception. |

---

## 3. Endpoints Reference

### 3.1 Ingestion & Telemetry

#### `POST /api/sensor-data`
**Description:** Primary ingestion endpoint for environmental readings from ESP32 or simulator. Evaluates multi-parameter risk scores, accumulates session duration stress, triggers alerts if risk tier escalates, and persists records in SQLite.

* **Headers:** `Content-Type: application/json`
* **Request Body:**
```json
{
  "temperature": 14.2,
  "humidity": 88.5,
  "gas": 245.0,
  "device_id": "ESP32-FOOD-001",
  "source": "esp32",
  "timestamp": "2026-11-15T10:15:30.000000+00:00"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `temperature` | float | **Yes** | Ambient temperature in °C (valid range: $-40.0$ to $80.0$). Rejects NaN/Inf. |
| `humidity` | float | **Yes** | Relative humidity in % (valid range: $0.0$ to $100.0$). Rejects NaN/Inf. |
| `gas` | float | **Yes** | MQ-135 ADC count (valid range: $0.0$ to $4095.0$). Rejects NaN/Inf. |
| `device_id` | string | No | Hardware node identifier (defaults to `UNKNOWN_DEV`). |
| `source` | string | No | Telemetry origin (`"esp32"` or `"simulator"`, defaults to `"esp32"`). |
| `timestamp` | string | No | ISO-8601 UTC timestamp. If omitted, server defaults to `now_utc`. Clamped if >15m in future. |

* **Success Response (`201 Created`):**
```json
{
  "status": "success",
  "reading_id": 142,
  "temperature": 14.2,
  "humidity": 88.5,
  "gas": 245.0,
  "source": "esp32",
  "device_id": "ESP32-FOOD-001",
  "timestamp": "2026-11-15T10:15:30+00:00",
  "food_profile": {
    "id": "rice",
    "name": "Rice",
    "temp_min": 12.0,
    "temp_max": 15.0,
    "humidity_min": 85.0,
    "humidity_max": 90.0
  },
  "risk": {
    "composite_score": 14.6,
    "category": "Low",
    "color": "green",
    "components": {
      "temp_score": 0.0,
      "humidity_score": 0.0,
      "gas_score": 29.5,
      "duration_score": 36.4
    },
    "recommendation": "Storage conditions are optimal. Produce is dormant.",
    "effective_exposure_hours": 61.2,
    "ideal_shelf_life_hours": 168.0
  },
  "session": {
    "session_id": 3,
    "session_name": "Rice Storage Chamber Batch A"
  },
  "new_alert": null
}
```

* **Error Response (`422 Unprocessable Entity`):**
```json
{
  "error": "Temperature value cannot be NaN or Infinity."
}
```

---

#### `GET /api/latest`
**Description:** Retrieves the latest sensor reading, instantaneous component risk scores, active storage session state, hardware connection metadata, and system operating mode.

* **Success Response (`200 OK`):**
```json
{
  "has_data": true,
  "system_mode": "hardware",
  "hardware": {
    "status": "online",
    "is_connected": true,
    "device_id": "ESP32-FOOD-001",
    "last_seen": "2026-11-15T10:15:30+00:00",
    "seconds_ago": 4.2,
    "lan_ip": "192.168.0.101",
    "lan_endpoint": "http://192.168.0.101:5000/api/sensor-data"
  },
  "reading": {
    "id": 142,
    "temperature": 14.2,
    "humidity": 88.5,
    "gas": 245.0,
    "device_id": "ESP32-FOOD-001",
    "source": "esp32",
    "timestamp": "2026-11-15T10:15:30+00:00"
  },
  "risk": {
    "composite_score": 14.6,
    "category": "Low",
    "color": "green",
    "components": {
      "temp_score": 0.0,
      "humidity_score": 0.0,
      "gas_score": 29.5,
      "duration_score": 36.4
    },
    "recommendation": "Storage conditions are optimal. Produce is dormant.",
    "effective_exposure_hours": 61.2,
    "ideal_shelf_life_hours": 168.0
  },
  "active_session": {
    "id": 3,
    "session_name": "Rice Storage Chamber Batch A",
    "food_profile_id": "rice",
    "food_name": "Rice",
    "start_time": "2026-11-15T08:00:00+00:00",
    "is_active": 1,
    "accumulated_effective_hours": 61.2,
    "total_readings_count": 48
  },
  "active_profile": {
    "id": "rice",
    "name": "Rice",
    "temp_min": 12.0,
    "temp_max": 15.0,
    "humidity_min": 85.0,
    "humidity_max": 90.0,
    "ideal_shelf_life_hours": 168.0,
    "gas_baseline": 180.0,
    "gas_threshold": 400.0
  },
  "simulator": {
    "is_running": false,
    "current_mode": "normal",
    "mode_label": "1. Normal Conditions"
  }
}
```

---

#### `GET /api/history`
**Description:** Retrieves time-series telemetry points for Recharts graph visualization. Filterable by time range and session.

* **Query Parameters:**
  * `range`: `'1h'` | `'24h'` | `'7d'` | `'all'` (default: `'24h'`)
  * `limit`: Integer (default: `300`, maximum: `1000`)
  * `session_id`: Optional integer to isolate historical telemetry by session.
* **Success Response (`200 OK`):**
```json
{
  "range": "24h",
  "count": 120,
  "data": [
    {
      "id": 1,
      "timestamp": "2026-11-15T09:00:00+00:00",
      "temperature": 13.5,
      "humidity": 87.2,
      "gas": 195.0,
      "source": "esp32",
      "composite_risk": 11.2,
      "temp_score": 0.0,
      "humidity_score": 0.0,
      "gas_score": 6.8,
      "duration_score": 12.5,
      "risk_category": "Low",
      "food_name": "Rice"
    }
  ]
}
```

---

### 3.2 System Health & Operating Mode

#### `GET /api/health`
**Description:** System diagnostics, database connectivity check, and hardware node status.

* **Success Response (`200 OK`):**
```json
{
  "status": "online",
  "timestamp": "2026-11-15T10:20:00+00:00",
  "database": "connected",
  "system_mode": "hardware",
  "hardware": {
    "status": "online",
    "is_connected": true,
    "device_id": "ESP32-FOOD-001",
    "last_seen": "2026-11-15T10:15:30+00:00",
    "seconds_ago": 12.5,
    "lan_ip": "192.168.0.101",
    "lan_endpoint": "http://192.168.0.101:5000/api/sensor-data"
  },
  "active_session": { "id": 3, "session_name": "Rice Storage Batch A" },
  "simulator": {
    "is_running": false,
    "current_mode": "normal",
    "mode_label": "1. Normal Conditions"
  }
}
```

---

#### `GET /api/system/mode` & `POST /api/system/mode`
**Description:** Get or toggle application operating mode (`"simulation"` vs `"hardware"`). Switching to `"hardware"` automatically halts the synthetic simulator loop to prevent telemetry collisions.

* **POST Request Body:**
```json
{
  "mode": "simulation"
}
```
* **Success Response (`200 OK`):**
```json
{
  "status": "success",
  "system_mode": "simulation",
  "hardware": {
    "status": "standby",
    "is_connected": false,
    "device_id": "ESP32-FOOD-001",
    "lan_ip": "192.168.0.101"
  },
  "simulator": {
    "is_running": false,
    "current_mode": "normal",
    "mode_label": "1. Normal Conditions"
  }
}
```

---

### 3.3 Storage Session Management

#### `GET /api/sessions`
**Description:** Returns active session and list of historical storage sessions.

* **Success Response (`200 OK`):**
```json
{
  "active_session": {
    "id": 3,
    "session_name": "Rice Storage Batch A",
    "food_profile_id": "rice",
    "food_name": "Rice",
    "start_time": "2026-11-15T08:00:00+00:00",
    "is_active": 1,
    "accumulated_effective_hours": 12.5,
    "total_readings_count": 48
  },
  "sessions": [ ... ]
}
```

#### `POST /api/sessions/start`
**Description:** Starts a new storage session. Automatically terminates any existing active session.

* **Request Body:**
```json
{
  "food_profile_id": "fruits_and_snacks",
  "session_name": "Fresh Produce & Snack Storage Batch 1"
}
```
* **Success Response (`201 Created`):**
```json
{
  "status": "started",
  "session": {
    "id": 4,
    "session_name": "Fresh Produce & Snack Storage Batch 1",
    "food_profile_id": "fruits_and_snacks",
    "start_time": "2026-11-15T10:30:00+00:00",
    "is_active": 1,
    "accumulated_effective_hours": 0.0,
    "total_readings_count": 0
  }
}
```

#### `POST /api/sessions/end`
**Description:** Closes the active storage session and records its terminal timestamp.

* **Success Response (`200 OK`):**
```json
{
  "status": "ended",
  "session": {
    "id": 3,
    "is_active": 0,
    "end_time": "2026-11-15T10:30:00+00:00"
  }
}
```

---

### 3.4 Food Modes & Commodity Profiles

#### `GET /api/food-profiles`
**Description:** Retrieves all three supported commodity storage modes (`normal`, `fruits_and_snacks`, `rice`), including their calibrated psychrometric envelopes, gas thresholds, and demonstration risk adjustments.

* **Success Response (`200 OK`):**
```json
{
  "count": 3,
  "profiles": [
    {
      "id": "normal",
      "name": "Normal",
      "category": "Shelf-Stable Goods",
      "temp_min": 15.0,
      "temp_max": 22.0,
      "humidity_min": 40.0,
      "humidity_max": 65.0,
      "ideal_shelf_life_hours": 336.0,
      "gas_baseline": 180.0,
      "gas_threshold": 400.0,
      "mode_adjustment": -15.0
    },
    {
      "id": "fruits_and_snacks",
      "name": "Fruits and Snacks",
      "category": "Fresh Produce / Perishable",
      "temp_min": 3.0,
      "temp_max": 8.0,
      "humidity_min": 85.0,
      "humidity_max": 90.0,
      "ideal_shelf_life_hours": 672.0,
      "gas_baseline": 180.0,
      "gas_threshold": 400.0,
      "mode_adjustment": -10.0
    },
    {
      "id": "rice",
      "name": "Rice",
      "category": "Prepared Grain (TCS Perishable)",
      "temp_min": 1.0,
      "temp_max": 4.0,
      "humidity_min": 85.0,
      "humidity_max": 95.0,
      "ideal_shelf_life_hours": 96.0,
      "gas_baseline": 180.0,
      "gas_threshold": 380.0,
      "mode_adjustment": 5.0
    }
  ]
}
```

#### `GET /api/food-mode` & `POST /api/food-mode`
**Description:** Gets the current active food mode or immediately switches modes. When switching modes, the backend immediately recalculates the displayed score from the latest available base score without accumulating adjustments.

* **Formula:** `display_score = clamp(base_risk_score + mode_adjustment, 0, 100)`
* **POST Request Body:**
```json
{
  "mode": "fruits_and_snacks"
}
```
* **Success Response (`200 OK`):**
```json
{
  "status": "mode_updated",
  "active_mode": "fruits_and_snacks",
  "mode_name": "Fruits and Snacks",
  "mode_adjustment": -10.0,
  "session": {
    "id": 5,
    "session_name": "Fruits and Snacks Monitoring Session",
    "food_profile_id": "fruits_and_snacks",
    "is_active": 1
  }
}
```

---

### 3.5 Alerts Management

#### `GET /api/alerts`
**Description:** Retrieves historical and unacknowledged alerts sorted chronologically descending.

* **Success Response (`200 OK`):**
```json
{
  "count": 2,
  "alerts": [
    {
      "id": 5,
      "session_id": 3,
      "severity": "High",
      "message": "Storage risk elevated to HIGH (68.4%). Temperature elevated (+6.5°C). Relocate produce.",
      "risk_score": 68.4,
      "previous_severity": "Moderate",
      "timestamp": "2026-11-15T09:45:10+00:00",
      "acknowledged": 0
    }
  ]
}
```

#### `POST /api/alerts/acknowledge`
**Description:** Marks an alert as reviewed by an operator.

* **Request Body:**
```json
{
  "alert_id": 5
}
```
* **Success Response (`200 OK`):**
```json
{
  "success": true,
  "alert_id": 5
}
```

---

### 3.5 Sensor Simulator Controls

#### `POST /api/simulator/mode`
**Description:** Sets the active microclimate simulation condition.
* **Options:** `'normal'` | `'high_temp'` | `'high_humidity'` | `'elevated_gas'` | `'combined_stress'`
* **Request Body:** `{ "mode": "elevated_gas" }`
* **Success Response (`200 OK`):** `{ "mode": "elevated_gas", "label": "4. Elevated Gas" }`

#### `POST /api/simulator/start`
**Description:** Starts background automated synthetic telemetry streaming.
* **Request Body:** `{ "interval_seconds": 3.5 }`
* **Success Response (`200 OK`):** `{ "status": "running", "interval_seconds": 3.5, "mode": "normal" }`

#### `POST /api/simulator/stop`
**Description:** Halts background automated telemetry generator.
* **Success Response (`200 OK`):** `{ "status": "stopped" }`

#### `POST /api/simulator/step`
**Description:** Injects a single synthetic reading immediately for step-by-step verification.
* **Success Response (`200 OK`):** Full ingestion payload identical to `POST /api/sensor-data`.

---

## 4. ESP32 Arduino C++ Integration Example

Below is the production C++ code utilized by the ESP32 firmware to post readings and parse risk categories:

```cpp
#include <WiFi.h>
#include <HTTPClient.h>

void postTelemetry(float temp, float hum, float gas) {
  if (WiFi.status() != WL_CONNECTED) return;

  HTTPClient http;
  String url = "http://192.168.0.101:5000/api/sensor-data";
  http.begin(url);
  http.setTimeout(5000);
  http.addHeader("Content-Type", "application/json");

  String payload = "{";
  payload += "\"temperature\":" + String(temp, 2) + ",";
  payload += "\"humidity\":" + String(hum, 2) + ",";
  payload += "\"gas\":" + String(gas, 1) + ",";
  payload += "\"device_id\":\"ESP32-FOOD-001\",";
  payload += "\"source\":\"esp32\"";
  payload += "}";

  int httpCode = http.POST(payload);
  if (httpCode == 201 || httpCode == 200) {
    String response = http.getString();

    // 1. Extract backend-adjusted composite score (Single Source of Truth)
    float adjustedScore = 0.0f;
    int scoreIdx = response.indexOf("\"composite_score\":");
    if (scoreIdx != -1) {
      int sStart = scoreIdx + 18;
      int sEnd = response.indexOf(",", sStart);
      if (sEnd == -1) sEnd = response.indexOf("}", sStart);
      if (sEnd != -1) adjustedScore = response.substring(sStart, sEnd).toFloat();
    }

    // 2. Drive physical status LEDs directly based on backend adjusted score:
    //    0–30: Green LED ON (Safe)
    //    >30 and <=50: Blue LED ON (Moderate Warning)
    //    >50: Red LED ON (Elevated / Critical Danger)
    if (adjustedScore <= 30.0f) {
      digitalWrite(LED_GREEN, HIGH); digitalWrite(LED_BLUE, LOW);  digitalWrite(LED_RED, LOW);
    } else if (adjustedScore <= 50.0f) {
      digitalWrite(LED_GREEN, LOW);  digitalWrite(LED_BLUE, HIGH); digitalWrite(LED_RED, LOW);
    } else {
      digitalWrite(LED_GREEN, LOW);  digitalWrite(LED_BLUE, LOW);  digitalWrite(LED_RED, HIGH);
    }
    Serial.printf("[SYNC] Final Adjusted Score: %.1f%%\n", adjustedScore);
  }
  http.end();
}
```
