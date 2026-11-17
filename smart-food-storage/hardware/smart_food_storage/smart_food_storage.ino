/**
 * ==============================================================================
 * Smart Food Storage Spoilage Predictor - ESP32 Firmware
 * ==============================================================================
 * Target Microcontroller: ESP32-WROOM-32 Development Board
 * 
 * Hardware Connections:
 *   - DHT22 (Temp & Humidity) : DATA -> GPIO 4, VCC -> 3.3V, GND -> GND
 *   - MQ-135 (Gas Sensor)     : AO -> 10k:10k Voltage Divider -> GPIO 34 (ADC1_CH6)
 *                               VCC -> 5V / VIN, GND -> GND, DO -> Not Connected
 *   - 0.96" I2C OLED (SSD1306): SDA -> GPIO 21, SCL -> GPIO 22, VCC -> 3.3V, GND -> GND
 *   - Status LEDs (220R each) : Red   -> GPIO 18 (Score > 50%: Elevated / Critical Risk)
 *                               Green -> GPIO 19 (Score 0–30%: Low / Safe Risk)
 *                               Blue  -> GPIO 23 (Score > 30% and <= 50%: Moderate Risk)
 * 
 * Electrical Safety & Signal Conditioning:
 *   ESP32 ADC pins are rated for 3.3V maximum and are NOT 5V tolerant.
 *   The MQ-135 heating element requires 5V. Its analog output (AO) is stepped
 *   down through an external 10k:10k passive voltage divider (R1=10k, R2=10k)
 *   to guarantee the input to GPIO 34 never exceeds 2.5V (well within 3.3V).
 *   The firmware applies a 2.0x compensation factor (VOLTAGE_DIVIDER_RATIO).
 * 
 * Technical Disclaimer:
 *   The MQ-135 sensor provides a relative, non-specific analog response to
 *   oxidizable gases and volatile organic compounds (VOCs). It does not identify
 *   specific chemical species or confirm biological food safety. All spoilage
 *   risk classifications are computed by the backend risk engine as the single
 *   source of truth; the ESP32 does not calculate spoilage risk locally.
 * ==============================================================================
 */

#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <DHT.h>

#if __has_include("config.h")
  #include "config.h"
#elif __has_include("config.example.h")
  #include "config.example.h"
#else
  #warning "Neither config.h nor config.example.h found. Using embedded fallback defaults."
  const char* const WIFI_SSID             = "DESKTOP-S8R42DF 1104";
  const char* const WIFI_PASSWORD         = "412:pT57";
  const char* const BACKEND_SERVER_IP     = "192.168.137.1";
  const int         BACKEND_PORT          = 5000;
  const char* const SENSOR_API_ENDPOINT   = "/api/sensor-data";
  const char* const DEVICE_ID             = "ESP32-FOOD-001";
  #define DHT_PIN             4
  #define DHT_TYPE            DHT22
  #define MQ135_PIN           34
  #define OLED_SDA_PIN        21
  #define OLED_SCL_PIN        22
  #define OLED_I2C_ADDR       0x3C
  #define SCREEN_WIDTH        128
  #define SCREEN_HEIGHT       64
  #define OLED_RESET_PIN      -1
  #define LED_RED_PIN         18
  #define LED_GREEN_PIN       19
  #define LED_BLUE_PIN        23
  const unsigned long SAMPLING_INTERVAL_MS   = 10000;
  const unsigned long MQ135_WARMUP_SECONDS   = 60;
  const float         VOLTAGE_DIVIDER_RATIO  = 2.0f;
  const float         ADC_VREF               = 3.3f;
  const int           MQ135_OVERSAMPLING_COUNT = 16;
  const unsigned long WIFI_RETRY_INTERVAL_MS = 10000;
  const unsigned long HTTP_TIMEOUT_MS        = 5000;
#endif

// ==============================================================================
// GLOBAL SENSOR & PERIPHERAL OBJECTS
// ==============================================================================
DHT dht(DHT_PIN, DHT_TYPE);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET_PIN);

// Risk Classification State (Derived directly from Flask backend adjusted score)
enum RiskLevel {
  RISK_UNKNOWN = 0,
  RISK_LOW,        // 0 - 30%: Safe / Green LED
  RISK_MODERATE,   // >30 - <=50%: Warning / Blue LED
  RISK_HIGH,       // >50%: Elevated / Red LED
  RISK_CRITICAL,   // >80%: Critical / Red LED
  RISK_OFFLINE     // Link or Sensor Fault / Error Pattern (Alt Red/Blue Blink)
};

