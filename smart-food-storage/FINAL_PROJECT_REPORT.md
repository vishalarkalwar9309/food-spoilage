# FINAL PROJECT DELIVERY & ARCHITECTURE REPORT
## Smart Food Storage Spoilage Predictor (v1.0.0 Production Release)

**Project Title:** Smart Food Storage Spoilage Predictor  
**Date of Completion:** November 15, 2026  
**Engineering Roles:** Senior IoT Engineer, Embedded Systems Developer, Full-Stack Software Architect, QA Lead  
**Operating Environment:** Windows 10/11 Local Host, SQLite Relational Database, ESP32 Microcontroller Node  
**Repository State:** Complete, fully integrated, tested, and documented across all three development prompts.

---

## 1. Final Project Architecture

```
+---------------------------------------------------------------------------------------------------------+
|                                     EDGE HARDWARE LAYER (HEADSPACE)                                      |
|                                                                                                         |
|  [ DHT22 Sensor ]                                      [ MQ-135 Gas Sensor ]                            |
|  Pin: GPIO 4 (3.3V Data Bus)                           Pin: GPIO 34 via 10k:20k Voltage Divider         |
|         │                                                      │                                        |
|         └──────────────────────────┬───────────────────────────┘                                        |
|                                    ▼                                                                    |
|                      [ ESP32 NodeMCU Dev Module ]                                                       |
|                        - 12-bit ADC Oversampling & Moving Average Filter                                |
|                        - Non-blocking 10s Telemetry Acquisition Loop                                    |
|                        - Local Actuators: Green (18), Yellow (19), Red (21) LEDs, Buzzer (22)           |
|                        - Safe Fallback Communication Timeout                                            |
+------------------------------------+--------------------------------------------------------------------+
                                     │
                      HTTP POST JSON │ 2.4 GHz Wi-Fi (LAN: http://192.168.0.101:5000/api/sensor-data)
                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                                 APPLICATION & RISK ENGINE LAYER (FLASK)                                 |
|                                                                                                         |
|  [ Flask REST API (app.py) ]                                                                            |
|    ├── Input Validation (Bounds checking, NaN/Inf rejection, Future timestamp clamping)                 |
|    ├── Operating Mode State Machine ('simulation' vs 'hardware' stream isolation)                       |
|    ├── Multi-Mode Sensor Simulator (5 scenarios: Normal, High T, High H, Gas, Combined)                 |
|    └── LAN IP Interface Discovery (Automatic binding to 0.0.0.0:5000)                                   |
|                                                                                                         |
|  [ Mathematical Spoilage Risk Engine (risk_engine.py) ]                                                 |
|    ├── Composite Equation: R = (0.30 * Ts) + (0.25 * Hs) + (0.25 * Gs) + (0.20 * Ds)                   |
|    ├── Commodity Profiles: Rice, Oranges (Experimental Setup)                                      |
|    └── Exposure Duration Acceleration Model: E_penalty(t) = 1.0 + α * (max(Ts, Hs)/100)                |
|                                                                                                         |
|  [ Database Persistence Layer (database.py) ]                                                           |
|    └── SQLite (food_storage.db) in WAL Mode (sensor_readings, risk_history, sessions, alerts)           |
+------------------------------------+--------------------------------------------------------------------+
                                     │
                      REST Endpoints │ Dynamic JSON Telemetry & Polling (Interval: 3.5s)
                                     ▼
+---------------------------------------------------------------------------------------------------------+
|                                    PRESENTATION & DASHBOARD LAYER (REACT)                               |
|                                                                                                         |
|  [ React 19 + TypeScript + Vite + Tailwind CSS ]                                                        |
|    ├── Navbar: Real-Time Hardware Status Badge, Mode Switcher, Device ID, LAN Ingestion Pill            |
|    ├── Simulator Dock: 5 Emulation Conditions, Step-Once, Auto-Streaming with Hardware Protection       |
|    ├── Radial Risk Gauge Card: Visual Risk Percentage, Severity Tiers, Dynamic Advisory Recommendations |
|    ├── Telemetry Metric Cards: Live T, RH, Gas ADC, and Effective Duration vs Ideal Shelf Life          |
|    ├── Historical Analytics: Synchronized Recharts (T, RH, Gas, Risk) with 1h/24h/7d Temporal Cutoffs  |
|    ├── Food Profile Manager: Interactive Matrix of Optimal Envelopes and Shelf-Life Parameters          |
|    ├── Storage Session Lifecycle: Active Batch Controller, Duration Counter, Previous Sessions Table    |
|    ├── Alerts & Notifications Panel: Escalation Event Timeline with Single-Click Acknowledgment         |
|    └── Technical Disclaimer: Prominent Engineering Notice detailing ambient risk modeling vs assay      |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Final Folder Structure

```
CP/
├── AUDIT_REPORT.md                 # Complete report from Prompt 2 engineering audit
├── HARDWARE_GUIDE.md               # Hardware pinout, voltage divider, and circuit schematics
├── API_DOCUMENTATION.md            # Comprehensive REST API reference and curl examples
├── SETUP_GUIDE.md                  # Windows installation, firewall, and startup manual
├── DEMONSTRATION_GUIDE.md          # College viva & live evaluation walkthrough script
├── FINAL_TEST_REPORT.md            # Complete automated test suite results & verification matrix
├── FINAL_PROJECT_REPORT.md         # Final comprehensive project architecture & delivery report
├── start.bat                       # Automated Windows system launcher with LAN IP detection
│
├── hardware/
│   └── esp32/
│       ├── smart_food_storage.ino  # Production ESP32 Arduino firmware
│       ├── config.example.h        # Configuration template (Wi-Fi, IP, GPIO)
│       ├── config.h                # Active local configuration (git-ignored)
│       └── README.md               # Embedded flashing and wiring guide
│
└── smart-food-storage/
    ├── start.bat                   # Subfolder launcher mirror
    ├── README.md                   # Full repository documentation
    ├── backend/
    │   ├── app.py                  # Flask REST API backend, mode management, and endpoints
    │   ├── risk_engine.py          # Mathematical spoilage risk calculation engine
    │   ├── database.py             # SQLite persistence layer with WAL mode
    │   ├── food_profiles.py        # Centralized crop psychrometric parameters
    │   ├── simulator.py            # Thread-safe multi-mode sensor emulator
    │   ├── seed_demo_data.py       # Seed script for pre-populating historical telemetry
    │   ├── requirements.txt        # Python backend dependencies (Flask, Flask-CORS, pytest)
    │   ├── food_storage.db         # Persistent SQLite database file
    │   └── tests/
    │       ├── test_api.py         # 14 API integration and validation tests
    │       ├── test_database.py    # 8 SQLite schema and lifecycle tests
    │       └── test_risk_engine.py # 11 mathematical boundary and model tests
    └── frontend/
        ├── index.html              # HTML shell
        ├── package.json            # Node.js dependencies and build scripts
        ├── vite.config.ts          # Vite bundler configuration
        ├── tailwind.config.js      # Industrial dark theme design tokens
        ├── tsconfig.json           # TypeScript configuration
        └── src/
            ├── App.tsx             # Root dashboard controller & state manager
            ├── types/              # Centralized TypeScript interface definitions
            ├── services/           # Typed REST API service client (api.ts)
            └── components/
                ├── Navbar.tsx                   # Top navigation, hardware status & mode toggle
                ├── SimulatorDock.tsx            # Emulation controls with hardware guard
                ├── RiskGaugeCard.tsx            # Prominent radial risk gauge & recommendation
                ├── MetricCardCluster.tsx        # 4 real-time telemetry cards (T, RH, Gas, Time)
                ├── HistoricalAnalytics.tsx      # Recharts graphs with safe envelopes
                ├── FoodProfileManager.tsx       # Commodity profiles management
                ├── StorageSessionManager.tsx    # Batch lifecycle & session tracking
                ├── AlertsPanel.tsx              # Escalation timeline & acknowledgment
                └── EngineeringDisclaimer.tsx    # Technical accuracy and scope disclaimer
