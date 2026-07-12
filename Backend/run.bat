@echo off
echo ================================
echo TransitOps - Smart Transport Platform
echo Backend Server Startup (Windows)
echo ================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [FAILED] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] %PYTHON_VERSION%
echo.

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo [INFO] Installing dependencies...
pip install -q -r requirements.txt
if %errorlevel% neq 0 (
    echo [FAILED] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed
echo.

REM Create .env if it doesn't exist
if not exist ".env" (
    echo [INFO] Creating .env file from template...
    copy .env.example .env
    echo [OK] .env file created
)

echo.
echo ================================
echo [START] TransitOps Backend Server
echo ================================
echo.
echo Server running at: http://localhost:8000
echo.
echo API Documentation:
echo    - Swagger UI: http://localhost:8000/docs
echo    - ReDoc: http://localhost:8000/redoc
echo.
echo Testing:
echo    - See TESTING_GUIDE.md for curl examples
echo    - See API_CONTRACTS.json for endpoint details
echo.
echo Press Ctrl+C to stop the server
echo.

REM Run the server
python main.py

pause
