# HARDWARE INTEGRATION & WIRING GUIDE
## Smart Food Storage Spoilage Predictor - Edge Hardware Node

**Version:** 1.0.0 (Production Release)  
**Target Hardware:** ESP32 Development Board (ESP-WROOM-32 / NodeMCU 30-pin or 38-pin)  
**Firmware Location:** [`hardware/esp32/smart_food_storage.ino`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/smart_food_storage.ino)

---

## 1. System Hardware Architecture Diagram

```
+---------------------------------------------------------------------------------------------------+
|                                      FOOD STORAGE CONTAINER                                       |
|                                                                                                   |
|  +--------------------+     +---------------------+                                               |
|  | DHT22 / AM2302     |     | MQ-135 Gas Sensor   |                                               |
|  | Temp & Humidity    |     | Reducing VOCs/Amines|                                               |
|  +---------+----------+     +----------+----------+                                               |
+------------|---------------------------|----------------------------------------------------------+
             | Data (GPIO 4)             | Analog Out (5V Signal)
             |                           v
             |                +---------------------+
             |                | Voltage Divider     |
             |                | 10kΩ : 20kΩ to GND  |
             |                +----------+----------+
             |                           | Scaled 0 - 3.3V (GPIO 34)
             v                           v
+-------------------------------------------------------------------+
|               ESP32 DEVKIT V1 MICROCONTROLLER NODE                |
|                                                                   |
|   - 12-bit ADC Channel 1 (ADC1_CH6 on GPIO 34)                    |
|   - Adafruit DHT Bus Reader (GPIO 4)                              |
|   - Moving-Average Digital Filter (8 samples)                     |
|   - Non-Blocking Acquisition Loop (10s interval)                  |
|   - WiFi Station Mode (2.4 GHz 802.11 b/g/n)                      |
|                                                                   |
|   [Local Alert Actuators]                                         |
|     ├── Green LED   (GPIO 18) ---> Safe Baseline (Low Risk)       |
|     ├── Yellow LED  (GPIO 19) ---> Warning (Moderate Risk)        |
|     ├── Red LED     (GPIO 21) ---> Danger (High/Critical Risk)    |
|     └── Piezo Buzzer(GPIO 22) ---> Audible Cooldown Chime (Crit)  |
+---------------------------------+---------------------------------+
                                  |
                   HTTP POST JSON | Wi-Fi LAN
                                  v
+-------------------------------------------------------------------+
|            FLASK REST API & RISK ENGINE (192.168.0.101:5000)       |
|                                                                   |
|   - Ingestion Endpoint: /api/sensor-data                          |
|   - Mathematical Spoilage Engine: R = 0.30Ts + 0.25Hs + ...       |
|   - Session Duration Stress Tracking (α = 1.5)                    |
|   - SQLite WAL Persistence (food_storage.db)                      |
+---------------------------------+---------------------------------+
                                  |
                   REST Telemetry | Polling & WebSockets
                                  v
+-------------------------------------------------------------------+
|             REACT + VITE DASHBOARD UI (PORT 5173)                 |
|                                                                   |
|   - Real-Time Radial Risk Gauge & Tiers                           |
|   - Multi-Parameter History Charts (Recharts)                     |
|   - Storage Session & Commodity Profile Management                |
+-------------------------------------------------------------------+
```

---

## 2. Complete Bill of Materials (BOM)

| Item # | Component | Quantity | Value / Specification | Role in Circuit |
|---|---|---|---|---|
| **1** | ESP32 Dev Board | 1 | NodeMCU ESP-WROOM-32 (30/38 pin) | Core edge microcontroller & Wi-Fi transmitter |
| **2** | DHT22 / AM2302 | 1 | Capacitive Humidity & NTC Temp | Microclimate temperature and relative humidity |
| **3** | MQ-135 Sensor | 1 | Metal Oxide Semiconductor ($SnO_2$) | Headspace reducing gases & volatile amines |
| **4** | Green 5mm LED | 1 | $V_f \approx 2.1\text{V}$, $I_f \le 15\text{mA}$ | Visual indication: Low Risk ($0\text{--}30\%$) |
| **5** | Yellow 5mm LED | 1 | $V_f \approx 2.0\text{V}$, $I_f \le 15\text{mA}$ | Visual indication: Moderate Risk ($31\text{--}60\%$) |
| **6** | Red 5mm LED | 1 | $V_f \approx 1.8\text{V}$, $I_f \le 15\text{mA}$ | Visual indication: High / Critical ($61\text{--}100\%$) |
| **7** | Piezo Buzzer | 1 | 5V Active Piezo Buzzer | Audible pulse alert for Critical ($81\text{--}100\%$) |
| **8** | Resistors ($R_{LED}$) | 3 | $220\,\Omega$ or $330\,\Omega$, $1/4\text{W}$ | Current limiting for LEDs |
| **9** | Resistor ($R_1$) | 1 | $10\,\text{k}\Omega$, $1/4\text{W}$, 5% | Voltage divider upper branch (MQ-135 $A_{OUT}$) |
| **10**| Resistor ($R_2$) | 1 | $20\,\text{k}\Omega$ (or $2 \times 10\,\text{k}\Omega$), $1/4\text{W}$ | Voltage divider lower branch (to Ground) |
| **11**| Resistor ($R_{pullup}$)| 1 | $10\,\text{k}\Omega$, $1/4\text{W}$ | Pull-up resistor for DHT22 Data pin to 3.3V |
| **12**| Breadboard | 1 | 830-point solderless breadboard | Prototyping circuit distribution |
| **13**| Jumper Wires | 20+ | Male-to-Male & Male-to-Female | Interconnecting modules |
| **14**| Power Supply | 1 | 5V, 2.0A Micro-USB adapter | Powers ESP32 and MQ-135 heating coil |

