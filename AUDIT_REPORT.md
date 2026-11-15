# ENGINEERING AUDIT, TESTING & BUG FIXING REPORT
## Project: Smart Food Storage Spoilage Predictor (v1.0.0)
**Date:** November 15, 2026  
**Auditor Roles:** Senior Software Engineer, IoT Systems Architect, QA Lead Engineer  
**Audit Scope:** Full codebase audit covering backend algorithms, SQLite durability, API validation, simulator stability, React frontend state management, Recharts visualization fidelity, and Windows execution scripts.

---

## 1. Actual Bugs Identified & Verified

During this rigorous audit, six actual bugs and edge cases were discovered, verified with reproducible tests, and systematically resolved:

| ID | Component | Severity | Description | Status |
|---|---|---|---|---|
| **BUG-01** | `app.py` / `database.py` | **High** | Alert suppression after recovery: lookup queried global `alerts` table rather than session's previous state, suppressing real subsequent escalations. | **Fixed & Verified** |
| **BUG-02** | `app.py` / `database.py` | **Medium-High** | Session exposure leakage: `GET /api/latest` pulled `accumulated_effective_hours` from the latest sensor reading's session rather than the active session. | **Fixed & Verified** |
| **BUG-03** | `database.py` | **Medium** | Historical temporal filtering failure: `get_history(hours)` ignored `hours` in the SQL query, returning the same records regardless of `1h`/`24h`/`7d` range. | **Fixed & Verified** |
| **BUG-04** | `database.py` | **Medium** | Out-of-order timestamp exposure corruption: `update_session_duration` unconditionally set `last_reading_time = ?`, allowing older timestamps to wind time backwards. | **Fixed & Verified** |
| **BUG-05** | `app.py` | **Medium** | Input validation bypass: `float('nan')` and `float('inf')` bypassed numeric checks; malformed JSON raised unhandled exceptions. | **Fixed & Verified** |
| **BUG-06** | `HistoricalAnalytics.tsx` | **Medium** | Recharts Y-axis domain clipping: auto-domains on Temperature and Gas charts ignored reference areas and threshold lines when readings had narrow ranges. | **Fixed & Verified** |
| **BUG-07** | `start.bat` | **Medium** | Windows batch syntax failure: quotation escaping bug (`\"`) and nested `cd /d` inside quotes with path spaces caused startup crashes. | **Fixed & Verified** |

---

## 2. Root Cause Analysis

### BUG-01: Alert Escalation Suppression After Recovery
* **Root Cause**: `app.py` queried `database.get_latest_alert()`. If a past reading triggered a `High` alert, the `alerts` table's latest row was `High`. If conditions subsequently normalized to `Low` and later elevated to `Moderate` or `High` again, `current_order > prev_order` evaluated to `False` ($1 > 2$ or $2 > 2$), permanently muting genuine future alerts.
* **Fix**: Implemented `database.get_previous_risk_for_session(session_id)` which queries the *immediate previous reading's risk category* for the active session. When conditions normalize, the active baseline drops to `Low`. Any subsequent escalation accurately dispatches a new alert.

### BUG-02: Exposure Hours Leaking Across Sessions in `GET /api/latest`
* **Root Cause**: `database.get_latest_state()` joined `sensor_readings` with `storage_sessions` using the latest reading's `session_id`. When a user ended Session #1 (e.g., 18.5 hours accumulated) and started Session #2, before any reading arrived for Session #2, `GET /api/latest` returned Session #1's accumulated hours under `risk.effective_exposure_hours`.
* **Fix**: In `app.py`, `effective_exposure_hours` is now strictly sourced from `active_session["accumulated_effective_hours"]` whenever an active session is running, guaranteeing $0.0\text{ hrs}$ at batch inception.

### BUG-03: `GET /api/history` Ignored Temporal Range Filter
* **Root Cause**: In `database.py`, `get_history(hours, limit)` received `hours` (1.0, 24.0, 168.0) from the API query parameter `?range=1h|24h|7d`, but the SQL statement lacked a `WHERE r.timestamp >= ?` clause.
* **Fix**: Added dynamic ISO-8601 UTC timestamp cutoff calculation: `cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()`, ensuring `1h`, `24h`, and `7d` queries return genuinely time-bounded telemetry.

