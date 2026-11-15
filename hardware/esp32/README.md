# ESP32 Firmware Guide: Smart Food Storage Spoilage Predictor

This directory contains the production Arduino IDE-compatible firmware for the ESP32 edge telemetry node.

---

## 1. Directory Structure

```
hardware/
└── esp32/
    ├── smart_food_storage.ino   # Main Arduino firmware source
    ├── config.example.h        # Configuration template (Wi-Fi, IP, GPIO)
    ├── config.h                # User-specific credentials (git-ignored)
    └── README.md               # Hardware setup and flashing instructions
```

---

## 2. Hardware Bill of Materials (BOM)

| Component | Quantity | Specification / Rating |
|---|---|---|
| **ESP32 Dev Module** | 1 | NodeMCU ESP-WROOM-32 (30-pin or 38-pin, 2.4 GHz Wi-Fi) |
| **DHT22 (or DHT11)** | 1 | Digital temperature & relative humidity sensor |
| **MQ-135 Gas Sensor** | 1 | Air quality / MOS gas sensor (analog output) |
| **Green 5mm LED** | 1 | Low Risk indicator |
| **Yellow 5mm LED** | 1 | Moderate Risk / Warning indicator |
| **Red 5mm LED** | 1 | High / Critical Risk indicator |
| **Piezo Buzzer** | 1 | 5V active or passive buzzer for critical audible alerts |
| **Resistors (LEDs)** | 3 | $220\,\Omega$ or $330\,\Omega$, $1/4\text{W}$ |
| **Voltage Divider Resistors** | 2 | $R_1 = 10\,\text{k}\Omega$, $R_2 = 20\,\text{k}\Omega$ ($1/4\text{W}$) |
| **DHT Pull-Up Resistor** | 1 | $10\,\text{k}\Omega$ (if using bare 4-pin DHT sensor) |
| **Breadboard & Jumper Wires**| 1 | Standard solderless breadboard + Dupont wires |
| **Micro-USB Cable** | 1 | Data-capable cable for flashing and serial monitoring |

---

## 3. Electrical Connections & Pinout

```
+--------------------------------------------------------------------------+
|                        ESP32 GPIO PIN ASSIGNMENTS                        |
+---------------------+-------------+--------------------------------------+
| Component Pin       | ESP32 GPIO  | Circuit Notes                        |
+---------------------+-------------+--------------------------------------+
| DHT Data            | GPIO 4      | 10kΩ pull-up to 3.3V                 |
| MQ-135 Analog (AO)  | GPIO 34     | Via 10kΩ/20kΩ voltage divider to GND |
| Green LED (+)       | GPIO 18     | In series with 220Ω to GND           |
| Yellow LED (+)      | GPIO 19     | In series with 220Ω to GND           |
| Red LED (+)         | GPIO 21     | In series with 220Ω to GND           |
| Buzzer (+)          | GPIO 22     | Directly (or via 100Ω/NPN driver)    |
| All GNDs            | GND         | Common Ground Rail                   |
+---------------------+-------------+--------------------------------------+
```

### Critical Electrical Safety Note: Voltage Divider for MQ-135

> [!CAUTION]
> **DO NOT CONNECT MQ-135 ANALOG OUTPUT DIRECTLY TO GPIO 34!**
> The ESP32 ADC inputs are rated for **3.3V maximum** and are **NOT 5V tolerant**. The MQ-135 heating coil requires 5V ($V_{IN}$), so its analog output can swing up to 5.0V under high gas concentrations.

Connect the voltage divider between the MQ-135 $A_{OUT}$ pin and ESP32 GPIO 34:
```
MQ-135 AOUT  ----[ 10kΩ (R1) ]----+----[ 20kΩ (R2) ]---- GND (Common Ground)
                                  |
                                  +----> ESP32 GPIO 34 (ADC1_CH6)
```
**Voltage Calculation**:
$$V_{ADC} = V_{AOUT} \times \frac{R_2}{R_1 + R_2} = 5.0\,\text{V} \times \frac{20\,\text{k}\Omega}{10\,\text{k}\Omega + 20\,\text{k}\Omega} = 3.33\,\text{V maximum}$$

---

## 4. Software Setup & Flashing Instructions