---

## 3. Detailed Pinout & Wiring Table

| Component | Component Pin | Connects To | Voltage Level | Notes / Protection |
|---|---|---|---|---|
| **ESP32** | $V_{IN}$ / 5V | 5V Power Rail | 5.0V DC | Powers the ESP32 onboard 3.3V LDO regulator |
| **ESP32** | GND | Ground Rail | 0V | Common circuit ground |
| **ESP32** | 3V3 | 3.3V Power Rail | 3.3V DC | Regulated 3.3V rail for DHT22 |
| **DHT22** | Pin 1 (VCC) | 3.3V Power Rail | 3.3V DC | Do NOT power with 5V to protect data pin |
| **DHT22** | Pin 2 (DATA) | ESP32 **GPIO 4** | 3.3V Logic | $10\,\text{k}\Omega$ pull-up resistor to 3.3V rail |
| **DHT22** | Pin 3 (NC) | Not Connected | - | Leave floating |
| **DHT22** | Pin 4 (GND) | Ground Rail | 0V | Common ground |
| **MQ-135** | VCC | 5V Power Rail | 5.0V DC | **Mandatory 5V** for internal heater ($R_H \approx 33\,\Omega$) |
| **MQ-135** | GND | Ground Rail | 0V | Common ground |
| **MQ-135** | DOUT | Not Connected | - | Digital threshold output is unused |
| **MQ-135** | AOUT | Divider $R_1$ ($10\,\text{k}\Omega$) | Up to 5.0V | **Pass through voltage divider before ESP32!** |
| **Divider** | Midpoint ($R_1 / R_2$) | ESP32 **GPIO 34** | **0 – 3.33V MAX** | Input-only ADC1 channel 6 |
| **Divider** | $R_2$ Bottom | Ground Rail | 0V | Completes voltage divider to common ground |
| **Green LED** | Anode (+) | ESP32 **GPIO 18** | 3.3V Logic | Through $220\,\Omega$ current-limiting resistor |
| **Green LED** | Cathode (-) | Ground Rail | 0V | Common ground |
| **Yellow LED** | Anode (+) | ESP32 **GPIO 19** | 3.3V Logic | Through $220\,\Omega$ current-limiting resistor |
| **Yellow LED** | Cathode (-) | Ground Rail | 0V | Common ground |
| **Red LED** | Anode (+) | ESP32 **GPIO 21** | 3.3V Logic | Through $220\,\Omega$ current-limiting resistor |
| **Red LED** | Cathode (-) | Ground Rail | 0V | Common ground |
| **Buzzer** | Positive (+) | ESP32 **GPIO 22** | 3.3V Logic | Active buzzer signal pin |
| **Buzzer** | Negative (-) | Ground Rail | 0V | Common ground |

---

## 4. Electrical Safety Warnings & Voltage Divider Circuit

> [!CAUTION]
> **CRITICAL ELECTRICAL HAZARD: ESP32 IS NOT 5V TOLERANT!**  
> Exposing ESP32 GPIOs or ADC pins to voltages above $3.6\text{V}$ causes irreversible permanent damage to the ESP32 silicon substrate.

### The Problem
The MQ-135 internal heater requires $5.0\text{V}$ to reach its operational temperature of $\approx 200\text{--}300^\circ\text{C}$. Consequently, the module's analog output voltage ($V_{AOUT}$) scales from $0\text{V}$ up to $4.8\text{--}5.0\text{V}$ when exposed to volatile amine off-gases.