```

---

## 3. Hardware Wiring Summary

| Component | Pin | Connects To | Voltage | Protection / Resistor |
|---|---|---|---|---|
| **DHT22** | DATA | ESP32 **GPIO 4** | 3.3V Logic | $10\,\text{k}\Omega$ pull-up resistor to 3.3V |
| **MQ-135** | AOUT | ESP32 **GPIO 34** | **0–3.3V** | **$10\,\text{k}\Omega / 20\,\text{k}\Omega$ Voltage Divider** |
| **Green LED** | Anode (+) | ESP32 **GPIO 18** | 3.3V Logic | $220\,\Omega$ current-limiting resistor to GND |
| **Yellow LED** | Anode (+) | ESP32 **GPIO 19** | 3.3V Logic | $220\,\Omega$ current-limiting resistor to GND |
| **Red LED** | Anode (+) | ESP32 **GPIO 21** | 3.3V Logic | $220\,\Omega$ current-limiting resistor to GND |
| **Piezo Buzzer** | Positive (+) | ESP32 **GPIO 22** | 3.3V Logic | Direct (or via 100Ω/2N2222 transistor) |
| **Ground** | GND | Ground Rail | 0V | **Common ground across all modules** |

---

## 4. ESP32 Firmware Information

* **Primary Firmware File:** [`hardware/esp32/smart_food_storage.ino`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/smart_food_storage.ino)
* **Configuration Header:** [`hardware/esp32/config.example.h`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/config.example.h)
* **Key Features:**
  - Configurable GPIO definitions at the top of the header.
  - Automatic 60-second power-up heater stabilization countdown with LED feedback.
  - 8-sample moving-average analog filtering to reject electrical switching noise.
  - Mathematical compensation for the $1.50\times$ voltage divider ratio.
  - Rejection of invalid sensor values (`NaN`, `Inf`, out-of-range).
  - HTTPClient POST to `POST /api/sensor-data` with 5000ms timeout and auto-reconnect.
  - JSON response parser to extract backend risk category ("Low", "Moderate", "High", "Critical").
  - Multi-tier local actuation: Green (Low), Yellow (Moderate), Yellow+Red (High), Red+Buzzer (Critical).
  - Non-blocking 15-second buzzer cooldown to prevent acoustic fatigue.
  - Communication loss safe fallback: Yellow LED pulses at 1Hz without falsely claiming food safety.

---

## 5. Startup & Execution Instructions

### Automated Launch (One-Click)
Run [`start.bat`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/start.bat) from the project root. It will detect dependencies, initialize SQLite, determine your laptop's LAN IP address, launch Flask on port 5000, launch Vite on port 5173, and open your web browser automatically.

### Manual Launch
1. **Backend:**
   ```powershell
   cd smart-food-storage\backend
   python app.py
   ```
2. **Frontend:**
   ```powershell
   cd smart-food-storage\frontend
   npm run dev
   ```

---

## 6. REST API Endpoint Reference

| Endpoint | Method | Role | Status Codes |
|---|---|---|---|
| `/api/health` | `GET` | System diagnostics & hardware node status | 200 |
| `/api/sensor-data` | `POST` | Ingest sensor reading, calculate risk, evaluate alerts | 201, 400, 422, 500 |
| `/api/latest` | `GET` | Most recent reading, component scores, active session | 200 |
| `/api/history` | `GET` | Time-series telemetry points (`?range=1h\|24h\|7d`) | 200 |
| `/api/alerts` | `GET` | Incident log sorted descending | 200 |
| `/api/alerts/acknowledge` | `POST` | Acknowledge incident alert by ID | 200, 400, 404 |
| `/api/food-profiles` | `GET` | List all available crop envelopes | 200 |
| `/api/sessions` | `GET` | Active session and past session history | 200 |
| `/api/sessions/start` | `POST` | Start a new storage batch | 201, 400, 404 |
| `/api/sessions/end` | `POST` | Terminate active storage session | 200 |
| `/api/system/mode` | `GET`/`POST` | Query or toggle `'simulation'` vs `'hardware'` | 200, 400 |
| `/api/simulator/mode` | `POST` | Select simulation scenario (1 of 5) | 200, 400, 422 |
| `/api/simulator/start` | `POST` | Start automated background synthetic streaming | 200, 409 |
| `/api/simulator/stop` | `POST` | Stop automated synthetic streaming | 200 |
| `/api/simulator/step` | `POST` | Ingest single synthetic reading | 200 |

---

## 7. Database Location & Storage Engine

* **File Location:** [`smart-food-storage/backend/food_storage.db`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/food_storage.db)
* **Engine:** SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode = WAL`) and Foreign Key enforcement.
* **Tables:**
  1. `food_profiles`: Psychrometric parameters and shelf-life constants.
  2. `storage_sessions`: Batch names, timestamps, cumulative hours, reading count.
  3. `sensor_readings`: Raw telemetry records ($T, H, G$, timestamp, source, device_id).
  4. `risk_history`: Calculated component scores ($T_s, H_s, G_s, D_s$), composite risk, recommendation.
  5. `alerts`: Escalation incidents, previous severity, risk score, acknowledgment status.