RiskLevel     currentRiskLevel      = RISK_UNKNOWN;
float         currentCompositeScore = 0.0f;
String        currentRiskCategory   = "INITIALIZING";
String        lastHttpResult        = "WAIT";
String        activeProfileName     = "Detecting...";
bool          oledInitialized       = false;
bool          warmupComplete        = false;

// Non-blocking Timing Trackers
unsigned long lastSampleTimeMs      = 0;
unsigned long lastWifiRetryMs       = 0;
unsigned long lastErrorBlinkMs      = 0;
bool          errorBlinkState       = false;

// ==============================================================================
// FUNCTION DECLARATIONS
// ==============================================================================
void setupHardwarePins();
void initOLED();
void renderWarmupScreen(unsigned long remainingSec, int percent);
void renderTelemetryScreen(float temp, float hum, float gasAdc, float gasVolt);
void renderErrorScreen(const char* title, const char* message);
void performWarmupCycle();
bool readSensorData(float &temperature, float &humidity, float &gasAdc, float &gasVoltage);
void updateActuators(RiskLevel level);
void parseBackendResponse(const String &responseJson);
void sendTelemetryToBackend(float temperature, float humidity, float gasAdc, float gasVoltage);

// ==============================================================================
// OLED DISPLAY RENDERING FUNCTIONS
// ==============================================================================
void initOLED() {
  Wire.begin(OLED_SDA_PIN, OLED_SCL_PIN);
  if (!display.begin(SSD1306_SWITCHCAPVCC, OLED_I2C_ADDR)) {
    Serial.println(F("[WARN] OLED SSD1306 allocation failed. Check I2C wiring (SDA=21, SCL=22)."));
    oledInitialized = false;
  } else {
    oledInitialized = true;
    display.clearDisplay();
    display.setTextColor(SSD1306_WHITE);
    display.setTextSize(1);
    display.setCursor(0, 0);
    display.println(F("===================="));
    display.println(F(" SMART FOOD STORAGE "));
    display.println(F(" SPOILAGE PREDICTOR "));
    display.println(F("===================="));
    display.setCursor(0, 42);
    display.println(F("Booting Edge Node..."));
    display.printf("Dev: %s\n", DEVICE_ID);
    display.display();
    delay(1200);
  }
}

void renderWarmupScreen(unsigned long remainingSec, int percent) {
  if (!oledInitialized) return;
  display.clearDisplay();

  // Header
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println(F("MQ-135 STABILIZING"));
  display.drawFastHLine(0, 9, 128, SSD1306_WHITE);

  // Status & Countdown
  display.setCursor(0, 14);
  display.printf("Thermal Warmup: %lus\n", remainingSec);
  display.printf("Progress: %d%%\n", percent);

  // Visual Progress Bar
  int barWidth = map(percent, 0, 100, 0, 120);
  display.drawRect(4, 34, 120, 10, SSD1306_WHITE);
  display.fillRect(6, 36, max(0, barWidth - 4), 6, SSD1306_WHITE);

  // Status Note
  display.setCursor(0, 50);
  display.println(F("Reaching thermal eq."));
  display.display();
}

void renderTelemetryScreen(float temp, float hum, float gasAdc, float gasVolt) {
  if (!oledInitialized) return;
  display.clearDisplay();

  // Top Status Bar: Wi-Fi status & Backend HTTP response
  display.setTextSize(1);
  display.setCursor(0, 0);
  if (WiFi.status() == WL_CONNECTED) {
    display.print(F("WiFi:OK "));
  } else {
    display.print(F("WiFi:-- "));
  }
  display.print(F("| API:"));
  display.println(lastHttpResult);
  display.drawFastHLine(0, 9, 128, SSD1306_WHITE);

  // Environmental Telemetry
  display.setCursor(0, 13);
  display.printf("T: %.1f C   H: %.1f%%\n", temp, hum);

  display.setCursor(0, 24);
  display.printf("Gas: %.0f (%.2fV)\n", gasAdc, gasVolt);

  display.drawFastHLine(0, 34, 128, SSD1306_WHITE);

  // Spoilage Risk Engine Results (from Backend)
  display.setCursor(0, 38);
  if (currentRiskLevel == RISK_OFFLINE) {
    display.println(F("RISK: LINK ERROR"));
    display.setCursor(0, 50);
    display.println(F("Status: BACKEND OFFLINE"));
  } else if (currentRiskLevel == RISK_UNKNOWN) {
    display.println(F("RISK: Awaiting Sync..."));
    display.setCursor(0, 50);
    display.println(F("Status: STANDBY"));
  } else {
    display.printf("Risk: %.1f%%  [%s]\n", currentCompositeScore, currentRiskCategory.c_str());
    display.setCursor(0, 50);
    if (currentRiskLevel == RISK_LOW) {
      display.println(F("Status: SAFE (GREEN)"));
    } else if (currentRiskLevel == RISK_MODERATE) {
      display.println(F("Status: WARN (BLUE)"));
    } else if (currentRiskLevel == RISK_HIGH) {
      display.println(F("Status: DANGER (RED)"));
    } else if (currentRiskLevel == RISK_CRITICAL) {
      display.println(F("Status: CRITICAL (RED)"));
    }
  }

  display.display();
}

