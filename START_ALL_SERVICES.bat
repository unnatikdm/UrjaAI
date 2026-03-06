@echo off
REM ============================================================================
REM  UrjaAI Special Features - Multi-Service Startup Script
REM ============================================================================
REM
REM This script starts all three required services for the UrjaAI platform
REM with integrated browniepoint1 and browniepoint2 features.
REM
REM Prerequisites:
REM   - Python 3.8+ installed
REM   - Node.js 16+ installed
REM   - All dependencies installed (requirements.txt, package.json)
REM
REM Usage: Start this script, then open a browser to http://localhost:5173
REM ============================================================================

setlocal enabledelayedexpansion

echo.
echo ============================================================================
echo  UrjaAI Special Features - Starting All Services
echo ============================================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    pause
    exit /b 1
)

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js is not installed. Please install Node.js 16 or higher.
    pause
    exit /b 1
)

echo [INFO] Python and Node.js detected. Starting services...
echo.

REM Get the script directory
set SERVER_DIR=%~dp0

REM Start Terminal 1: UrjaAI Backend
echo [INFO] Terminal 1: Starting UrjaAI Backend (FastAPI on port 8000)...
cd /d "%SERVER_DIR%UrjaAI\backend"
start "UrjaAI Backend" cmd /k "python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 2

REM Start Terminal 2: Browniepoint1 (Carbon Tracker)
echo [INFO] Terminal 2: Starting Browniepoint1 - Carbon Tracker (Flask on port 5000)...
cd /d "%SERVER_DIR%browniepoint1"
start "Browniepoint1 - Carbon Tracker" cmd /k "python api_server.py"
timeout /t 2

REM Start Terminal 3: Browniepoint2 (ML Platform)
echo [INFO] Terminal 3: Starting Browniepoint2 - TabTransformer ML (FastAPI on port 8001)...
cd /d "%SERVER_DIR%browniepoint2"
start "Browniepoint2 - TabTransformer ML" cmd /k "python main_app.py"
timeout /t 2

REM Start Terminal 4: UrjaAI Frontend
echo [INFO] Terminal 4: Starting UrjaAI Frontend (Vite on port 5173)...
cd /d "%SERVER_DIR%UrjaAI\frontend"
start "UrjaAI Frontend" cmd /k "npm run dev"
timeout /t 2

echo.
echo ============================================================================
echo [SUCCESS] All services started successfully!
echo ============================================================================
echo.
echo Service URLs:
echo   Frontend Dashboard: http://localhost:5173
echo   Special Features:  http://localhost:5173/special-features
echo   UrjaAI API Docs:   http://localhost:8000/docs
echo   Browniepoint1:     http://localhost:5000
echo   Browniepoint2:     http://localhost:8001/docs
echo.
echo Quick Links:
echo   1. Login to http://localhost:5173/login
echo   2. Navigate to Special Features (icon in header)
echo   3. Switch between Carbon Tracker and ML Platform tabs
echo.
echo Note: Close any terminal window to stop that service
echo ============================================================================
echo.

pause
