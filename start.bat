@echo off
title AI-Powered Trading Analysis System
echo.
echo ===================================================================
echo             AI-Powered Trading Analysis System
echo ===================================================================
echo.
echo Starting application...
echo.

:: Check if Python is installed
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed or not in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

:: Check if virtual environment exists, if so, activate it
if exist venv\Scripts\activate.bat (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo No virtual environment found, using system Python.
)

:: Check if required packages are installed
echo Checking dependencies...
python -c "import fastapi, uvicorn" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing dependencies with --user flag to avoid permission issues...
    pip install --user -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo Error installing dependencies.
        echo.
        echo You may need to run this script as administrator or create a virtual environment.
        echo.
        echo To create a virtual environment:
        echo python -m venv venv
        echo venv\Scripts\activate
        echo pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

:: Ensure required directories exist
echo Creating required directories...
if not exist data\sample mkdir data\sample
if not exist results mkdir results

:: Run the application
echo.
echo Launching application...
echo.
python start.py

:: Keep window open if there's an error
if %ERRORLEVEL% neq 0 (
    echo.
    echo An error occurred while running the application.
    pause
) 