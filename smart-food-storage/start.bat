@echo off
setlocal enabledelayedexpansion

echo =====================================================================
echo    SMART FOOD STORAGE SPOILAGE PREDICTOR - SYSTEM LAUNCHER
echo =====================================================================
echo.

:: Resolve Project Root Directory
set "PROJECT_ROOT=%~dp0"
if exist "%PROJECT_ROOT%smart-food-storage\backend" (
    set "PROJECT_ROOT=%PROJECT_ROOT%smart-food-storage\"
)
set "BACKEND_DIR=%PROJECT_ROOT%backend"
set "FRONTEND_DIR=%PROJECT_ROOT%frontend"

:: 1. Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in PATH!
    echo Please install Python 3.10+ and restart.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
echo [OK] Detected %PYTHON_VER%

:: 2. Check Node.js
node -v >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is not installed or not in PATH!
    echo Please install Node.js 18+ and restart.
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('node -v 2^>^&1') do set NODE_VER=%%i
echo [OK] Detected Node.js %NODE_VER%

:: 3. Setup Backend Dependencies
echo.
echo [*] Checking Backend Dependencies...
cd /d "%BACKEND_DIR%"
python -m pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [WARNING] Failed to install some requirements, retrying with standard pip...
    python -m pip install -r requirements.txt
)
echo [OK] Backend dependencies verified.

:: 4. Initialize SQLite Database
echo.
echo [*] Initializing SQLite database (food_storage.db)...
python -c "import database; database.init_db(); print('[OK] Database initialized and seeded successfully.')"

:: Detect LAN IPv4 for ESP32 configuration
for /f "tokens=*" %%a in ('python -c "import socket; s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(('8.8.8.8', 80)); print(s.getsockname()[0]); s.close()" 2^>nul') do set LAN_IP=%%a
if "%LAN_IP%"=="" set LAN_IP=127.0.0.1

:: Return to Project Root
cd /d "%PROJECT_ROOT%"

:: 5. Setup Frontend Dependencies
echo.
echo [*] Checking Frontend Dependencies...
cd /d "%FRONTEND_DIR%"
if not exist "node_modules" (
    echo [*] Installing frontend dependencies [first run]...
    call npm install
) else (
    echo [OK] Frontend node_modules already installed.
)

:: Return to Project Root
cd /d "%PROJECT_ROOT%"

:: 6. Launch Backend and Frontend in separate windows
echo.
echo =====================================================================
echo    STARTING LOCAL SERVICES
echo    Local Dashboard  : http://localhost:5173
echo    Backend REST API : http://127.0.0.1:5000
echo    ESP32 LAN Ingest : http://%LAN_IP%:5000/api/sensor-data
echo =====================================================================
echo.

start "Smart Food Storage - Backend (Flask)" /D "%BACKEND_DIR%" cmd /k "python app.py"

start "Smart Food Storage - Frontend (Vite)" /D "%FRONTEND_DIR%" cmd /k "npm run dev"

:: Wait 3 seconds then open browser
ping 127.0.0.1 -n 4 >nul
echo [*] Opening browser at http://localhost:5173 ...
start http://localhost:5173

echo.
echo [DONE] Application is running!
echo Press any key in this window to exit this launcher (services keep running in their own windows).
pause >nul