### The Solution: Passive Voltage Divider
To safely step down the $0\text{--}5.0\text{V}$ signal to the ESP32's allowable $0\text{--}3.3\text{V}$ range:
1. Connect a $10\,\text{k}\Omega$ resistor ($R_1$) in series from the MQ-135 `AOUT` pin.
2. Connect a $20\,\text{k}\Omega$ resistor ($R_2$, or two $10\,\text{k}\Omega$ resistors in series) from the junction point to `GND`.
3. Connect the junction point directly to ESP32 **GPIO 34**.

```
             MQ-135 Module
             +-----------+
             |      AOUT |-----+
             +-----------+     |
                               |
                              [ ] R1 = 10 kΩ
                               |
                               +---------------------> ESP32 GPIO 34 (ADC1_CH6)
                               |                       (Input voltage: 0 to 3.33V MAX)
                              [ ] R2 = 20 kΩ
                               |
                               v
                          Common GND
```

### Voltage Divider Calculation
$$V_{ADC} = V_{AOUT} \times \frac{R_2}{R_1 + R_2} = 5.0\,\text{V} \times \frac{20\,\text{k}\Omega}{10\,\text{k}\Omega + 20\,\text{k}\Omega} = 5.0\,\text{V} \times \frac{2}{3} \approx 3.33\,\text{V}$$

In the ESP32 firmware [`smart_food_storage.ino`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/smart_food_storage.ino), the scale factor `VOLTAGE_DIVIDER_RATIO = 1.50f` automatically reconstitutes the equivalent ADC count:
$$ADC_{normalized} = ADC_{measured} \times 1.50$$

---

## 5. Power Supply & Common Ground Requirements

1. **Power Supply Capacity**:
   * ESP32 Wi-Fi bursts draw up to $250\text{mA}$ peak.
   * MQ-135 heater draws $\approx 150\text{--}180\text{mA}$ continuously at 5V.
   * LEDs and Buzzer draw $\approx 50\text{mA}$.
   * **Total Requirement**: Provide a clean $5.0\text{V}$ power source capable of delivering at least **$1.0\text{A}$ (preferably $2.0\text{A}$)**.
2. **Common Ground**:
   * All modules (ESP32, DHT22, MQ-135, LEDs, buzzer, voltage divider) must connect to a single **Common Ground** rail. Failing to tie grounds together results in erratic analog readings and floating ADC references.

---

## 6. Sensor Conditioning & Warm-Up Characteristics

### MQ-135 Thermal Kinetics
1. **Initial Heater Stabilization (Warm-Up)**:
   * **Duration**: 60 to 180 seconds after power-up.
   * **Purpose**: Stabilizes the internal heating coil temperature and brings the tin dioxide ($SnO_2$) semiconductor layer to operating equilibrium.
   * **Behavior**: Analog readings may fluctuate wildly during the first 30 seconds before flattening. The firmware runs an automated countdown during this window.
2. **Long-Term Conditioning (Burn-In)**:
   * **Duration**: 24 to 48 hours for brand-new sensors.
   * **Purpose**: Desorbs residual surface moisture and chemical contaminants accumulated during manufacturing and shipping.
   * **Note**: Initial stabilization is performed every power cycle; factory burn-in is only needed once when first unboxing a new sensor.

### Technical Disclaimer
The MQ-135 sensor is a broad-spectrum metal oxide semiconductor device sensitive to ammonia ($NH_3$), sulfides ($H_2S$), carbon dioxide ($CO_2$), ethanol, and aromatic amines. It **does not identify specific chemical molecules** and **does not measure bacterial colonies or pathogenic safety**. It functions strictly as a relative headspace off-gas indicator.

---

## 7. Local Alert Mechanism & Actuator States

The ESP32 firmware actuates its physical peripherals based on the backend risk engine's classification:

```
+--------------------+----------------+----------------+----------------+--------------------------+
| Risk Category      | Green (GPIO 18)| Yellow (GPIO19)| Red (GPIO 21)  | Buzzer (GPIO 22)         |
+--------------------+----------------+----------------+----------------+--------------------------+
| Low (0–30%)        | SOLID ON       | OFF            | OFF            | OFF                      |
| Moderate (31–60%)  | OFF            | SOLID ON       | OFF            | OFF                      |
| High (61–80%)      | OFF            | SOLID ON       | SOLID ON       | OFF (Visual warning)     |
| Critical (81–100%) | OFF            | OFF            | SOLID ON       | 3 BEEPS EVERY 15s        |
| Network Offline    | OFF            | BLINK (1 Hz)   | OFF            | OFF (Safe fallback)      |
+--------------------+----------------+----------------+----------------+--------------------------+
```

### Buzzer Cooldown Logic
To avoid continuous, ear-piercing alarms in laboratory or domestic settings, the buzzer triggers a distinct 3-beep pattern ($120\text{ms}$ ON / $80\text{ms}$ OFF) followed by a **$15\text{-second}$ silence cooldown period**. If the critical risk condition persists, the sequence repeats non-blockingly using `millis()`.
