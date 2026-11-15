# Smart Food Storage Spoilage Predictor

[![Status](https://img.shields.io/badge/status-active-emerald.svg)]()
[![Platform](https://img.shields.io/badge/platform-local%20windows-blue.svg)]()
[![Backend](https://img.shields.io/badge/backend-Flask%20%7C%20SQLite-black.svg)]()
[![Frontend](https://img.shields.io/badge/frontend-React%20%7C%20Vite%20%7C%20Tailwind-cyan.svg)]()
[![Firmware](https://img.shields.io/badge/firmware-ESP32%20%7C%20Arduino-red.svg)]()
[![Tests](https://img.shields.io/badge/tests-33%2F33%20passed-success.svg)]()

> **Edge Microclimate Telemetry & Cumulative Duration-Weighted Environmental Spoilage Risk Engine**

An industrial IoT food storage monitoring application that acquires headspace microclimate kinetics (temperature, relative humidity, volatile metabolic off-gas response) and evaluates a composite environmental spoilage-risk index tailored to specific perishable agricultural commodities.

---

## Complete Project Documentation

| Document | Purpose | Key Content |
|---|---|---|
| 📘 [**DEMONSTRATION_GUIDE.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/DEMONSTRATION_GUIDE.md) | **College Review & Viva Walkthrough** | Step-by-step evaluation guide for both Simulation & Physical ESP32 modes |
| 🔌 [**HARDWARE_GUIDE.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/HARDWARE_GUIDE.md) | **Circuit Wiring & Safety Guide** | BOM, pinout mapping, $10\text{k}\Omega / 20\text{k}\Omega$ voltage divider, safe 3.3V operation |
| 📡 [**API_DOCUMENTATION.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/API_DOCUMENTATION.md) | **REST API Reference** | Full request/response JSON schemas, status codes, and ESP32 C++ client code |
| 💻 [**SETUP_GUIDE.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/SETUP_GUIDE.md) | **Installation Manual** | Windows setup, LAN discovery, firewall rule for port 5000, and Arduino IDE |
| 🧪 [**FINAL_TEST_REPORT.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/FINAL_TEST_REPORT.md) | **QA & Verification Report** | 33/33 automated tests, 0 build errors, firmware syntax checks |
| 📑 [**FINAL_PROJECT_REPORT.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/FINAL_PROJECT_REPORT.md) | **Final Delivery Report** | Complete system architecture, folder map, files modified and created |
| 🔍 [**AUDIT_REPORT.md**](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/AUDIT_REPORT.md) | **Prompt 2 Engineering Audit** | Detailed root-cause analysis and resolution of verified issues |

---

## 1. System Architecture

```
[ Physical ESP32 Hardware Node ]                  [ Built-in Simulator ]
  ├── DHT22 (GPIO 4: Temp & RH)                     ├── 5 Microclimate Scenarios
  └── MQ-135 (GPIO 34: 10k:20k Divider)             └── Auto-Streaming Loop
                    │                                         │
                    └───────────────────┬─────────────────────┘
                                        │ HTTP POST JSON (/api/sensor-data)
                                        ▼
                   [ Python Flask Backend (:5000) ]
                     ├── Ingestion & NaN/Inf Validator
                     ├── Operating Mode State Machine ('simulation' vs 'hardware')
                     ├── Crop Envelopes (Tomatoes, Bananas, Apples, Greens)
                     ├── Spoilage-Risk Mathematical Engine (risk_engine.py)
                     └── SQLite Relational Persistence (WAL Mode)
                                        │
                                        │ REST Telemetry & Polling (3.5s)
                                        ▼
                   [ Industrial Dark Dashboard UI (:5173) ]
                     ├── Real-Time Radial Risk Gauge & Classification Tiers
                     ├── Telemetry Metric Cards (T, RH, Gas, Cumulative Duration)
                     ├── 4 Synchronized Historical Analytics Charts (Recharts)
                     ├── Commodity Profile Matrix & Switcher
                     ├── Storage Session Lifecycle Controller
                     └── Incident Alert Timeline & Acknowledgment Panel
```

---

## 2. Spoilage-Risk Mathematical Model

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

### D. Cumulative Duration & Exposure Persistence Score ($D_s$)
Biological decay accelerates when produce is kept under environmental stress:
$$E_{penalty}(t) = 1.0 + \alpha \cdot \text{stress\_intensity}(t)$$
$$\text{stress\_intensity}(t) = \frac{\max(T_s, H_s)}{100}$$
$$D_s = \min\left(100, \frac{\int E_{penalty}(\tau) d\tau}{L_{ideal}} \times 100\right)$$
Where $L_{ideal}$ is the expected nominal shelf life in hours, and $\alpha \ge 0.5$ is the crop-specific accelerated stress multiplier.

### E. Discrete Risk Severity Tiers
* **Low Risk ($0 \le R \le 30\%$)**: Green indicator. Normal dormancy.
* **Moderate Risk ($31 \le R \le 60\%$)**: Yellow indicator. Incipient stress; inspect container seal or adjust thermostat.
* **High Risk ($61 \le R \le 80\%$)**: Orange indicator. Elevated degradation; relocate produce to cold storage immediately.
* **Critical Risk ($81 \le R \le 100\%$)**: Red indicator. Severe thermal or putrefactive abuse; immediate culinary triage required.

---

## 3. Predefined Commodity Profiles

| Commodity | Scientific Name | Optimal Temp | Optimal RH | Shelf Life ($L_{ideal}$) | Gas Threshold | Stress Multiplier ($\alpha$) |
|---|---|---|---|---|---|---|
| **Tomatoes** | *Solanum lycopersicum* | 12–15°C | 85–90% | 168 hrs (7d) | 400 ADC | 1.5 |
| **Bananas** | *Musa acuminata* | 13–16°C | 85–95% | 120 hrs (5d) | 350 ADC | 1.5 |
| **Apples** | *Malus domestica* | 1–4°C | 90–95% | 720 hrs (30d) | 450 ADC | 1.2 |
| **Leafy Greens** | *Spinacia oleracea* | 0–4°C | 95–100% | 120 hrs (5d) | 380 ADC | 2.0 |

---

## 4. Hardware Wiring & Pin Assignments

```
+--------------------+-------------+---------------------------------------+
| Component          | ESP32 GPIO  | Circuit Connection                    |
+--------------------+-------------+---------------------------------------+
| DHT22 Data         | GPIO 4      | 10kΩ pull-up resistor to 3.3V         |
| MQ-135 Analog (AO) | GPIO 34     | 10kΩ / 20kΩ voltage divider to Ground |
| Green LED (+)      | GPIO 18     | 220Ω resistor to Ground               |
| Yellow LED (+)     | GPIO 19     | 220Ω resistor to Ground               |
| Red LED (+)        | GPIO 21     | 220Ω resistor to Ground               |
| Piezo Buzzer (+)   | GPIO 22     | Directly (or via 100Ω to Ground)      |
| Common Ground      | GND         | Common ground rail across all modules |
+--------------------+-------------+---------------------------------------+
```

> [!CAUTION]
> **ELECTRICAL SAFETY WARNING: ESP32 ADC IS NOT 5V TOLERANT!**  
> The MQ-135 requires 5V for its heater. Its analog output must pass through a $10\,\text{k}\Omega / 20\,\text{k}\Omega$ voltage divider before connecting to GPIO 34 to step down 5.0V to $3.33\text{V}$ max.

---

## 5. Quick Launch Instructions

### One-Click Launch (Windows)
Double click [`start.bat`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/start.bat) in the project root:
1. Detects Python 3.10+ and Node.js.
2. Installs requirements and initializes SQLite.
3. Automatically detects your laptop's LAN IPv4 address (e.g. `192.168.0.101`).
4. Launches Flask on `http://127.0.0.1:5000` (listening on `0.0.0.0:5000`).
5. Launches Vite on `http://localhost:5173`.
6. Opens the web browser automatically.

### Running Automated Verification Tests
```powershell
# Backend unit & integration test suite (33 tests)
python -m pytest -v

# Frontend TypeScript & Vite production build
cd smart-food-storage\frontend
npm run build
```

---

## 6. Technical Disclaimer

The Smart Food Storage Spoilage Predictor models ambient headspace environmental risk factors. It does not perform invasive microbiological culture testing or biochemical titration and does not claim to scientifically confirm biological safety or food sterility.
