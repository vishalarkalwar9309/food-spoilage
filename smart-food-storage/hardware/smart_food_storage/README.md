# ESP32 Firmware - Smart Food Storage Spoilage Predictor

This directory contains the production Arduino C++ firmware for the ESP32-WROOM-32 edge hardware node.

## Directory Files

- `smart_food_storage.ino`: Main firmware source code.
- `config.h`: Private hardware pinouts, Wi-Fi credentials, and server configurations.
- `config.example.h`: Version-controlled configuration template.

## Hardware Pinout Reference

| Component | Pin | ESP32 GPIO | Description |
|---|---|---|---|
| **DHT22** | DATA | GPIO 4 | Environmental temp and relative humidity |
| **DHT22** | VCC | 3.3V | 3.3V logic power rail |
| **DHT22** | GND | GND | Common ground |
| **MQ-135** | AO | GPIO 34 | Via 10kΩ : 10kΩ voltage divider (ADC1_CH6) |
| **MQ-135** | VCC | 5V / VIN | 5.0V power rail for heating element |
| **MQ-135** | GND | GND | Common ground |
| **OLED (SSD1306)** | SDA | GPIO 21 | I2C Data bus (3.3V logic) |
| **OLED (SSD1306)** | SCL | GPIO 22 | I2C Clock bus (3.3V logic) |
| **OLED** | VCC | 3.3V | 3.3V power rail |
| **OLED** | GND | GND | Common ground |
| **Red LED** | Anode (+) | GPIO 18 | High / Critical Risk indicator (via 220Ω) |
| **Green LED** | Anode (+) | GPIO 19 | Safe / Low Risk indicator (via 220Ω) |
| **Blue LED** | Anode (+) | GPIO 23 | Moderate Risk indicator (via 220Ω) |
| **Buzzer** | Signal | GPIO 25 | Active DC or Passive PWM audible alert |
| **Buzzer** | Ground | GND | Common ground |

## Required Arduino Libraries

Install these via **Tools -> Manage Libraries...** in Arduino IDE:

1. `Adafruit SSD1306` (by Adafruit) - version 2.5.x
2. `Adafruit GFX Library` (by Adafruit) - version 1.11.x or 1.12.x
3. `DHT sensor library` (by Adafruit) - version 1.4.x
4. `Adafruit Unified Sensor` (by Adafruit) - version 1.1.x
5. `ArduinoJson` (by Benoit Blanchon) - version 7.x

## Compilation & Upload

1. Open `hardware/smart_food_storage/smart_food_storage.ino` in Arduino IDE.
2. Ensure `config.h` exists with your Wi-Fi credentials and laptop LAN IP address.
3. Select Board: **ESP32 Dev Module** (or your specific ESP32-WROOM-32 board).
4. Select Port: The COM port corresponding to your ESP32 (e.g. `COM3`, `COM4`).
5. Upload Speed: `921600` (or `115200` if upload fails).
6. Click **Upload**.
7. Open Serial Monitor at **115200 baud** to view live diagnostics.
