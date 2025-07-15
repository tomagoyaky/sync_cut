@echo off
cls
REM Sync Cut Application Startup Script
REM This script creates a virtual environment, installs dependencies, and starts the application

echo Starting Sync Cut Application...

REM Set the project directory
set PROJECT_DIR=%~dp0
cd /d "%PROJECT_DIR%"

REM Check if virtual environment exists
if not exist "workspace\venv" (
    echo Creating virtual environment...
    python -m venv workspace\venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        echo Please ensure Python is installed and added to PATH
        pause
        exit /b 1
    )
) else (
    echo Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call workspace\venv\Scripts\activate.bat

REM Check if requirements were already installed by checking for a marker file
if not exist "workspace\status\.deps_installed" (
    echo Upgrading pip...
    python -m pip install --upgrade pip
    
    echo Installing dependencies...
    pip install -r plugins\requirements.txt || exit /b 1
    
    REM Create marker file to indicate dependencies are installed
    echo Dependencies installed on %date% %time% > workspace\status\.deps_installed
    echo Dependencies installed successfully
) else (
    echo Dependencies already installed, skipping installation
)

REM Ensure workspace directories exist
echo Ensuring workspace directories exist...
if not exist "workspace\models" mkdir workspace\models
if not exist "workspace\logs" mkdir workspace\logs
if not exist "workspace\upload" mkdir workspace\upload
if not exist "workspace\tmp" mkdir workspace\tmp
if not exist "workspace\status" mkdir workspace\status

REM Add FFmpeg tools to PATH
echo Adding FFmpeg tools to PATH...
set PATH=%PROJECT_DIR%plugins\tools;%PATH%

REM Start the application
python plugins\web_app\run.py

REM Deactivate virtual environment when done
deactivate

echo Application stopped
pause 