/**
 * config.example.h
 * Smart Food Storage Spoilage Predictor - ESP32 Configuration Template
 * 
 * INSTRUCTIONS:
 * 1. Duplicate or rename this file to "config.h" in the same directory.
 * 2. Update the Wi-Fi credentials and laptop LAN IP address below.
 * 3. Never commit your production "config.h" with real credentials to version control.
 */

#ifndef CONFIG_H
#define CONFIG_H

// ==============================================================================
// 1. WI-FI NETWORK CREDENTIALS
// ==============================================================================
// Enter your 2.4 GHz Wi-Fi SSID and Password (ESP32 does NOT support 5 GHz Wi-Fi)
const char* const WIFI_SSID     = "YOUR_WIFI_SSID";
const char* const WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";

// ==============================================================================
// 2. BACKEND SERVER CONFIGURATION
// ==============================================================================
// Set this to your laptop's local LAN IPv4 address (e.g. run "ipconfig" in CMD/PowerShell)
// DO NOT use "127.0.0.1" or "localhost" - the ESP32 cannot resolve them.
// Example: "192.168.0.101"
const char* const BACKEND_SERVER_IP = "192.168.0.101";
const int         BACKEND_PORT      = 5000;

// REST API ingestion endpoint on the Flask backend
const char* const SENSOR_API_ENDPOINT = "/api/sensor-data";

// Unique hardware identifier reported to backend telemetry
const char* const DEVICE_ID = "ESP32-FOOD-001";

// ==============================================================================
// 3. HARDWARE GPIO PIN ASSIGNMENTS (Configurable)
// ==============================================================================
#define DHT_PIN         4   // GPIO 4  - DHT11 / DHT22 Data pin (requires 10k pull-up to 3.3V)
#define MQ135_PIN      34   // GPIO 34 - MQ-135 Analog Out (ADC1_CH6, input only, requires voltage divider!)
#define LED_GREEN_PIN  18   // GPIO 18 - Green LED (Low Risk status)
#define LED_YELLOW_PIN 19   // GPIO 19 - Yellow LED (Moderate / High Risk status)
#define LED_RED_PIN    21   // GPIO 21 - Red LED (High / Critical Risk status)
#define BUZZER_PIN     22   // GPIO 22 - Piezo Buzzer (Critical Alert)

// ==============================================================================
// 4. SENSOR CONFIGURATION & ELECTRICAL CALIBRATION
// ==============================================================================
// Sensor Type: Set to DHT22 (recommended) or DHT11
#define DHT_TYPE DHT22

// Sampling interval in milliseconds (default: 10000 ms = 10 seconds)
const unsigned long SAMPLING_INTERVAL_MS = 10000;

// Initial MQ-135 heater warm-up duration in seconds.
// - Standard laboratory stabilization: 180 seconds.
// - Fast college demonstration mode: 30 seconds.
const unsigned long MQ135_WARMUP_SECONDS = 60;

// Voltage divider ratio for MQ-135 analog output to ESP32 ADC:
// If MQ-135 is powered with 5V, its analog output can reach 5V.
// ESP32 ADC pins are rated for 3.3V MAX!
// Using R1 = 10kΩ and R2 = 20kΩ: V_out = V_in * (20 / (10 + 20)) = 0.667 * V_in
// Compensation factor: 1.0 / 0.667 = 1.50
// Set to 1.0 if using a 3.3V powered MQ-135 module directly.
const float VOLTAGE_DIVIDER_RATIO = 1.50f;

// Number of analog samples for moving-average noise rejection
const int MQ135_OVERSAMPLING_COUNT = 8;

// Buzzer cooldown period in milliseconds (prevents continuous deafening sound)
const unsigned long BUZZER_COOLDOWN_MS = 15000;

#endif // CONFIG_H
