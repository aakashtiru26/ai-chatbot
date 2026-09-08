@echo off
echo ============================================================
echo   Setting up AI Chatbot on Windows...
echo ============================================================

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH!
    echo Please install Python 3.10+ from https://www.python.org/
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment (venv)...
    python -m venv venv
)

call venv\Scripts\activate.bat

echo Installing requirements from requirements.txt...
pip install -r requirements.txt

echo.
echo ============================================================
echo   Starting AI Chatbot Server at http://127.0.0.1:8000
echo ============================================================
uvicorn server:app --reload --host 127.0.0.1 --port 8000

pause