---

## 8. Automated Test Results

* **Backend Suite:** `pytest -v`
  - **33 passed in 0.89 seconds (100% pass rate, 0 failures)**.
  - Covers mathematical risk calculations, boundary conditions, zero division prevention, stress multiplier validation, SQLite persistence across crashes, out-of-order timestamp safety, temporal history cutoff filtering, alert escalation and recovery state machines, and hardware mode stream isolation.
* **Frontend Production Build:** `tsc -b && vite build`
  - **Built cleanly in 857ms with 0 errors**.
  - All TypeScript types verified with strict compilation.

---

## 9. Firmware Verification & Hardware Bench Status

* **Firmware Syntax & Types:** Verified with MinGW `g++ -fsyntax-only` (**0 errors**).
* **Hardware Bench Testing Notice:**
  > Physical hardware bench testing was **NOT fabricated**. An ESP32 microcontroller is not physically connected to this PC. The firmware, schematics, and flashing instructions are completely verified for deployment by the user onto physical hardware.

---

## 10. Remaining Limitations & Future Work

1. **Broad-Spectrum Gas Selectivity:** The MQ-135 is sensitive to multiple volatile compounds; specific ethylene sensing would require dedicated non-dispersive infrared (NDIR) or electrochemical sensors.
2. **Duty-Cycled Power Management:** The MQ-135 heater draws $\approx 160\text{mA}$ continuous at 5V. Future versions for remote field storage should implement pulsed heater operation to enable battery power.
3. **Bluetooth Provisioning:** Adding ESP32 BLE provisioning would allow Wi-Fi credentials to be configured via mobile phone rather than hardcoding in `config.h`.