### BUG-04: Out-of-Order Timestamp Duration Overcounting
* **Root Cause**: In `database.py`, `update_session_duration()` unconditionally updated `last_reading_time = reading_time`. If an out-of-order packet arrived with an earlier timestamp, `last_reading_time` moved backwards, causing the next reading to overcount elapsed time.
* **Fix**: Implemented conditional SQL assignment:
  ```sql
  SET last_reading_time = CASE
      WHEN last_reading_time IS NULL OR ? > last_reading_time THEN ?
      ELSE last_reading_time
  END
  ```
  Guarantees that `last_reading_time` is strictly monotonically non-decreasing.

### BUG-05: Non-Finite Numeric Values and Timestamp Injection
* **Root Cause**: Python's `float("nan")` and `float("inf")` successfully cast to floats without raising `ValueError`, bypassing type checks and causing serialization failures or corrupting mathematical calculations. Additionally, future timestamps (>15 min) could distort duration.
* **Fix**: Added `math.isnan()` and `math.isinf()` assertions for `temperature`, `humidity`, and `gas`. Added future-timestamp clamping to `now_utc`.

### BUG-06: Recharts Y-Axis Domain Clipping Safe Band and Gas Threshold
* **Root Cause**: Recharts auto-scaling calculates domains strictly from `<Line dataKey="..." />` values. When temperature variation was small (e.g. $13.2\text{--}13.8^\circ\text{C}$), the domain collapsed to $[13, 14]$, placing the $[12, 15]^\circ\text{C}$ `<ReferenceArea>` outside the visible canvas. Similarly, the 400 ADC senescence line was clipped on baseline readings.
* **Fix**: Provided dynamic domain calculation functions that encompass both sensor data ranges and reference envelopes.

### BUG-07: Windows Batch Script Space & Escaping Incompatibilities
* **Root Cause**: `node_modules\"` escaped quotes in `cmd.exe`. Nested `cd /d` inside quotes failed when paths contained spaces.
* **Fix**: Used native Windows `start "title" /D "%DIR%" cmd /k "..."` working directory flag, eliminating nested quotation escaping and path space issues.

---

## 3. Files Modified During Audit

1. [backend/database.py](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/database.py):
   * Added `get_previous_risk_for_session(session_id)`.
   * Implemented temporal cutoff filtering in `get_history(hours, limit, session_id)`.
   * Enforced monotonic `last_reading_time` progression in `update_session_duration`.
   * Hardened `end_active_session` to deactivate all active records.
2. [backend/app.py](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/app.py):
   * Restructured alert trigger logic to check immediate previous risk category.
   * Fixed session duration isolation in `GET /api/latest`.
   * Added `math.isnan()`, `math.isinf()`, and future timestamp clamping.
   * Handled silent JSON extraction and error status codes.
3. [backend/simulator.py](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/simulator.py):
   * Added thread-safe re-entrant lock on `start()` and `stop()` to guarantee a single simulator loop.
   * Adjusted `high_humidity` simulation mode for 100% RH profiles (leafy greens).
4. [backend/tests/test_api.py](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/tests/test_api.py):
   * Added `test_alert_recovery_and_re_escalation`.
   * Added `test_session_isolation_no_exposure_leak`.
   * Added `test_sensor_data_nan_inf_validation`.
   * Added `test_history_hours_filtering`.
   * Added `test_acknowledge_alert_validation`.
5. [backend/tests/test_database.py](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/tests/test_database.py):
   * Added `test_out_of_order_timestamp_handling`.
   * Added `test_get_previous_risk_for_session`.
6. [frontend/src/App.tsx](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/App.tsx):
   * Added consecutive poll failure tracker (`pollErrorCountRef`) for live offline detection and automatic recovery.
   * Added active session overwrite guards with confirmation dialogs.
7. [frontend/src/components/HistoricalAnalytics.tsx](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/components/HistoricalAnalytics.tsx):
   * Updated YAxis domain functions for Temperature and Gas charts to prevent clipping of safe zones and thresholds.