void renderErrorScreen(const char* title, const char* message) {
  if (!oledInitialized) return;
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println(F("--- SENSOR ERROR ---"));
  display.drawFastHLine(0, 9, 128, SSD1306_WHITE);

  display.setCursor(0, 16);
  display.println(title);

  display.setCursor(0, 30);
  display.println(message);

  display.setCursor(0, 50);
  display.println(F("Retrying in loop..."));
  display.display();
}

// ==============================================================================
// HARDWARE INITIALIZATION & PIN SETUP
// ==============================================================================
void setupHardwarePins() {
  pinMode(LED_RED_PIN, OUTPUT);
  pinMode(LED_GREEN_PIN, OUTPUT);
  pinMode(LED_BLUE_PIN, OUTPUT);

  // Start with all LEDs off
  digitalWrite(LED_RED_PIN, LOW);
  digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_BLUE_PIN, LOW);

  // Power-on self-test (LED Chaser: Green -> Blue -> Red)
  digitalWrite(LED_GREEN_PIN, HIGH); delay(180); digitalWrite(LED_GREEN_PIN, LOW);
  digitalWrite(LED_BLUE_PIN, HIGH);  delay(180); digitalWrite(LED_BLUE_PIN, LOW);
  digitalWrite(LED_RED_PIN, HIGH);   delay(180); digitalWrite(LED_RED_PIN, LOW);
}

// ==============================================================================
// MQ-135 SENSOR WARM-UP & STABILIZATION CYCLE
// ==============================================================================
void performWarmupCycle() {
  Serial.printf("[*] Beginning MQ-135 Heater Warm-Up (%lu seconds)...\n", MQ135_WARMUP_SECONDS);
  Serial.println(F("    Stabilizing SnO2 tin-dioxide semiconductor element to operating thermal equilibrium."));

  unsigned long startTime  = millis();
  unsigned long durationMs = MQ135_WARMUP_SECONDS * 1000UL;

  while (millis() - startTime < durationMs) {
    unsigned long elapsedSec   = (millis() - startTime) / 1000UL;
    unsigned long remainingSec = MQ135_WARMUP_SECONDS - elapsedSec;
    int progressPct            = (elapsedSec * 100) / MQ135_WARMUP_SECONDS;

    // Pulse Blue LED at 1Hz during stabilization
    digitalWrite(LED_BLUE_PIN, (elapsedSec % 2 == 0) ? HIGH : LOW);
    digitalWrite(LED_GREEN_PIN, LOW);
    digitalWrite(LED_RED_PIN, LOW);

    // Update OLED progress
    renderWarmupScreen(remainingSec, progressPct);

    if (elapsedSec > 0 && elapsedSec % 10 == 0) {
      Serial.printf("    Stabilizing heater: %lu s remaining (%d%%)...\n", remainingSec, progressPct);
    }
    delay(400);
  }

  digitalWrite(LED_BLUE_PIN, LOW);
  warmupComplete = true;
  Serial.println(F("[OK] MQ-135 Heater Stabilization Complete. Entering Acquisition Loop."));
}