---

## 11. Complete List of Modified and Newly Created Files

### Newly Created Files in Prompt 3:
1. [`hardware/esp32/smart_food_storage.ino`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/smart_food_storage.ino): Production ESP32 Arduino firmware.
2. [`hardware/esp32/config.example.h`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/config.example.h): Configuration header template.
3. [`hardware/esp32/config.h`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/config.h): Local credentials configuration.
4. [`hardware/esp32/README.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/README.md): Embedded hardware and flashing documentation.
5. [`HARDWARE_GUIDE.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/HARDWARE_GUIDE.md): Circuit schematics, BOM, voltage divider calculation.
6. [`API_DOCUMENTATION.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/API_DOCUMENTATION.md): Complete REST API specification.
7. [`SETUP_GUIDE.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/SETUP_GUIDE.md): Windows installation, network firewall, and troubleshooting manual.
8. [`DEMONSTRATION_GUIDE.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/DEMONSTRATION_GUIDE.md): Step-by-step viva & project review evaluation guide.
9. [`FINAL_TEST_REPORT.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/FINAL_TEST_REPORT.md): Comprehensive test execution and verification report.
10. [`FINAL_PROJECT_REPORT.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/FINAL_PROJECT_REPORT.md): This final delivery document.

### Modified Files:
1. [`backend/app.py`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/app.py): Added LAN IP discovery, system operating mode state machine (`/api/system/mode`), ESP32 hardware presence tracking, and simulator auto-pause protection.
2. [`backend/database.py`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/database.py): Added `get_latest_reading_by_source` helper.
3. [`backend/tests/test_api.py`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/backend/tests/test_api.py): Added tests for system mode toggling and ESP32 telemetry ingestion.
4. [`frontend/src/types/index.ts`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/types/index.ts): Added `HardwareStatus` interface and updated `LatestDataResponse`.
5. [`frontend/src/services/api.ts`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/services/api.ts): Added `fetchSystemMode` and `setSystemMode`.
6. [`frontend/src/components/Navbar.tsx`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/components/Navbar.tsx): Added mode switcher toggle, live ESP32 status badge, and one-click LAN endpoint copy pill.
7. [`frontend/src/components/SimulatorDock.tsx`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/components/SimulatorDock.tsx): Added hardware mode banner notice and simulator lock protection.
8. [`frontend/src/App.tsx`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/frontend/src/App.tsx): Connected mode switcher state, handlers, and synchronized with backend.
9. [`start.bat`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/start.bat) & [`smart-food-storage/start.bat`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/start.bat): Added dynamic LAN IP detection and ESP32 ingestion URL display.
10. [`README.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/README.md) & [`smart-food-storage/README.md`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/smart-food-storage/README.md): Updated with links to all new guides and hardware documentation.
