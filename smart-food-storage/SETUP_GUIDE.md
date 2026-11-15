# WINDOWS SETUP & INSTALLATION GUIDE
## Smart Food Storage Spoilage Predictor

**Platform:** Windows 10 / 11 (64-bit)  
**Supported Execution:** Automated (`start.bat`) or Manual (PowerShell / Command Prompt)

---

## 1. System Prerequisites

Before launching the application, ensure the following tools are installed:

| Tool | Minimum Version | Verification Command | Download Link |
|---|---|---|---|
| **Python** | 3.10+ (Tested on 3.11.9) | `python --version` | [python.org](https://www.python.org/downloads/) *(Check "Add Python to PATH")* |
| **Node.js** | 18+ (Tested on v24.19.0) | `node -v` | [nodejs.org](https://nodejs.org/) |
| **Arduino IDE** | 2.0+ (For ESP32 flashing) | `arduino-ide` | [arduino.cc](https://www.arduino.cc/en/software) |

---

## 2. Automated Quickstart (Recommended)

The easiest way to start both backend and frontend is using the unified Windows startup script:

1. Double-click **`start.bat`** in the project root directory, or run from PowerShell:
   ```powershell
   .\start.bat
   ```
2. The script will automatically:
   - Verify Python and Node.js installations.
   - Install backend requirements (`Flask`, `Flask-CORS`, `pytest`).
   - Initialize and seed the SQLite database (`food_storage.db`).
   - Detect your local laptop LAN IPv4 address (e.g. `192.168.0.101`).
   - Install frontend npm packages if `node_modules` is missing.
   - Launch Flask on `http://127.0.0.1:5000` (listening on `0.0.0.0`).
   - Launch Vite on `http://localhost:5173`.
   - Open your default web browser to the dashboard.

---

## 3. Manual Installation & Startup

If you prefer launching each service in its own terminal window:

### Step 1: Backend Setup
```powershell
cd smart-food-storage\backend

# Install dependencies
python -m pip install -r requirements.txt

# Initialize database
python -c "import database; database.init_db(); print('Database ready.')"

# Start Flask API server
python app.py
```
*The backend will start and display:*
```
Starting Smart Food Storage Spoilage Predictor API on http://127.0.0.1:5000
 * Running on all addresses (0.0.0.0:5000)
 * Running on http://127.0.0.1:5000
```

### Step 2: Frontend Setup
Open a second terminal window:
```powershell
cd smart-food-storage\frontend

# Install dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```
*The frontend will start on `http://localhost:5173`.*

---

## 4. Local Network (LAN) & Windows Firewall Setup

When connecting a physical ESP32 to your laptop over Wi-Fi, the ESP32 needs to send HTTP requests to port 5000 on your laptop. Windows Firewall by default may block incoming LAN traffic.

### Step 1: Find Your Laptop's LAN IPv4 Address
Open Command Prompt or PowerShell and run:
```cmd
ipconfig
```
Locate your active Wi-Fi adapter:
```
Wireless LAN adapter Wi-Fi:
   IPv4 Address. . . . . . . . . . . : 192.168.0.101
```
*(Your IP will typically look like `192.168.1.X` or `192.168.0.X`).*

### Step 2: Open Port 5000 in Windows Firewall
Run PowerShell as **Administrator** and execute:
```powershell
New-NetFirewallRule -DisplayName "Smart Food Storage API (Port 5000)" `
  -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow
```
*(Alternatively, open Windows Defender Firewall with Advanced Security → Inbound Rules → New Rule → Port → TCP 5000 → Allow the connection).*

---

## 5. ESP32 Arduino IDE Setup & Flashing

### Step 1: Install ESP32 Board Package
1. Open Arduino IDE 2.x.
2. Go to **File → Preferences**.
3. Under **Additional Board Manager URLs**, paste:
   ```
   https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json
   ```
4. Open **Tools → Board → Boards Manager**, search for `esp32` by Espressif Systems, and click **Install**.

### Step 2: Install Libraries
Open **Tools → Manage Libraries** and install:
- **DHT sensor library** (Adafruit)
- **Adafruit Unified Sensor** (Adafruit)

### Step 3: Configure `config.h`
1. Navigate to [`hardware/esp32/`](file:///c:/Users/visha/OneDrive/Desktop/third%20year/sem%201/IOT/CP/hardware/esp32/).
2. Copy `config.example.h` to `config.h`.
3. Open `config.h` and update:
   ```cpp
   const char* const WIFI_SSID         = "YOUR_WIFI_NAME";
   const char* const WIFI_PASSWORD     = "YOUR_WIFI_PASSWORD";
   const char* const BACKEND_SERVER_IP = "192.168.0.101"; // Your laptop LAN IP
   const int         BACKEND_PORT      = 5000;
   ```

> [!IMPORTANT]
> The ESP32 only supports **2.4 GHz Wi-Fi networks**. Make sure your laptop and ESP32 are connected to the same 2.4 GHz network or hotspot.

### Step 4: Flash Firmware
1. Connect ESP32 to laptop via micro-USB.
2. Select **Tools → Board → ESP32 Arduino → DOIT ESP32 DEVKIT V1** (or ESP32 Dev Module).
3. Select your serial port under **Tools → Port** (e.g. `COM3`).
4. Click **Upload**.
5. Open **Tools → Serial Monitor** at **115200 baud** to see live boot telemetry.

---

## 6. Verification Checklist

To confirm both servers are listening:

```powershell
# Check backend listening on port 5000
Test-NetConnection -ComputerName 127.0.0.1 -Port 5000

# Check frontend listening on port 5173
Test-NetConnection -ComputerName 127.0.0.1 -Port 5173

# Test backend health endpoint via PowerShell
Invoke-RestMethod -Uri http://127.0.0.1:5000/api/health
```

---

## 7. Troubleshooting Guide

| Symptom | Root Cause | Solution |
|---|---|---|
| **`start.bat` closes immediately** | Missing Python or Node.js in PATH | Open `cmd` and verify `python --version` and `node -v`. Reinstall with "Add to PATH" checked. |
| **`npm ERR! code ENOENT`** | `package.json` not found in current folder | Ensure you are executing within `smart-food-storage/frontend`. |
| **ESP32 prints `HTTP Request failed, code: -1`** | Firewall blocking port 5000 or incorrect IP | Add the firewall rule from Section 4 and verify `BACKEND_SERVER_IP` in `config.h` matches `ipconfig`. |
| **ESP32 loops `Connecting to Wi-Fi ......`** | Connected to 5 GHz Wi-Fi or wrong password | Switch to a 2.4 GHz SSID. ESP32 does not support 5 GHz Wi-Fi channels. |
| **`Failed to fetch latest data` on Dashboard** | Flask backend crashed or stopped | Check the Flask terminal window for Python tracebacks. Re-run `python app.py`. |
| **DHT reads `NaN` or `Humidity: 0.00%`** | Missing 10k pull-up resistor or wrong GPIO | Wire a $10\,\text{k}\Omega$ resistor between DHT Data and 3.3V, and confirm GPIO 4 pin assignment. |
| **MQ-135 reading is stuck near 4095** | Overvoltage or missing voltage divider | Check that the $10\,\text{k}\Omega / 20\,\text{k}\Omega$ voltage divider is connected to GPIO 34. |
