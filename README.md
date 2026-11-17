# Smart Food Storage Spoilage Predictor

[![Status](https://img.shields.io/badge/status-active-emerald.svg)]()
[![Platform](https://img.shields.io/badge/platform-local%20windows-blue.svg)]()
[![Backend](https://img.shields.io/badge/backend-Flask%20%7C%20SQLite-black.svg)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%7C%20Vite%20%7C%20Tailwind-cyan.svg)]()
[![Firmware](https://img.shields.io/badge/firmware-ESP32%20%7C%20Arduino-red.svg)]()
[![Tests](https://img.shields.io/badge/tests-36%2F36%20passed-success.svg)]()

> **Edge Microclimate Telemetry & Cumulative Duration-Weighted Environmental Spoilage Risk Engine**

An industrial IoT food storage monitoring application that acquires headspace microclimate kinetics (temperature, relative humidity, volatile metabolic off-gas response) and evaluates a composite environmental spoilage-risk index tailored to specific perishable agricultural commodities and storage modes.

---

## Complete Project Documentation

| Document | Purpose | Key Content |
|---|---|---|
| [**DEMONSTRATION_GUIDE.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/DEMONSTRATION_GUIDE.md) | **College Review & Viva Walkthrough** | Step-by-step evaluation guide for both Simulation & Physical ESP32 modes |
| [**HARDWARE_GUIDE.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/HARDWARE_GUIDE.md) | **Circuit Wiring & Safety Guide** | BOM, pinout mapping, 10k:10k voltage divider, safe 3.3V operation |
| [**API_DOCUMENTATION.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/API_DOCUMENTATION.md) | **REST API Reference** | Full request/response JSON schemas, food modes, status codes, and ESP32 C++ client code |
| [**SETUP_GUIDE.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/SETUP_GUIDE.md) | **Installation Manual** | Windows setup, LAN discovery, firewall rule for port 5000, and Arduino IDE |
| [**FINAL_TEST_REPORT.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/FINAL_TEST_REPORT.md) | **QA & Verification Report** | 36/36 automated tests, 0 build errors, firmware syntax checks |
| [**FINAL_PROJECT_REPORT.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/FINAL_PROJECT_REPORT.md) | **Final Delivery Report** | Complete system architecture, folder map, files modified and created |
| [**AUDIT_REPORT.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/AUDIT_REPORT.md) | **Prompt 2 Engineering Audit** | Detailed root-cause analysis and resolution of verified issues |

---

## 1. System Architecture

```
[ Physical ESP32 Hardware Node ]                  [ Built-in Simulator ]
  ├── DHT22 (GPIO 4: Temp & RH)                     ├── 5 Microclimate Scenarios
  └── MQ-135 (GPIO 34: 10k:10k Divider)             └── Auto-Streaming Loop
                    │                                         │
                    └───────────────────┬─────────────────────┘
                                        │ HTTP POST JSON (/api/sensor-data)
                                        ▼
                   [ Python Flask Backend (:5000) ]
                     ├── Ingestion & NaN/Inf Validator
                     ├── Operating Mode State Machine ('simulation' vs 'hardware')
                     ├── Food Modes (Normal, Fruits and Snacks, Rice)
                     ├── Mode-Based Demonstration Risk Adjuster
                     ├── Spoilage-Risk Mathematical Engine (risk_engine.py)
                     └── SQLite Relational Persistence (WAL Mode)
                                        │
                                        │ REST Telemetry & Polling (3.5s)
                                        ▼
                   [ Industrial Dark Dashboard UI (:5173) ]
                     ├── Real-Time Radial Risk Gauge & Classification Tiers
                     ├── Telemetry Metric Cards (T, RH, Gas, Cumulative Duration)
                     ├── 4 Synchronized Historical Analytics Charts (Recharts)
                     ├── Food Mode Switcher (Normal, Fruits & Snacks, Rice)
                     ├── Storage Session Lifecycle Controller
                     └── Incident Alert Timeline & Acknowledgment Panel
```

---

## 2. Food Modes & Demonstration Risk Adjustments

The system supports exactly three selectable food modes. The mathematical base risk score is computed from raw microclimate readings ($0–100\%$), and a demonstration adjustment is applied to illustrate commodity sensitivity:

$$\text{display\_score} = \text{clamp}(\text{base\_risk\_score} + \text{mode\_adjustment}, 0, 100)$$

| Mode ID | Display Name | Scientific Reference | Temp Window | RH Window | Shelf Life | Demo Adj | Notes |
|---|---|---|---|---|---|---|---|
| `normal` | **Normal** | Ambient Pantry / Packaged Goods | 15–22°C | 40–65% | 336 hrs (14d) | **-15%** | Standard ambient pantry baseline. Lower baseline perishability. |
| `fruits_and_snacks` | **Fruits and Snacks** | Fresh Produce (*Citrus*, Tabletop Snacks) | 3–8°C | 85–90% | 672 hrs (28d) | **-10%** | Moderate perishability; postharvest standards (USDA Handbook 66). |
| `rice` | **Rice** | Cooked Grain (*Oryza sativa*) | 1–4°C | 85–95% | 96 hrs (4d) | **+5%** | TCS high-moisture perishable (*Bacillus cereus* risk per FDA Food Code). |

> [!NOTE]
> **Demonstration Adjustment Disclaimer:** Mode adjustments are demonstration offsets applied to the base environmental risk model for classroom and viva comparison. Raw physical sensor telemetry (temperature, relative humidity, gas ADC counts, and elapsed hours) is preserved without modification in SQLite. Switching modes immediately recalculates the displayed score from the original base score without accumulation.

---

## 3. Actuator & Status LED Indications

The physical status LEDs on the ESP32 and the dashboard gauge are driven directly by the final backend-adjusted score:

| Adjusted Score Range | Risk Classification | ESP32 LED Indication | Web Dashboard Color | Recommended Action |
|---|---|---|---|---|
| **0 – 30%** | **Low (Safe)** | **Green LED Solid ON** | Emerald / Green | Optimal microclimate. Storage conditions normal. |
| **>30% and <=50%** | **Moderate (Warning)** | **Blue LED Solid ON** | Cyan / Blue | Incipient deviation. Check container seal or ventilation. |
| **>50%** | **High / Critical (Danger)** | **Red LED Solid ON** | Rose / Red | Severe thermal, humidity, or VOC abuse. Immediate triage required. |
| *Offline / Link Error* | *Fault / Standby* | *Alternating Red & Blue Blink* | Amber / Warning Banner | Backend unreachable or sensor communication fault. |

---

## 4. Spoilage-Risk Mathematical Model

The application computes an empirical, duration-weighted cumulative risk index $R \in [0, 100]\%$:

$$R = (T_s \times W_T) + (H_s \times W_H) + (G_s \times W_G) + (D_s \times W_D)$$

Where weights satisfy:
$$W_T + W_H + W_G + W_D = 1.0 \quad (0.30 + 0.25 + 0.25 + 0.20 = 1.0)$$

### A. Temperature Deviation Score ($T_s$)
Configured over psychrometric window $[T_{min}, T_{max}]$, critical threshold $T_{crit}$, and freezing threshold $T_{freeze}$:
* $T_s = 0$ if $T_{min} \le T \le T_{max}$
* $T_s = \min\left(100, \frac{T - T_{max}}{T_{crit} - T_{max}} \times 100\right)$ if $T > T_{max}$
* $T_s = \min\left(100, \frac{T_{min} - T}{T_{min} - T_{freeze}} \times 100\right)$ if $T < T_{min}$

### B. Humidity Deviation Score ($H_s$)
Configured over optimal relative humidity envelope $[H_{min}, H_{max}]$:
* $H_s = 0$ if $H_{min} \le H \le H_{max}$
* $H_s = \min\left(100, \frac{H - H_{max}}{100 - H_{max}} \times 100\right)$ if $H > H_{max}$ (condensation & mold sporulation)
* $H_s = \min\left(100, \frac{H_{min} - H}{H_{min}} \times 100\right)$ if $H < H_{min}$ (desiccation & transpiration loss)

### C. Gas Response Deviation Score ($G_s$)
MQ-135 ADC response relative to calibrated baseline $G_0$ and senescence threshold $G_{thresh}$:
$$G_s = \min\left(100, \max\left(0, \frac{G_{curr} - G_0}{G_{thresh} - G_0} \times 100\right)\right)$$

### D. Exposure Duration Stress Score ($D_s$)
$$D_s = \min\left(100, \left(\frac{t_{effective}}{t_{ideal}}\right) \times 100\right)$$
Where $t_{effective}$ accumulates stress dynamically whenever environmental violations occur:
$$\Delta t_{effective} = \Delta t \times (1 + \alpha \times S_{env})$$

---

## 5. Hardware Wiring & Pin Assignments

| Component | ESP32 GPIO | Circuit Connection | Electrical Specification |
|---|---|---|---|
| **DHT22 Data** | GPIO 4 | 10k pull-up resistor to 3.3V | 3.3V Digital Signal |
| **MQ-135 AO** | GPIO 34 (ADC1_CH6) | 10k:10k Voltage Divider to GND | 0–2.5V safe input (2.0x ratio) |
| **Status LED: Red** | GPIO 18 | 220R series resistor to GND | Score > 50% (High / Critical) |
| **Status LED: Green** | GPIO 19 | 220R series resistor to GND | Score 0–30% (Low / Safe) |
| **Status LED: Blue** | GPIO 23 | 220R series resistor to GND | Score > 30% and <= 50% (Moderate) |
| **I2C OLED SDA** | GPIO 21 | Direct I2C bus to SSD1306 | 3.3V Data Line |
| **I2C OLED SCL** | GPIO 22 | Direct I2C bus to SSD1306 | 3.3V Clock Line |
| **Common GND** | GND | Common ground rail across all modules | Reference GND |

> [!CAUTION]
> **ELECTRICAL SAFETY WARNING: ESP32 ADC IS NOT 5V TOLERANT!**  
> The MQ-135 requires 5V for its heater. Its analog output must pass through a 10k:10k voltage divider before connecting to GPIO 34 to step down 5.0V to 2.5V max.

---

## 6. Quick Launch Instructions

### One-Click Launch (Windows)
Double click [`start.bat`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/start.bat) in the project root:
1. Detects Python 3.10+ and Node.js.
2. Installs requirements and initializes SQLite.
3. Automatically detects your laptop's LAN IPv4 address (e.g. `192.168.137.1`).
4. Launches Flask on `http://127.0.0.1:5000` (listening on `0.0.0.0:5000`).
5. Launches Vite on `http://localhost:5173`.
6. Opens the web browser automatically.

### Running Automated Verification Tests
```powershell
# Backend unit & integration test suite (36 tests)
python -m pytest smart-food-storage/backend/tests -v

# Frontend TypeScript & Vite production build
cd smart-food-storage/frontend
npm run build
```

---

## 7. Technical Disclaimer

The Smart Food Storage Spoilage Predictor models ambient headspace environmental risk factors. It does not perform invasive microbiological culture testing or biochemical titration and does not claim to scientifically confirm biological safety or food sterility.
