/**
 * ==============================================================================
 * Smart Food Storage Spoilage Predictor - ESP32 Firmware
 * ==============================================================================
 * Description:
 *   Production firmware for ESP32-based headspace telemetry monitoring.
 *   Acquires Temperature and Humidity from DHT11/DHT22 and analog gas VOC
 *   readings from an MQ-135 sensor. Transmits data via HTTP POST to a local
 *   Flask backend and actuates local multi-color LEDs and an audible buzzer
 *   based on backend-calculated spoilage risk classifications.
 * 
 * Hardware Requirements:
 *   - ESP32 Development Board (e.g. NodeMCU ESP-WROOM-32)
 *   - DHT11 or DHT22 Temperature & Humidity Sensor
 *   - MQ-135 Air Quality / Gas Sensor
 *   - 3x LEDs: Green (Low Risk), Yellow (Moderate Risk), Red (High/Critical)
 *   - 3x 220Ω - 330Ω Current-limiting resistors for LEDs
 *   - 1x Active or Passive 5V Piezo Buzzer (with 100Ω resistor or 2N2222 driver)
 *   - 1x Voltage Divider (10kΩ + 20kΩ resistors) for MQ-135 analog output
 *   - 1x 10kΩ pull-up resistor for DHT data line (if using bare sensor)
 * 
 * Electrical Safety Warning:
 *   ESP32 GPIO pins are 3.3V MAX and NOT 5V tolerant.
 *   The MQ-135 heating element requires 5V to function. Its analog output (AOUT)
 *   must pass through a voltage divider (e.g., 10kΩ series, 20kΩ to GND) before
 *   connecting to GPIO 34 (ADC1_CH6).
 * 
 * Technical Disclaimer:
 *   The MQ-135 sensor provides a relative, non-specific analog response to
 *   oxidizable gases and volatile organic compounds (VOCs). It does not identify
 *   specific chemical species (e.g. ethylene vs ammonia) or directly measure
 *   pathogenic food spoilage. All classifications represent environmental
 *   storage risk indicators derived by the backend risk engine.
 * ==============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <DHT.h>

// Attempt to load private config.h; fall back to config.example.h if not created
#if __has_include("config.h")
  #include "config.h"
#elif __has_include("config.example.h")
  #include "config.example.h"
#else
  #warning "Neither config.h nor config.example.h found. Using embedded fallback defaults."
  const char* const WIFI_SSID         = "YOUR_WIFI_SSID";
  const char* const WIFI_PASSWORD     = "YOUR_WIFI_PASSWORD";
  const char* const BACKEND_SERVER_IP = "192.168.0.101";
  const int         BACKEND_PORT      = 5000;
  const char* const SENSOR_API_ENDPOINT = "/api/sensor-data";
  const char* const DEVICE_ID         = "ESP32-FOOD-001";
  #define DHT_PIN         4
  #define MQ135_PIN      34
  #define LED_GREEN_PIN  18
  #define LED_YELLOW_PIN 19
  #define LED_RED_PIN    21
  #define BUZZER_PIN     22
  #define DHT_TYPE DHT22
  const unsigned long SAMPLING_INTERVAL_MS = 10000;
  const unsigned long MQ135_WARMUP_SECONDS = 60;
  const float VOLTAGE_DIVIDER_RATIO = 1.50f;
  const int MQ135_OVERSAMPLING_COUNT = 8;
  const unsigned long BUZZER_COOLDOWN_MS = 15000;
#endif

// ==============================================================================
// GLOBAL SENSOR & HARDWARE OBJECTS
// ==============================================================================
DHT dht(DHT_PIN, DHT_TYPE);

// Risk Classification State
enum RiskLevel {
  RISK_UNKNOWN = 0,
  RISK_LOW,
  RISK_MODERATE,
  RISK_HIGH,
  RISK_CRITICAL,
  RISK_OFFLINE
};

RiskLevel currentRiskLevel = RISK_UNKNOWN;
float currentCompositeScore = 0.0f;

// Non-blocking Timing Trackers
unsigned long lastSampleTimeMs  = 0;
unsigned long lastBuzzerAlertMs = 0;
unsigned long bootTimestampMs   = 0;
bool warmupComplete             = false;

// ==============================================================================
// FUNCTION DECLARATIONS
// ==============================================================================
void setupHardwarePins();
void performWarmupCycle();
void updateActuators(RiskLevel level);
void executeBuzzerPattern(int beeps);
bool readSensorData(float &temperature, float &humidity, float &gasAdc);
void sendTelemetryToBackend(float temperature, float humidity, float gasAdc);
void parseBackendResponse(const String &payload);
void handleFallbackOfflineState();

// ==============================================================================
// SETUP ROUTINE
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println(F("=========================================================="));
  Serial.println(F("   SMART FOOD STORAGE SPOILAGE PREDICTOR - ESP32 NODE     "));
  Serial.println(F("=========================================================="));
  Serial.printf("Device ID       : %s\n", DEVICE_ID);
  Serial.printf("DHT Pin         : GPIO %d (Type: %s)\n", DHT_PIN, (DHT_TYPE == DHT22 ? "DHT22" : "DHT11"));
  Serial.printf("MQ-135 Pin      : GPIO %d (ADC1_CH6 with Voltage Divider)\n", MQ135_PIN);
  Serial.printf("Status LEDs     : Green: %d, Yellow: %d, Red: %d\n", LED_GREEN_PIN, LED_YELLOW_PIN, LED_RED_PIN);
  Serial.printf("Audible Buzzer  : GPIO %d\n", BUZZER_PIN);
  Serial.printf("Target Backend  : http://%s:%d%s\n", BACKEND_SERVER_IP, BACKEND_PORT, SENSOR_API_ENDPOINT);
  Serial.printf("Sample Interval : %lu ms\n", SAMPLING_INTERVAL_MS);
  Serial.println(F("=========================================================="));

  // 1. Initialize GPIO Pins
  setupHardwarePins();

  // 2. Configure ESP32 ADC Attenuation
  // 11dB attenuation gives full 0 - 3.3V input range for ADC readings
  analogSetAttenuation(ADC_11db);
  analogReadResolution(12); // 12-bit ADC: range 0 - 4095

  // 3. Initialize DHT Sensor
  dht.begin();
  Serial.println(F("[OK] DHT Environmental Sensor Initialized."));

  // 4. Connect to Wi-Fi Network
  Serial.print(F("[*] Connecting to Wi-Fi: "));
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 20) {
    delay(500);
    Serial.print(F("."));
    digitalWrite(LED_YELLOW_PIN, !digitalRead(LED_YELLOW_PIN)); // Blink yellow during connect
    wifiAttempts++;
  }
  digitalWrite(LED_YELLOW_PIN, LOW);

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.printf("[OK] Wi-Fi Connected! IP: %s (RSSI: %d dBm)\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println();
    Serial.println(F("[WARN] Wi-Fi Connection Timeout. Will retry in main loop."));
  }

  // 5. Sensor Heater Warm-up Routine
  bootTimestampMs = millis();
  performWarmupCycle();

  // Indicate Ready State
  updateActuators(RISK_LOW);
  Serial.println(F("[OK] ESP32 Ready. Entering Periodic Telemetry Acquisition Loop."));
}

// ==============================================================================
// MAIN ACQUISITION LOOP
// ==============================================================================
void loop() {
  unsigned long now = millis();

  // Ensure Wi-Fi connection
  if (WiFi.status() != WL_CONNECTED) {
    static unsigned long lastReconnectAttempt = 0;
    if (now - lastReconnectAttempt > 10000) {
      lastReconnectAttempt = now;
      Serial.println(F("[!] Wi-Fi dropped. Attempting non-blocking reconnect..."));
      WiFi.reconnect();
    }
  }

  // Check sampling interval
  if (now - lastSampleTimeMs >= SAMPLING_INTERVAL_MS) {
    lastSampleTimeMs = now;

    float temperature = 0.0f;
    float humidity = 0.0f;
    float gasAdc = 0.0f;

    // Acquire and validate physical sensor readings
    bool readSuccess = readSensorData(temperature, humidity, gasAdc);

    if (readSuccess) {
      Serial.println();
      Serial.println(F("--- [TELEMETRY ACQUISITION] ---"));
      Serial.printf("Temperature : %.2f *C\n", temperature);
      Serial.printf("Humidity    : %.2f %%\n", humidity);
      Serial.printf("MQ-135 Raw  : %.0f ADC counts (Normalized: %.0f)\n", 
                    gasAdc / VOLTAGE_DIVIDER_RATIO, gasAdc);

      // Transmit to Flask REST API
      sendTelemetryToBackend(temperature, humidity, gasAdc);
    } else {
      Serial.println(F("[ERROR] Sensor acquisition failed. Telemetry packet skipped."));
      handleFallbackOfflineState();
    }
  }

  // Handle critical buzzer alert pulsing with non-blocking cooldown
  if (currentRiskLevel == RISK_CRITICAL) {
    if (now - lastBuzzerAlertMs >= BUZZER_COOLDOWN_MS) {
      lastBuzzerAlertMs = now;
      Serial.println(F("[ALERT] Critical Risk State active. Sounding audible alert pulses."));
      executeBuzzerPattern(3); // 3 warning beeps
    }
  }

  delay(20); // Small cooperative task yield for ESP32 background tasks
}

// ==============================================================================
// HARDWARE INITIALIZATION
// ==============================================================================
void setupHardwarePins() {
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_YELLOW_PIN, OUTPUT);
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);

  // Default all outputs to LOW (OFF)
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_YELLOW_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(BUZZER_PIN, LOW);

  // Self-test LEDs on power-up (Chaser sequence)
  digitalWrite(LED_GREEN_PIN, HIGH);  delay(150); digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_YELLOW_PIN, HIGH); delay(150); digitalWrite(LED_YELLOW_PIN, LOW);
  digitalWrite(LED_RED_PIN, HIGH);    delay(150); digitalWrite(LED_RED_PIN, LOW);

  // Quick 50ms chime on buzzer to confirm operational status
  digitalWrite(BUZZER_PIN, HIGH); delay(50); digitalWrite(BUZZER_PIN, LOW);
}

// ==============================================================================
// MQ-135 SENSOR WARM-UP & STABILIZATION
// ==============================================================================
void performWarmupCycle() {
  Serial.printf("[*] Beginning MQ-135 Heater Stabilization (%lu seconds)...\n", MQ135_WARMUP_SECONDS);
  Serial.println(F("    (Note: Distinguishing power-up thermal stabilization from 24h factory burn-in)"));

  unsigned long startTime = millis();
  unsigned long durationMs = MQ135_WARMUP_SECONDS * 1000UL;

  while (millis() - startTime < durationMs) {
    unsigned long elapsedSec = (millis() - startTime) / 1000UL;
    unsigned long remainingSec = MQ135_WARMUP_SECONDS - elapsedSec;

    // Toggle Yellow LED at 1Hz during stabilization
    digitalWrite(LED_YELLOW_PIN, (elapsedSec % 2 == 0) ? HIGH : LOW);

    // Print countdown every 10 seconds
    if (elapsedSec > 0 && elapsedSec % 10 == 0) {
      int progressPct = (elapsedSec * 100) / MQ135_WARMUP_SECONDS;
      Serial.printf("    Stabilizing sensor heater: %lu s remaining (%d%%)...\n", remainingSec, progressPct);
    }
    delay(500);
  }

  digitalWrite(LED_YELLOW_PIN, LOW);
  warmupComplete = true;
  Serial.println(F("[OK] MQ-135 Sensor Heater Stabilization Complete."));
}

// ==============================================================================
// SENSOR ACQUISITION & FILTERING
// ==============================================================================
bool readSensorData(float &temperature, float &humidity, float &gasAdc) {
  // 1. Read DHT Environmental Sensor
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  // Validate DHT output against non-physical bounds
  if (isnan(t) || isnan(h) || isinf(t) || isinf(h) || t < -20.0f || t > 70.0f || h < 0.0f || h > 100.0f) {
    Serial.printf("[WARN] Invalid DHT read: Temp=%.1f, Humidity=%.1f. Retrying once...\n", t, h);
    delay(200);
    t = dht.readTemperature();
    h = dht.readHumidity();
    if (isnan(t) || isnan(h)) {
      return false;
    }
  }

  // 2. Read MQ-135 Analog Channel with Oversampling & Moving Average
  long rawSum = 0;
  for (int i = 0; i < MQ135_OVERSAMPLING_COUNT; i++) {
    rawSum += analogRead(MQ135_PIN);
    delay(10); // Small interval between samples
  }
  float avgRawAdc = (float)rawSum / (float)MQ135_OVERSAMPLING_COUNT;

  // Apply voltage divider compensation factor
  float normalizedGas = avgRawAdc * VOLTAGE_DIVIDER_RATIO;

  // Clamp within 12-bit ADC range
  if (normalizedGas < 0.0f) normalizedGas = 0.0f;
  if (normalizedGas > 4095.0f) normalizedGas = 4095.0f;

  temperature = t;
  humidity = h;
  gasAdc = normalizedGas;
  return true;
}

// ==============================================================================
// HTTP TELEMETRY TRANSMISSION TO FLASK BACKEND
// ==============================================================================
void sendTelemetryToBackend(float temperature, float humidity, float gasAdc) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WARN] Wi-Fi offline. Cannot post telemetry to backend."));
    handleFallbackOfflineState();
    return;
  }

  HTTPClient http;
  String url = String("http://") + BACKEND_SERVER_IP + ":" + String(BACKEND_PORT) + SENSOR_API_ENDPOINT;

  http.begin(url);
  http.setTimeout(5000); // 5-second connection timeout
  http.addHeader("Content-Type", "application/json");

  // Construct JSON Payload adhering strictly to backend API contract
  String jsonPayload = "{";
  jsonPayload += "\"temperature\":" + String(temperature, 2) + ",";
  jsonPayload += "\"humidity\":" + String(humidity, 2) + ",";
  jsonPayload += "\"gas\":" + String(gasAdc, 1) + ",";
  jsonPayload += "\"device_id\":\"" + String(DEVICE_ID) + "\",";
  jsonPayload += "\"source\":\"esp32\"";
  jsonPayload += "}";

  Serial.print(F("[HTTP] POST -> "));
  Serial.println(url);
  Serial.print(F("[HTTP] Payload: "));
  Serial.println(jsonPayload);

  int httpCode = http.POST(jsonPayload);

  if (httpCode == HTTP_CODE_CREATED || httpCode == HTTP_CODE_OK) {
    String response = http.getString();
    Serial.printf("[HTTP] Ingestion Successful (%d)\n", httpCode);
    parseBackendResponse(response);
  } else {
    Serial.printf("[HTTP] Request failed, code: %d, error: %s\n", 
                  httpCode, http.errorToString(httpCode).c_str());
    handleFallbackOfflineState();
  }

  http.end();
}

// ==============================================================================
// BACKEND RESPONSE PARSER & LOCAL RISK ACTUATION
// ==============================================================================
void parseBackendResponse(const String &payload) {
  // Extract Risk Category from Backend Response
  // Sample expected response segment: "risk":{"composite_score":42.5,"category":"Moderate",...}
  int categoryIdx = payload.indexOf("\"category\":");
  if (categoryIdx != -1) {
    int startQuote = payload.indexOf("\"", categoryIdx + 11);
    int endQuote = payload.indexOf("\"", startQuote + 1);
    if (startQuote != -1 && endQuote != -1) {
      String category = payload.substring(startQuote + 1, endQuote);

      // Extract composite score if available
      int scoreIdx = payload.indexOf("\"composite_score\":");
      if (scoreIdx != -1) {
        int scoreEnd = payload.indexOf(",", scoreIdx);
        if (scoreEnd != -1) {
          currentCompositeScore = payload.substring(scoreIdx + 18, scoreEnd).toFloat();
        }
      }

      Serial.printf("[BACKEND TRUTH] Risk Category: %s | Score: %.1f%%\n",
                    category.c_str(), currentCompositeScore);

      if (category.equalsIgnoreCase("Low")) {
        currentRiskLevel = RISK_LOW;
      } else if (category.equalsIgnoreCase("Moderate")) {
        currentRiskLevel = RISK_MODERATE;
      } else if (category.equalsIgnoreCase("High")) {
        currentRiskLevel = RISK_HIGH;
      } else if (category.equalsIgnoreCase("Critical")) {
        currentRiskLevel = RISK_CRITICAL;
      } else {
        currentRiskLevel = RISK_UNKNOWN;
      }

      updateActuators(currentRiskLevel);
      return;
    }
  }

  Serial.println(F("[WARN] Could not parse risk classification from response payload."));
}

// ==============================================================================
// LOCAL ACTUATOR CONTROLLER (LEDs & Buzzer)
// ==============================================================================
void updateActuators(RiskLevel level) {
  switch (level) {
    case RISK_LOW:
      // Green LED ONLY (Safe microclimate)
      digitalWrite(LED_GREEN_PIN, HIGH);
      digitalWrite(LED_YELLOW_PIN, LOW);
      digitalWrite(LED_RED_PIN, LOW);
      digitalWrite(BUZZER_PIN, LOW);
      break;

    case RISK_MODERATE:
      // Yellow LED ONLY (Early warning / mild fluctuation)
      digitalWrite(LED_GREEN_PIN, LOW);
      digitalWrite(LED_YELLOW_PIN, HIGH);
      digitalWrite(LED_RED_PIN, LOW);
      digitalWrite(BUZZER_PIN, LOW);
      break;

    case RISK_HIGH:
      // Yellow AND Red LEDs simultaneously (Elevated spoilage risk)
      digitalWrite(LED_GREEN_PIN, LOW);
      digitalWrite(LED_YELLOW_PIN, HIGH);
      digitalWrite(LED_RED_PIN, HIGH);
      digitalWrite(BUZZER_PIN, LOW);
      break;

    case RISK_CRITICAL:
      // Red LED Solid ON + Periodic Audible Alert (Active rapid spoilage)
      digitalWrite(LED_GREEN_PIN, LOW);
      digitalWrite(LED_YELLOW_PIN, LOW);
      digitalWrite(LED_RED_PIN, HIGH);
      // Buzzer pattern will be triggered via non-blocking cooldown tracker in loop()
      break;

    case RISK_OFFLINE:
    default:
      // Fallback state: Yellow LED pulse, Green & Red OFF
      digitalWrite(LED_GREEN_PIN, LOW);
      digitalWrite(LED_YELLOW_PIN, HIGH);
      digitalWrite(LED_RED_PIN, LOW);
      digitalWrite(BUZZER_PIN, LOW);
      break;
  }
}

// ==============================================================================
// AUDIBLE BUZZER ACTUATION WITH COOLDOWN
// ==============================================================================
void executeBuzzerPattern(int beeps) {
  for (int i = 0; i < beeps; i++) {
    digitalWrite(BUZZER_PIN, HIGH);
    delay(120);
    digitalWrite(BUZZER_PIN, LOW);
    delay(80);
  }
}

// ==============================================================================
// SAFE FALLBACK BEHAVIOR (Network/Backend Failure)
// ==============================================================================
void handleFallbackOfflineState() {
  Serial.println(F("[FALLBACK] Backend link unavailable. Entering safe indication state."));
  currentRiskLevel = RISK_OFFLINE;
  // Rapid toggle on Yellow LED indicates communication loss without falsely claiming safety
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_RED_PIN, LOW);
  for (int i = 0; i < 3; i++) {
    digitalWrite(LED_YELLOW_PIN, HIGH); delay(100);
    digitalWrite(LED_YELLOW_PIN, LOW);  delay(100);
  }
}
