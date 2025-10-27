@echo off
echo ========================================
echo Starting YT2Medium Flask App
echo ========================================
echo.

if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
    echo Virtual environment activated
) else (
    echo No virtual environment found
)

echo.
echo Starting Flask app on http://localhost:8000
echo Press Ctrl+C to stop
echo.

python app.py