### Step 1: Install Arduino IDE
1. Download and install **Arduino IDE 2.x** from [arduino.cc](https://www.arduino.cc/en/software).

### Step 2: Add ESP32 Board Support
1. In Arduino IDE, navigate to `File` → `Preferences`.
2. In **Additional Board Manager URLs**, paste:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
3. Open `Tools` → `Board` → `Boards Manager`, search for `esp32` by **Espressif Systems**, and click **Install**.

### Step 3: Install Required Libraries
Open `Tools` → `Manage Libraries` and install:
- **DHT sensor library** by Adafruit (v1.4.x)
- **Adafruit Unified Sensor** by Adafruit (dependency for DHT)

*(Note: `WiFi.h` and `HTTPClient.h` are built-in with the ESP32 board package).*

### Step 4: Configure Credentials
1. Copy `config.example.h` to `config.h`:
   ```bash
   cp config.example.h config.h
   ```
2. Open `config.h` in Arduino IDE or a text editor.
3. Set your Wi-Fi SSID and Password:
   ```cpp
   const char* const WIFI_SSID     = "MyHomeWiFi";
   const char* const WIFI_PASSWORD = "MySecretPassword";
   ```
4. Set your laptop's local LAN IPv4 address (run `ipconfig` in Command Prompt to find it):
   ```cpp
   const char* const BACKEND_SERVER_IP = "192.168.0.101"; // Replace with your laptop IP
   const int         BACKEND_PORT      = 5000;
   ```

### Step 5: Flash to ESP32
1. Connect the ESP32 to your laptop using a micro-USB data cable.
2. Select your board under `Tools` → `Board` → `ESP32 Arduino` → `DOIT ESP32 DEVKIT V1` (or `ESP32 Dev Module`).
3. Select the correct COM port under `Tools` → `Port` (e.g. `COM3`, `COM4`).
4. Click the **Upload** button (arrow icon).
5. Open `Tools` → `Serial Monitor` and set the baud rate to **115200**.

---

## 5. Serial Monitor Output Example

```
==========================================================
   SMART FOOD STORAGE SPOILAGE PREDICTOR - ESP32 NODE     
==========================================================
Device ID       : ESP32-FOOD-001
DHT Pin         : GPIO 4 (Type: DHT22)
MQ-135 Pin      : GPIO 34 (ADC1_CH6 with Voltage Divider)
Status LEDs     : Green: 18, Yellow: 19, Red: 21
Audible Buzzer  : GPIO 22
Target Backend  : http://192.168.0.101:5000/api/sensor-data
Sample Interval : 10000 ms
==========================================================
[OK] DHT Environmental Sensor Initialized.
[*] Connecting to Wi-Fi: MyHomeWiFi......
[OK] Wi-Fi Connected! IP: 192.168.0.145 (RSSI: -58 dBm)
[*] Beginning MQ-135 Heater Stabilization (60 seconds)...
    Stabilizing sensor heater: 50 s remaining (16%)...
    Stabilizing sensor heater: 40 s remaining (33%)...
    Stabilizing sensor heater: 30 s remaining (50%)...
    Stabilizing sensor heater: 20 s remaining (66%)...
    Stabilizing sensor heater: 10 s remaining (83%)...
[OK] MQ-135 Sensor Heater Stabilization Complete.
[OK] ESP32 Ready. Entering Periodic Telemetry Acquisition Loop.

--- [TELEMETRY ACQUISITION] ---
Temperature : 13.80 *C
Humidity    : 87.20 %
MQ-135 Raw  : 245 ADC counts (Normalized: 368)
[HTTP] POST -> http://192.168.0.101:5000/api/sensor-data
[HTTP] Payload: {"temperature":13.80,"humidity":87.20,"gas":368.0,"device_id":"ESP32-FOOD-001","source":"esp32"}
[HTTP] Ingestion Successful (201)
[BACKEND TRUTH] Risk Category: Low | Score: 12.4%
```

---

## 6. LED and Buzzer Alert Behavior

The ESP32 uses the backend risk calculation engine as the **single source of truth**:

| Backend Risk Category | Green LED (GPIO 18) | Yellow LED (GPIO 19) | Red LED (GPIO 21) | Buzzer (GPIO 22) |
|---|---|---|---|---|
| **Low** | **ON** | OFF | OFF | OFF |
| **Moderate** | OFF | **ON** | OFF | OFF |
| **High** | OFF | **ON** | **ON** | OFF (Warning state) |
| **Critical** | OFF | OFF | **ON** | **3-Beep Pulse every 15s** |
| **Network Failure** | OFF | **Blinking (1Hz)** | OFF | OFF (Safe Fallback) |

---

## 7. Technical Disclaimer

The MQ-135 sensor is a broad-spectrum metal oxide semiconductor (MOS) sensor that responds to a wide array of volatile organic compounds (ammonia, sulfides, alcohol, carbon dioxide). It does not discriminate between individual gases and does NOT confirm biological contamination or pathogen presence. All risk assessments are indicative microclimate vulnerability estimates computed by the backend risk engine.