// ==============================================================================
// SENSOR ACQUISITION & ELECTRICAL COMPENSATION
// ==============================================================================
bool readSensorData(float &temperature, float &humidity, float &gasAdc, float &gasVoltage) {
  // 1. Read DHT22 Digital Temperature & Humidity
  float t = dht.readTemperature();
  float h = dht.readHumidity();

  // Validate DHT output against realistic physical bounds
  if (isnan(t) || isnan(h) || isinf(t) || isinf(h) || t < -40.0f || t > 80.0f || h < 0.0f || h > 100.0f) {
    Serial.printf("[WARN] Invalid DHT22 reading: Temp=%.1f, Humidity=%.1f. Retrying once...\n", t, h);
    delay(250);
    t = dht.readTemperature();
    h = dht.readHumidity();
    if (isnan(t) || isnan(h)) {
      renderErrorScreen("DHT22 READ ERROR", "Check GPIO 4 & 3.3V pull-up");
      return false;
    }
  }

  // 2. Read MQ-135 Analog Channel with Oversampling & Moving Average Filter
  long rawSum = 0;
  for (int i = 0; i < MQ135_OVERSAMPLING_COUNT; i++) {
    rawSum += analogRead(MQ135_PIN);
    delay(8); // Small spacing between ADC samples for charge stabilization
  }
  float avgRawAdc = (float)rawSum / (float)MQ135_OVERSAMPLING_COUNT;

  // 3. Electrical Voltage Divider Compensation:
  // Circuit: AO -> R1(10k) -> Junction (GPIO 34) -> R2(10k) -> GND
  // Voltage at ESP32 ADC: V_junction = (avgRawAdc / 4095.0f) * ADC_VREF
  // Original Sensor AO Voltage: V_AO = V_junction * ( (R1 + R2) / R2 ) = V_junction * 2.0f
  float vJunction = (avgRawAdc / 4095.0f) * ADC_VREF;
  float vSensorAO = vJunction * VOLTAGE_DIVIDER_RATIO;

  // Reconstitute normalized ADC count for backend processing:
  // The backend risk engine evaluates gas relative to calibrated ADC thresholds (0 to 4095)
  float normalizedAdc = avgRawAdc * VOLTAGE_DIVIDER_RATIO;
  if (normalizedAdc < 0.0f)    normalizedAdc = 0.0f;
  if (normalizedAdc > 4095.0f) normalizedAdc = 4095.0f;

  temperature = t;
  humidity    = h;
  gasAdc      = normalizedAdc;
  gasVoltage  = vSensorAO;
  return true;
}

// ==============================================================================
// LOCAL ACTUATOR CONTROLLER (Status LEDs)
// ==============================================================================
void updateActuators(RiskLevel level) {
  switch (level) {
    case RISK_LOW:
      // Green LED ONLY (Safe microclimate, produce dormant)
      digitalWrite(LED_GREEN_PIN, HIGH);
      digitalWrite(LED_BLUE_PIN,  LOW);
      digitalWrite(LED_RED_PIN,   LOW);
      break;

    case RISK_MODERATE:
      // Blue LED ONLY (Incipient stress / moderate fluctuation)
      digitalWrite(LED_GREEN_PIN, LOW);
      digitalWrite(LED_BLUE_PIN,  HIGH);
      digitalWrite(LED_RED_PIN,   LOW);
      break;

    case RISK_HIGH:
    case RISK_CRITICAL:
      // Red LED Solid ON (Elevated degradation or critical spoilage risk)
      digitalWrite(LED_GREEN_PIN, LOW);
      digitalWrite(LED_BLUE_PIN,  LOW);
      digitalWrite(LED_RED_PIN,   HIGH);
      break;

    case RISK_OFFLINE:
    default:
      // Network/Sensor Fault State: Blue & Red alternating blink handled non-blockingly in loop()
      digitalWrite(LED_GREEN_PIN, LOW);
      break;
  }
}