8. [start.bat](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/start.bat) and [smart-food-storage/start.bat](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/start.bat):
   * Updated to use native `/D` directory flag for robust path execution with spaces.

---

## 4. Mathematical Validation Results

The mathematical formulations from the project proposal were audited and verified across boundary conditions:

### Formulation:
$$R = (T_s \times 0.30) + (H_s \times 0.25) + (G_s \times 0.25) + (D_s \times 0.20)$$
* **Weight Constraint**: $0.30 + 0.25 + 0.25 + 0.20 = 1.0000$ (Verified).
* **Upper & Lower Bounds**:
  * Minimum: $T_s=0, H_s=0, G_s=0, D_s=0 \implies R = 0.0\%$ (Verified).
  * Maximum: $T_s=100, H_s=100, G_s=100, D_s=100 \implies R = 100.0\%$ (Verified).
* **Proposal Baseline Case (Par. 112)**:
  * Inputs: $T_s = 80, H_s = 70, G_s = 60, D_s = 75$.
  * Calculation: $(80 \times 0.30) + (70 \times 0.25) + (60 \times 0.25) + (75 \times 0.20) = 24.0 + 17.5 + 15.0 + 15.0 = 71.5\%$.
  * Engine Output: Exactly $71.50\%$ (High Risk). (Verified).
* **Stress-Weighted Exposure Persistence**:
  * Nominal Conditions ($T_s=0, H_s=0$): $1\text{ hr elapsed} \implies 1.00\text{ effective hrs added}$.
  * Thermal Abuse ($T_s=100, \alpha=1.5$): $1\text{ hr elapsed} \implies 2.50\text{ effective hrs added}$.
  * Verified that brief spikes do not immediately saturate $D_s$, whereas sustained exposure accumulates rapidly.

---

## 5. Automated Backend Test Results (`pytest -v`)

Full test execution output:

```
collected 31 items

tests/test_api.py::test_health_endpoint PASSED                           [  3%]
tests/test_api.py::test_food_profiles_endpoint PASSED                    [  6%]
tests/test_api.py::test_session_lifecycle_api PASSED                     [  9%]
tests/test_api.py::test_sensor_data_validation PASSED                    [ 12%]
tests/test_api.py::test_sensor_data_nan_inf_validation PASSED            [ 16%]
tests/test_api.py::test_sensor_data_ingestion_and_risk PASSED            [ 19%]
tests/test_api.py::test_alert_escalation_logic PASSED                    [ 22%]
tests/test_api.py::test_alert_recovery_and_re_escalation PASSED          [ 25%]
tests/test_api.py::test_session_isolation_no_exposure_leak PASSED        [ 29%]
tests/test_api.py::test_acknowledge_alert_validation PASSED              [ 32%]
tests/test_api.py::test_simulator_controls_and_step PASSED               [ 35%]
tests/test_api.py::test_history_hours_filtering PASSED                   [ 38%]
tests/test_database.py::test_init_db_and_profiles PASSED                 [ 41%]
tests/test_database.py::test_session_lifecycle PASSED                    [ 45%]
tests/test_database.py::test_sensor_reading_and_risk_persistence PASSED  [ 48%]
tests/test_database.py::test_persistence_across_restart PASSED           [ 51%]
tests/test_database.py::test_alerts_logging_and_ack PASSED               [ 54%]
tests/test_database.py::test_out_of_order_timestamp_handling PASSED      [ 58%]
tests/test_database.py::test_get_previous_risk_for_session PASSED        [ 61%]
tests/test_database.py::test_empty_database_state_safety PASSED          [ 64%]
tests/test_risk_engine.py::test_temperature_risk_in_range PASSED         [ 67%]
tests/test_risk_engine.py::test_temperature_risk_above_max PASSED        [ 70%]
tests/test_risk_engine.py::test_temperature_risk_below_min PASSED        [ 74%]
tests/test_risk_engine.py::test_humidity_risk_in_range PASSED            [ 77%]
tests/test_risk_engine.py::test_humidity_risk_out_of_range PASSED        [ 80%]
tests/test_risk_engine.py::test_gas_risk_scoring PASSED                  [ 83%]
tests/test_risk_engine.py::test_duration_risk_scoring PASSED             [ 87%]
tests/test_risk_engine.py::test_duration_stress_multiplier PASSED        [ 90%]
tests/test_risk_engine.py::test_composite_risk_weights_and_bounds PASSED [ 93%]
tests/test_risk_engine.py::test_risk_classification PASSED               [ 96%]
tests/test_risk_engine.py::test_actionable_recommendations PASSED        [100%]

============================= 31 passed in 0.83s ==============================
```

