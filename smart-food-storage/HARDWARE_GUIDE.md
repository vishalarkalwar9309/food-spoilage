# HARDWARE INTEGRATION & WIRING GUIDE
## Smart Food Storage Spoilage Predictor - Edge Hardware Node

**Version:** 2.0.0 (Production Release)  
**Target Hardware:** ESP32 Development Board (ESP-WROOM-32 / NodeMCU 30-pin or 38-pin)  
**Firmware Location:** [`hardware/smart_food_storage/smart_food_storage.ino`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/smart_food_storage/smart_food_storage.ino)

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
             | Data (GPIO 4)             | Analog Out (0 - 5.0V Signal)
             |                           v
             |                +---------------------+
             |                | Voltage Divider     |
             |                | 10kΩ : 10kΩ to GND  |
             |                +----------+----------+
             |                           | Scaled 0 - 2.5V (GPIO 34)
             v                           v
+-------------------------------------------------------------------+
|               ESP32 DEVKIT V1 MICROCONTROLLER NODE                |
|                                                                   |
|   - 12-bit ADC Channel 1 (ADC1_CH6 on GPIO 34)                    |
|   - Adafruit DHT Bus Reader (GPIO 4)                              |
|   - Moving-Average Digital Filter (16 samples)                    |
|   - Non-Blocking Acquisition Loop (10s interval)                  |
|   - WiFi Station Mode (2.4 GHz 802.11 b/g/n)                      |
|                                                                   |
|   [Visual & Audible Edge Interfaces]                              |
|     ├── 0.96" I2C OLED (SDA: GPIO 21, SCL: GPIO 22)               |
|     ├── Green LED   (GPIO 19) ---> Safe Baseline (Low Risk <=30%) |
|     ├── Blue LED    (GPIO 23) ---> Warning (Moderate Risk 31-60%) |
|     ├── Red LED     (GPIO 18) ---> Danger (High/Crit Risk >60%)   |
|     └── Piezo Buzzer(GPIO 25) ---> Audible Alarm Chime (Crit >80%)|
+---------------------------------+---------------------------------+
                                  |
                   HTTP POST JSON | Wi-Fi LAN
                                  v
+-------------------------------------------------------------------+
|            FLASK REST API & RISK ENGINE (LAN_IP:5000)             |
|                                                                   |
|   - Ingestion Endpoint: /api/sensor-data                          |
|   - Mathematical Spoilage Engine: R = 0.30Ts + 0.25Hs + ...       |
|   - Session Duration Stress Tracking (α = 1.5)                    |
|   - SQLite WAL Persistence (food_storage.db)                      |
+---------------------------------+---------------------------------+
                                  |
                   REST Telemetry | Polling (3.5s)
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
| **1** | ESP32 Dev Board | 1 | ESP32-WROOM-32 (30/38 pin) | Core edge microcontroller & Wi-Fi transmitter |
| **2** | DHT22 / AM2302 | 1 | Capacitive Humidity & NTC Temp (3-pin module) | Microclimate temperature and relative humidity |
| **3** | MQ-135 Sensor | 1 | Metal Oxide Semiconductor ($SnO_2$) | Headspace reducing gases & volatile amines |
| **4** | 0.96" I2C OLED | 1 | 128x64 SSD1306 Monochrome Display | Real-time edge telemetry, risk tier & status screen |
| **5** | Red 5mm LED | 1 | $V_f \approx 1.8\text{V}$, $I_f \le 15\text{mA}$ | Visual indication: High / Critical ($61\text{--}100\%$) |
| **6** | Green 5mm LED | 1 | $V_f \approx 2.1\text{V}$, $I_f \le 15\text{mA}$ | Visual indication: Low Risk ($0\text{--}30\%$) |
| **7** | Blue 5mm LED | 1 | $V_f \approx 3.0\text{V}$, $I_f \le 15\text{mA}$ | Visual indication: Moderate Risk ($31\text{--}60\%$) |
| **8** | Resistors ($R_{LED}$) | 3 | $220\,\Omega$, $1/4\text{W}$ | Current limiting for Red, Green, and Blue LEDs |
| **9** | Resistor ($R_1$) | 1 | $10\,\text{k}\Omega$, $1/4\text{W}$, 5% | Voltage divider upper branch (from MQ-135 $A_O$) |
| **10**| Resistor ($R_2$) | 1 | $10\,\text{k}\Omega$, $1/4\text{W}$, 5% | Voltage divider lower branch (to Ground) |
| **11**| Piezo Buzzer | 1 | 5V Active or Passive Piezo Buzzer | Audible pulse alert for Critical ($81\text{--}100\%$) |
| **12**| Breadboard | 1 | 830-point solderless breadboard | Prototyping circuit distribution |
| **13**| Jumper Wires | 20+ | Male-to-Male & Male-to-Female | Interconnecting modules |
| **14**| Power Supply | 1 | 5V, 2.0A Micro-USB adapter | Powers ESP32 and MQ-135 heating coil |

