/**
 * config.example.h
 * Smart Food Storage Spoilage Predictor - ESP32 Hardware Configuration Template
 * 
 * INSTRUCTIONS:
 * 1. Duplicate or rename this file to "config.h" in the same directory.
 * 2. Update the Wi-Fi credentials and host computer LAN IPv4 address below.
 * 3. Never commit your production "config.h" with real credentials to version control.
 * 
 * Hardware Setup:
 * - ESP32-WROOM-32 Development Board
 * - DHT22 (DATA -> GPIO 4, VCC -> 3.3V, GND -> GND)
 * - MQ-135 (AO -> 10k:10k Voltage Divider -> GPIO 34, VCC -> 5V/VIN, GND -> GND)
 * - 0.96" I2C SSD1306 OLED (SDA -> GPIO 21, SCL -> GPIO 22, VCC -> 3.3V, GND -> GND)
 * - Status LEDs: Red (GPIO 18), Green (GPIO 19), Blue (GPIO 23) via 220 ohm resistors
 */

#ifndef CONFIG_H
#define CONFIG_H

// ==============================================================================
// 1. WI-FI NETWORK CREDENTIALS
// ==============================================================================
// Enter your 2.4 GHz Wi-Fi credentials (ESP32 does NOT support 5 GHz networks)
const char* const WIFI_SSID             = "YOUR_WIFI_SSID";
const char* const WIFI_PASSWORD         = "YOUR_WIFI_PASSWORD";

// ==============================================================================
// 2. FLASK BACKEND SERVER CONFIGURATION
// ==============================================================================
// Set this to your host computer's local LAN IPv4 address (e.g. 192.168.137.1 or 192.168.0.101)
// Run "ipconfig" in Command Prompt/PowerShell to confirm your IPv4 address.
// DO NOT use "127.0.0.1" or "localhost" - the ESP32 cannot resolve loopback.
const char* const BACKEND_SERVER_IP     = "192.168.137.1";
const int         BACKEND_PORT          = 5000;
const char* const SENSOR_API_ENDPOINT   = "/api/sensor-data";
const char* const DEVICE_ID             = "ESP32-FOOD-001";

// ==============================================================================
// 3. DHT22 SENSOR CONFIGURATION
// ==============================================================================
#define DHT_PIN             4       // GPIO 4  - DHT22 DATA line
#define DHT_TYPE            DHT22

// ==============================================================================
// 4. MQ-135 GAS SENSOR CONFIGURATION
// ==============================================================================
#define MQ135_PIN           34      // GPIO 34 - MQ-135 AO via 10k:10k voltage divider

// ==============================================================================
// 5. OLED DISPLAY CONFIGURATION (SSD1306 I2C 128x64)
// ==============================================================================
#define OLED_SDA_PIN        21      // GPIO 21 - I2C SDA
#define OLED_SCL_PIN        22      // GPIO 22 - I2C SCL
#define OLED_I2C_ADDR       0x3C    // Standard I2C address (0x3C or 0x3D)
#define SCREEN_WIDTH        128     // OLED width in pixels
#define SCREEN_HEIGHT       64      // OLED height in pixels
#define OLED_RESET_PIN      -1      // Reset pin (-1 if sharing ESP32 reset)

// ==============================================================================
// 6. RGB STATUS LED CONFIGURATION
// ==============================================================================
// Each LED is connected through its own 220-ohm current-limiting resistor to GND.
#define LED_RED_PIN         18      // GPIO 18 - Red LED (High & Critical Risk)
#define LED_GREEN_PIN       19      // GPIO 19 - Green LED (Safe / Low Risk)
#define LED_BLUE_PIN        23      // GPIO 23 - Blue LED (Moderate Risk / Warmup Pulse)

// ==============================================================================
// 7. SENSOR SAMPLING & TIMING CONFIGURATION
// ==============================================================================
// Non-blocking sampling interval in milliseconds (default: 10000 = 10s)
const unsigned long SAMPLING_INTERVAL_MS   = 10000;

// Initial MQ-135 heater thermal stabilization duration in seconds
const unsigned long MQ135_WARMUP_SECONDS   = 60;

// ==============================================================================
// 8. MQ-135 VOLTAGE DIVIDER CALIBRATION
// ==============================================================================
// R1 = 10k ohm (series from MQ-135 AO to junction)
// R2 = 10k ohm (junction to GND)
// V_junction = V_AO * (10k / (10k + 10k)) = 0.5 * V_AO
// Compensation factor = 2.0
const float         VOLTAGE_DIVIDER_RATIO  = 2.0f;

// Nominal ESP32 11dB ADC reference voltage (approx. 3.3V)
const float         ADC_VREF               = 3.3f;

// Moving average oversampling count for electrical noise rejection
const int           MQ135_OVERSAMPLING_COUNT = 16;

// ==============================================================================
// 9. WIFI RECONNECTION CONFIGURATION
// ==============================================================================
const unsigned long WIFI_RETRY_INTERVAL_MS = 10000;

// ==============================================================================
// 10. HTTP CONFIGURATION
// ==============================================================================
const unsigned long HTTP_TIMEOUT_MS        = 5000;

#endif // CONFIG_H
