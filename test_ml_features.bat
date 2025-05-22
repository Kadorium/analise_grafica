@echo off
echo.
echo =====================================
echo Testing ML Signal Generator Features
echo =====================================
echo.
echo Starting the AI Trading Analysis System with ML features...
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Check if the virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found. Please run setup first.
    pause
    exit /b 1
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install additional ML dependencies if needed
echo Installing/updating ML dependencies...
pip install scikit-learn --quiet

REM Start the application
echo.
echo Starting FastAPI server...
echo Access the application at: http://127.0.0.1:8000
echo.
echo ML Features to Test:
echo - Upload multi-asset data in Data tab
echo - Go to Screener tab
echo - Enable "Include ML Signals" toggle
echo - Select strategies and run screener
echo - Check for LogisticRegression signals in results
echo - Verify accuracy column shows ML model performance
echo.

python app.py 