---

## 3. Detailed Pinout & Wiring Table

| Component | Pin | Connects To | Voltage Level | Notes / Protection |
|---|---|---|---|---|
| **ESP32** | $V_{IN}$ / 5V | 5V Power Rail | 5.0V DC | Powers the ESP32 onboard 3.3V LDO regulator |
| **ESP32** | GND | Ground Rail | 0V | Common circuit ground |
| **ESP32** | 3V3 | 3.3V Power Rail | 3.3V DC | Regulated 3.3V rail for DHT22 and OLED |
| **DHT22** | VCC | 3.3V Power Rail | 3.3V DC | Do NOT power with 5V to protect data pin |
| **DHT22** | DATA | ESP32 **GPIO 4** | 3.3V Logic | 3-pin module includes internal pull-up |
| **DHT22** | GND | Ground Rail | 0V | Common ground |
| **MQ-135** | VCC | 5V / VIN Rail | 5.0V DC | **Mandatory 5V** for internal heater ($R_H \approx 33\,\Omega$) |
| **MQ-135** | GND | Ground Rail | 0V | Common ground |
| **MQ-135** | DO | Not Connected | - | Digital comparator threshold is unused |
| **MQ-135** | AO | Divider $R_1$ ($10\,\text{k}\Omega$) | Up to 5.0V | **Pass through voltage divider before ESP32!** |
| **Divider** | Midpoint | ESP32 **GPIO 34** | **0 – 2.50V MAX** | Input-only ADC1 channel 6 |
| **Divider** | $R_2$ Bottom | Ground Rail | 0V | Completes voltage divider to common ground |
| **OLED** | GND | Ground Rail | 0V | Common ground |
| **OLED** | VCC | 3.3V Power Rail | 3.3V DC | Powered via ESP32 3.3V pin |
| **OLED** | SDA | ESP32 **GPIO 21** | 3.3V Logic | I2C Data bus |
| **OLED** | SCL | ESP32 **GPIO 22** | 3.3V Logic | I2C Clock bus |
| **Red LED** | Anode (+) | ESP32 **GPIO 18** | 3.3V Logic | Through $220\,\Omega$ resistor |
| **Red LED** | Cathode (-) | Ground Rail | 0V | Common ground |
| **Green LED** | Anode (+) | ESP32 **GPIO 19** | 3.3V Logic | Through $220\,\Omega$ resistor |
| **Green LED** | Cathode (-) | Ground Rail | 0V | Common ground |
| **Blue LED** | Anode (+) | ESP32 **GPIO 23** | 3.3V Logic | Through $220\,\Omega$ resistor |
| **Blue LED** | Cathode (-) | Ground Rail | 0V | Common ground |
| **Buzzer** | Signal / Control | ESP32 **GPIO 25** | 3.3V Logic | Active DC or Passive PWM (see Section 5) |
| **Buzzer** | Ground (-) | Ground Rail | 0V | Common ground |

---

## 4. Electrical Safety Warnings & 10k:10k Voltage Divider Circuit

> [!CAUTION]
> **CRITICAL ELECTRICAL HAZARD: ESP32 IS NOT 5V TOLERANT!**  
> Exposing ESP32 GPIOs or ADC pins to voltages above $3.6\text{V}$ causes irreversible permanent damage to the ESP32 silicon substrate.

### The Problem
The MQ-135 internal heater requires $5.0\text{V}$ to reach its operational temperature of $\approx 200\text{--}300^\circ\text{C}$. Consequently, the module's analog output voltage ($V_{AO}$) scales from $0\text{V}$ up to $4.8\text{--}5.0\text{V}$ when exposed to volatile amine off-gases.

### The Solution: 10kΩ : 10kΩ Voltage Divider
To safely halve the $0\text{--}5.0\text{V}$ signal into the safe $0\text{--}2.5\text{V}$ range:
1. Connect a $10\,\text{k}\Omega$ resistor ($R_1$) from MQ-135 `AO` to a common junction.
2. Connect ESP32 **GPIO 34** to the common junction.
3. Connect a second $10\,\text{k}\Omega$ resistor ($R_2$) from the common junction to `GND`.