// ==============================================================================
// BACKEND RESPONSE PARSER
// ==============================================================================
void parseBackendResponse(const String &responseJson) {
  // 1. Extract Crop / Profile Name if present in payload
  int profIdx = responseJson.indexOf("\"name\":");
  if (profIdx != -1) {
    int s1 = responseJson.indexOf("\"", profIdx + 7);
    int s2 = responseJson.indexOf("\"", s1 + 1);
    if (s1 != -1 && s2 != -1) {
      activeProfileName = responseJson.substring(s1 + 1, s2);
    }
  }

  // 2. Extract Risk Category (Single Source of Truth from Backend Risk Engine)
  int catIdx = responseJson.indexOf("\"category\":");
  if (catIdx != -1) {
    int s1 = responseJson.indexOf("\"", catIdx + 11);
    int s2 = responseJson.indexOf("\"", s1 + 1);
    if (s1 != -1 && s2 != -1) {
      currentRiskCategory = responseJson.substring(s1 + 1, s2);

      // 3. Extract Composite Spoilage Risk Score
      int scoreIdx = responseJson.indexOf("\"composite_score\":");
      if (scoreIdx != -1) {
        int scoreStart = scoreIdx + 18;
        int scoreEnd   = responseJson.indexOf(",", scoreStart);
        if (scoreEnd == -1) scoreEnd = responseJson.indexOf("}", scoreStart);
        if (scoreEnd != -1) {
          currentCompositeScore = responseJson.substring(scoreStart, scoreEnd).toFloat();
        }
      }

      Serial.printf("[BACKEND TRUTH] Crop: %s | Risk Category: %s | Adjusted Score: %.1f%%\n",
                    activeProfileName.c_str(), currentRiskCategory.c_str(), currentCompositeScore);

      // Direct LED drive based on final adjusted score from backend:
      // 0–30: Green LED ON (RISK_LOW)
      // >30 and <=50: Blue LED ON (RISK_MODERATE)
      // >50: Red LED ON (RISK_HIGH / RISK_CRITICAL)
      if (currentCompositeScore <= 30.0f) {
        currentRiskLevel = RISK_LOW;
      } else if (currentCompositeScore <= 50.0f) {
        currentRiskLevel = RISK_MODERATE;
      } else if (currentCompositeScore > 80.0f) {
        currentRiskLevel = RISK_CRITICAL;
      } else {
        currentRiskLevel = RISK_HIGH;
      }

      updateActuators(currentRiskLevel);
      return;
    }
  }

  Serial.println(F("[WARN] Could not parse risk classification from response payload."));
}

// ==============================================================================
// HTTP TELEMETRY TRANSMISSION TO FLASK BACKEND
// ==============================================================================
void sendTelemetryToBackend(float temperature, float humidity, float gasAdc, float gasVoltage) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println(F("[WARN] Wi-Fi offline. Cannot transmit telemetry."));
    currentRiskLevel = RISK_OFFLINE;
    lastHttpResult   = "NO_WIFI";
    updateActuators(RISK_OFFLINE);
    return;
  }

  HTTPClient http;
  String url = String("http://") + BACKEND_SERVER_IP + ":" + String(BACKEND_PORT) + SENSOR_API_ENDPOINT;

  http.begin(url);
  http.setTimeout(HTTP_TIMEOUT_MS);
  http.addHeader("Content-Type", "application/json");

  // Construct JSON Payload strictly matching the Flask /api/sensor-data schema
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
    lastHttpResult  = String(httpCode);
    Serial.printf("[HTTP] Ingestion Successful (%d)\n", httpCode);
    parseBackendResponse(response);
  } else {
    lastHttpResult = (httpCode > 0) ? String(httpCode) : "ERR";
    Serial.printf("[HTTP] Request failed, code: %d, error: %s\n",
                  httpCode, http.errorToString(httpCode).c_str());
    currentRiskLevel = RISK_OFFLINE;
    updateActuators(RISK_OFFLINE);
  }

  http.end();
}

// ==============================================================================
// SETUP ROUTINE
// ==============================================================================
void setup() {
  Serial.begin(115200);
  delay(1000);

  Serial.println();
  Serial.println(F("=========================================================="));
  Serial.println(F("   SMART FOOD STORAGE SPOILAGE PREDICTOR - ESP32 FIRMWARE "));
  Serial.println(F("=========================================================="));
  Serial.printf("Device ID       : %s\n", DEVICE_ID);
  Serial.printf("DHT22 Data Pin  : GPIO %d\n", DHT_PIN);
  Serial.printf("MQ-135 Gas Pin  : GPIO %d (10k:10k Voltage Divider, Ratio: %.2fx)\n", MQ135_PIN, VOLTAGE_DIVIDER_RATIO);
  Serial.printf("I2C OLED Pins   : SDA=GPIO %d, SCL=GPIO %d (Addr: 0x%02X)\n", OLED_SDA_PIN, OLED_SCL_PIN, OLED_I2C_ADDR);
  Serial.printf("Status LEDs     : Red: GPIO %d, Green: GPIO %d, Blue: GPIO %d\n", LED_RED_PIN, LED_GREEN_PIN, LED_BLUE_PIN);
  Serial.printf("Flask Endpoint  : http://%s:%d%s\n", BACKEND_SERVER_IP, BACKEND_PORT, SENSOR_API_ENDPOINT);
  Serial.printf("Sample Interval : %lu ms\n", SAMPLING_INTERVAL_MS);
  Serial.println(F("=========================================================="));

  // 1. Initialize Hardware Pins
  setupHardwarePins();

  // 2. Initialize 0.96" I2C OLED Display
  initOLED();

  // 3. Configure ESP32 12-bit ADC
  analogSetAttenuation(ADC_11db); // Full-scale range ~0 - 3.3V
  analogReadResolution(12);       // 12-bit resolution: 0 - 4095

  // 4. Initialize DHT22 Environmental Sensor
  dht.begin();
  Serial.println(F("[OK] DHT22 Environmental Sensor Initialized."));

  // 5. Connect to Wi-Fi
  Serial.print(F("[*] Connecting to Wi-Fi SSID: "));
  Serial.println(WIFI_SSID);
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  int wifiAttempts = 0;
  while (WiFi.status() != WL_CONNECTED && wifiAttempts < 20) {
    delay(500);
    Serial.print(F("."));
    digitalWrite(LED_BLUE_PIN, !digitalRead(LED_BLUE_PIN)); // Flash Blue during connection
    wifiAttempts++;
  }
  digitalWrite(LED_BLUE_PIN, LOW);

  if (WiFi.status() == WL_CONNECTED) {
    Serial.println();
    Serial.printf("[OK] Wi-Fi Connected! IP: %s (RSSI: %d dBm)\n",
                  WiFi.localIP().toString().c_str(), WiFi.RSSI());
  } else {
    Serial.println();
    Serial.println(F("[WARN] Wi-Fi Connection Timeout. Will retry non-blockingly in loop."));
  }

  // 6. Sensor Heater Thermal Stabilization
  performWarmupCycle();

  // Initial State: Safe / Ready
  updateActuators(RISK_LOW);
  Serial.println(F("[OK] System Ready. Entering Periodic Telemetry Acquisition Loop."));
}