---

## 6. Frontend Production Build Results (`npm run build`)

```
> frontend@0.0.0 build
> tsc -b && vite build

vite v8.3.8 building client environment for production...
transforming...
✓ 2468 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.85 kB │ gzip:   0.47 kB
dist/assets/index-DFtnKJbc.css   25.59 kB │ gzip:   5.44 kB
dist/assets/index-BlzTHJ19.js   653.91 kB │ gzip: 191.13 kB
✓ built in 908ms with 0 errors.
```

---

## 7. Live API Integration & End-to-End Test Results

Direct HTTP request verification against live Flask server (`http://127.0.0.1:5000`):

```
1. Health Endpoint: HTTP 200 (status: "online", database: "connected")
2. Food Profiles: HTTP 200 (4 profiles returned: tomatoes, bananas, apples, leafy_vegetables)
3. Session Creation (Apples): HTTP 201 (accumulated_effective_hours: 0.0)
4. Session Isolation Check: HTTP 200 (effective_exposure_hours: 0.0, no prior session bleed)
5. Thermal Stress Ingestion: HTTP 201 (Risk: 49.17%, Category: Moderate, New Alert: True)
6. Recovery Ingestion: HTTP 201 (Risk: 0.46%, Category: Low, New Alert: False)
7. Secondary Escalation Ingestion: HTTP 201 (Risk: 52.70%, Category: Moderate, New Alert: True)
8. Alert Persistence & Query: HTTP 200 (Alert logged with full context)
9. Alert Acknowledgment: HTTP 200 (acknowledged: 1)
10. Simulator Mode Change & Step: HTTP 200 (mode: combined_stress, reading generated with valid bounds)
```

---

## 8. Database Durability & Concurrency Verification

* **WAL Mode Active**: SQLite configured with `PRAGMA journal_mode = WAL;` and `PRAGMA foreign_keys = ON;`.
* **Restart Resilience**: Verified that restarting Flask preserves all historical telemetry, active sessions, and alerts.
* **Concurrency**: Handled simultaneous multi-thread ingestion from simulator background loop and API queries without database locks or transaction collisions.
* **Empty Database State**: Verified that an empty database returns structured empty arrays (`data: []`) and graceful nulls rather than throwing unhandled exceptions.

---

## 9. Simulator Reliability Verification

* **Mode Verification**:
  1. `normal`: Verified $T \in [T_{min}, T_{max}]$, $H \in [H_{min}, H_{max}]$, clean headspace gas ($G \approx 185\text{ ADC}$).
  2. `high_temp`: Verified thermal abuse ($26\text{--}30^\circ\text{C}$).
  3. `high_humidity`: Verified relative humidity saturation ($>95\%$).
  4. `elevated_gas`: Verified metabolic VOC surge ($350\text{--}550\text{ ADC}$).
  5. `combined_stress`: Verified synergistic multi-variable degradation.
* **Thread Safety**: Verified that calling `simulator/start` multiple times does not spin up duplicate threads.
* **Telemetry Tagging**: All simulator readings are explicitly labeled with `source: "simulator"`.

---

## 10. Remaining Scope & Hand-off to Prompt 3

1. **Physical Microcontroller Connection**:
   * Hardware is not physically plugged in yet.
   * The REST contract (`POST /api/sensor-data`) is fully ready to receive real ESP32 Wi-Fi HTTP requests.
2. **Read-Only Analysis Guardrail**:
   * The system strictly performs environmental spoilage-risk estimation rather than biological sterility testing, as specified in the proposal.
3. **Application State**:
   * All 31 automated tests pass.
   * Frontend builds in under 1 second without errors.
   * `start.bat` launches cleanly from both project directories on Windows.

---
**Audit Complete.** System is verified robust, mathematically verified, and ready for Prompt 3.