```
             MQ-135 Module
             +-----------+
             |        AO |-----+
             +-----------+     |
                               |
                              [ ] R1 = 10 kΩ
                               |
            Common Junction ---+---------------------> ESP32 GPIO 34 (ADC1_CH6)
                               |                       (Input voltage: 0 to 2.50V MAX)
                              [ ] R2 = 10 kΩ
                               |
                               v
                          Common GND
```

### Mathematical Formulation
$$V_{GPIO34} = V_{AO} \times \frac{R_2}{R_1 + R_2} = V_{AO} \times \frac{10\,\text{k}\Omega}{10\,\text{k}\Omega + 10\,\text{k}\Omega} = 0.50 \times V_{AO}$$

Reconstituting the original sensor voltage in firmware:
$$V_{AO} = V_{GPIO34} \times \frac{R_1 + R_2}{R_2} = V_{GPIO34} \times 2.0$$

In the firmware [`smart_food_storage.ino`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/smart_food_storage/smart_food_storage.ino):
```cpp
const float VOLTAGE_DIVIDER_RATIO = 2.0f;
float vJunction = (avgRawAdc / 4095.0f) * 3.3f;
float vSensorAO = vJunction * VOLTAGE_DIVIDER_RATIO;
float normalizedAdc = avgRawAdc * VOLTAGE_DIVIDER_RATIO;
```

---

## 5. Buzzer Driver Analysis: Direct GPIO vs. Transistor Driver

### Electrical Feasibility
* **ESP32 GPIO Limit**: Rated for $12\text{mA}$ nominal continuous current ($40\text{mA}$ absolute maximum before substrate damage).
* **Buzzer Types**:
  1. **Active Buzzer (DC)**: Contains internal oscillator. Typically draws $25\text{--}40\text{mA}$ at 5V, or $15\text{--}25\text{mA}$ at 3.3V.
  2. **Passive Buzzer (PWM/AC)**: Magnetic coil typically has low DC resistance ($16\,\Omega$ to $42\,\Omega$). Connecting directly to 3.3V draws:
     $$I = \frac{3.3\text{V}}{16\,\Omega} \approx 206\text{ mA} \quad (\text{Catastrophic Overload!})$$

### Drive Recommendations
1. **Direct GPIO Drive (GPIO 25)**:
   * **Only safe** if using a high-impedance ceramic piezo transducer or a 3.3V active buzzer with a $100\,\Omega$ series current-limiting resistor ($I \approx \frac{3.3\text{V} - 1.5\text{V}}{100\,\Omega} \approx 18\text{mA}$).
2. **Transistor Driver Circuit (Recommended for Laboratory & Magnetic Buzzers)**:
   * Use an NPN transistor (2N2222, BC547, or 2N3904):
     * **Base**: Connect to GPIO 25 via a $1\,\text{k}\Omega$ resistor.
     * **Emitter**: Connect to Common GND.
     * **Collector**: Connect to Buzzer Negative terminal.
     * **Buzzer Positive**: Connect to 5V (VIN) rail.
     * **Flyback Diode**: Place a 1N4148 or 1N4001 diode across the buzzer terminals (Cathode to 5V, Anode to Collector) to eliminate inductive flyback voltage spikes.

---

## 6. Local Alert Mechanism & Actuator States

The ESP32 firmware actuates its physical peripherals based strictly on the backend risk engine's classification:

```
+--------------------+----------------+----------------+----------------+--------------------------+
| Risk Category      | Green (GPIO 19)| Blue (GPIO 23) | Red (GPIO 18)  | Buzzer (GPIO 25)         |
+--------------------+----------------+----------------+----------------+--------------------------+
| Low (0–30%)        | SOLID ON       | OFF            | OFF            | OFF                      |
| Moderate (31–60%)  | OFF            | SOLID ON       | OFF            | OFF                      |
| High (61–80%)      | OFF            | OFF            | SOLID ON       | OFF (Visual warning)     |
| Critical (81–100%) | OFF            | OFF            | SOLID ON       | 3 BEEPS EVERY 15s        |
| Network Offline    | OFF            | BLINK (1 Hz)   | OFF            | OFF (Safe fallback)      |
+--------------------+----------------+----------------+----------------+--------------------------+
```

> [!IMPORTANT]
> **Safety Rule**: If sensor readings are invalid or Wi-Fi/Backend connectivity drops, the Green LED is **strictly turned OFF**. The system flashes Blue/Red in a distinct error sequence and displays `ERR: SENSOR FAIL` or `ERR: BACKEND LINK` on the OLED rather than falsely indicating safety.