// ==============================================================================
// MAIN ACQUISITION LOOP
// ==============================================================================
void loop() {
  unsigned long now = millis();

  // 1. Non-blocking Wi-Fi Reconnection Handler
  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastWifiRetryMs >= WIFI_RETRY_INTERVAL_MS) {
      lastWifiRetryMs = now;
      Serial.println(F("[!] Wi-Fi dropped. Attempting non-blocking reconnect..."));
      WiFi.reconnect();
    }
  }

  // 2. Periodic Sensor Telemetry Acquisition & Backend Ingestion
  if (now - lastSampleTimeMs >= SAMPLING_INTERVAL_MS) {
    lastSampleTimeMs = now;

    float temperature = 0.0f;
    float humidity    = 0.0f;
    float gasAdc      = 0.0f;
    float gasVoltage  = 0.0f;

    bool readSuccess = readSensorData(temperature, humidity, gasAdc, gasVoltage);

    if (readSuccess) {
      Serial.println();
      Serial.println(F("--- [TELEMETRY ACQUISITION] ---"));
      Serial.printf("Temperature   : %.2f *C\n", temperature);
      Serial.printf("Humidity      : %.2f %%\n", humidity);
      Serial.printf("MQ-135 AO Volt: %.2f V (Divider midpoint: %.2f V)\n", gasVoltage, gasVoltage / VOLTAGE_DIVIDER_RATIO);
      Serial.printf("Normalized Gas: %.0f ADC counts (Raw measured: %.0f)\n", gasAdc, gasAdc / VOLTAGE_DIVIDER_RATIO);

      // Transmit to Flask REST API
      sendTelemetryToBackend(temperature, humidity, gasAdc, gasVoltage);

      // Render updated telemetry on OLED
      renderTelemetryScreen(temperature, humidity, gasAdc, gasVoltage);
    } else {
      Serial.println(F("[ERROR] Sensor acquisition failed. Skipping HTTP packet."));
      currentRiskLevel = RISK_OFFLINE;
      lastHttpResult   = "SENS_ERR";
      updateActuators(RISK_OFFLINE);
      renderErrorScreen("SENSOR READ FAIL", "DHT22 / MQ-135 Error");
    }
  }

  // 3. Non-blocking Error Indication (Blue/Red Blink during Offline/Error)
  if (currentRiskLevel == RISK_OFFLINE) {
    if (now - lastErrorBlinkMs >= 500) {
      lastErrorBlinkMs = now;
      errorBlinkState = !errorBlinkState;
      digitalWrite(LED_BLUE_PIN, errorBlinkState ? HIGH : LOW);
      digitalWrite(LED_RED_PIN,  errorBlinkState ? LOW : HIGH);
      digitalWrite(LED_GREEN_PIN, LOW); // Green strictly OFF
    }
  }

  delay(20); // Small cooperative task yield for ESP32 background FreeRTOS tasks
}
