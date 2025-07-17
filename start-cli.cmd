@echo off
REM Sync Cut CLI - Simplified Command Line Interface
REM Converts MP4 videos to TXT/SRT subtitles with optional engine selection
REM 
REM Usage:
REM   start-cli.cmd <input.mp4>                           - Convert using Whisper engine
REM   start-cli.cmd <input.mp4> <engine>                  - Convert using specified engine (whisper/alibaba_nls)
REM   start-cli.cmd <input.mp4> <engine> <output_folder>  - Convert to specified output folder
REM
REM Examples:
REM   start-cli.cmd demo.mp4
REM   start-cli.cmd demo.mp4 whisper
REM   start-cli.cmd demo.mp4 alibaba_nls output_folder

setlocal enabledelayedexpansion

REM Script configuration
set SCRIPT_NAME=Sync Cut CLI
set SCRIPT_VERSION=1.0.0
set PYTHON_MIN_VERSION=3.8

REM Colors for output (if supported)
set COLOR_INFO=[96m
set COLOR_SUCCESS=[92m
set COLOR_WARNING=[93m
set COLOR_ERROR=[91m
set COLOR_RESET=[0m

echo.
echo %COLOR_INFO%===============================================%COLOR_RESET%
echo %COLOR_INFO%   %SCRIPT_NAME% v%SCRIPT_VERSION%%COLOR_RESET%
echo %COLOR_INFO%   MP4 to TXT/SRT Conversion Tool%COLOR_RESET%
echo %COLOR_INFO%===============================================%COLOR_RESET%
echo.

REM Parse command line arguments
if "%~1"=="" goto show_usage
if "%~1"=="-h" goto show_usage
if "%~1"=="--help" goto show_usage
if "%~1"=="/?" goto show_usage

set INPUT_FILE=%~1
set ENGINE=%~2
set OUTPUT_FOLDER=%~3

REM Set default engine if not specified
if "%ENGINE%"=="" set ENGINE=whisper

REM Validate engine
if /i not "%ENGINE%"=="whisper" if /i not "%ENGINE%"=="alibaba_nls" (
    echo %COLOR_ERROR%Error: Invalid engine '%ENGINE%'%COLOR_RESET%
    echo Supported engines: whisper, alibaba_nls
    echo.
    goto show_usage
)

REM Check if input file exists
if not exist "%INPUT_FILE%" (
    echo %COLOR_ERROR%Error: Input file not found: %INPUT_FILE%%COLOR_RESET%
    echo.
    goto show_usage
)

REM Get input file info
for %%F in ("%INPUT_FILE%") do (
    set INPUT_NAME=%%~nF
    set INPUT_EXT=%%~xF
    set INPUT_DIR=%%~dpF
)

REM Validate input file extension
set VALID_EXT=0
for %%E in (.mp4 .avi .mov .mkv .flv .wmv) do (
    if /i "%INPUT_EXT%"=="%%E" set VALID_EXT=1
)

if %VALID_EXT%==0 (
    echo %COLOR_WARNING%Warning: Input file extension '%INPUT_EXT%' may not be supported%COLOR_RESET%
    echo Supported extensions: .mp4, .avi, .mov, .mkv, .flv, .wmv
    echo.
)

REM Determine output directory
if "%OUTPUT_FOLDER%"=="" (
    set OUTPUT_DIR=%INPUT_DIR%
) else (
    set OUTPUT_DIR=%OUTPUT_FOLDER%\
    if not exist "%OUTPUT_FOLDER%" (
        echo %COLOR_INFO%Creating output directory: %OUTPUT_FOLDER%%COLOR_RESET%
        mkdir "%OUTPUT_FOLDER%" 2>nul
        if errorlevel 1 (
            echo %COLOR_ERROR%Error: Cannot create output directory: %OUTPUT_FOLDER%%COLOR_RESET%
            goto error_exit
        )
    )
)

REM Generate output file paths
set OUTPUT_TXT=%OUTPUT_DIR%%INPUT_NAME%.txt
set OUTPUT_SRT=%OUTPUT_DIR%%INPUT_NAME%.srt

echo %COLOR_INFO%Configuration:%COLOR_RESET%
echo   Input file: %INPUT_FILE%
echo   Engine: %ENGINE%
echo   Output TXT: %OUTPUT_TXT%
echo   Output SRT: %OUTPUT_SRT%
echo.

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo %COLOR_ERROR%Error: Python is not installed or not in PATH%COLOR_RESET%
    echo Please install Python %PYTHON_MIN_VERSION% or later from: https://python.org
    goto error_exit
)

REM Get Python version
for /f "tokens=2" %%V in ('python --version 2^>^&1') do set PYTHON_VERSION=%%V
echo %COLOR_INFO%Python version: %PYTHON_VERSION%%COLOR_RESET%

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo %COLOR_INFO%Activating virtual environment...%COLOR_RESET%
    call venv\Scripts\activate.bat
) else (
    echo %COLOR_WARNING%Virtual environment not found. Using system Python...%COLOR_RESET%
    echo %COLOR_INFO%To create a virtual environment, run:%COLOR_RESET%
    echo   python -m venv venv
    echo   venv\Scripts\activate.bat
    echo   pip install -r plugins\requirements.txt
    echo.
)

REM Check if project files exist
if not exist "plugins\mp4_to_txt_cli.py" (
    echo %COLOR_ERROR%Error: Sync Cut project files not found%COLOR_RESET%
    echo Please run this script from the Sync Cut project root directory
    goto error_exit
)

REM Check dependencies
echo %COLOR_INFO%Checking dependencies...%COLOR_RESET%

REM Check basic dependencies
python -c "import yaml, pathlib" >nul 2>&1
if errorlevel 1 (
    echo %COLOR_WARNING%Installing basic dependencies...%COLOR_RESET%
    pip install pyyaml
)

REM Check engine-specific dependencies
if /i "%ENGINE%"=="whisper" (
    python -c "import faster_whisper" >nul 2>&1
    if errorlevel 1 (
        echo %COLOR_WARNING%Whisper engine not available. Installing faster-whisper...%COLOR_RESET%
        echo This may take a few minutes...
        pip install faster-whisper torch torchaudio
        if errorlevel 1 (
            echo %COLOR_ERROR%Error: Failed to install Whisper dependencies%COLOR_RESET%
            echo You can try installing manually:
            echo   pip install faster-whisper torch torchaudio
            goto error_exit
        )
    )
) else (
    python -c "import websocket" >nul 2>&1
    if errorlevel 1 (
        echo %COLOR_WARNING%Alibaba NLS engine not available. Installing websocket-client...%COLOR_RESET%
        pip install websocket-client
        if errorlevel 1 (
            echo %COLOR_ERROR%Error: Failed to install Alibaba NLS dependencies%COLOR_RESET%
            echo You can try installing manually:
            echo   pip install websocket-client
            goto error_exit
        )
    )
)

echo %COLOR_SUCCESS%Dependencies OK%COLOR_RESET%
echo.

REM Run the conversion
echo %COLOR_INFO%Starting conversion...%COLOR_RESET%
echo.

python plugins\mp4_to_txt_cli.py "%INPUT_FILE%" "%OUTPUT_TXT%" "%OUTPUT_SRT%" --engine %ENGINE%

if errorlevel 1 (
    echo.
    echo %COLOR_ERROR%Conversion failed!%COLOR_RESET%
    echo.
    echo %COLOR_INFO%Troubleshooting tips:%COLOR_RESET%
    echo   1. Check if the input file is valid and not corrupted
    echo   2. Ensure you have enough disk space
    echo   3. For Alibaba NLS, check your configuration in config.yaml
    echo   4. For Whisper, ensure sufficient RAM (model dependent)
    echo   5. Run with --verbose flag for detailed error information:
    echo      python plugins\mp4_to_txt_cli.py "%INPUT_FILE%" "%OUTPUT_TXT%" "%OUTPUT_SRT%" --engine %ENGINE% --verbose
    goto error_exit
) else (
    echo.
    echo %COLOR_SUCCESS%===============================================%COLOR_RESET%
    echo %COLOR_SUCCESS%   Conversion completed successfully!%COLOR_RESET%
    echo %COLOR_SUCCESS%===============================================%COLOR_RESET%
    echo.
    
    REM Show output file information
    if exist "%OUTPUT_TXT%" (
        for %%F in ("%OUTPUT_TXT%") do set TXT_SIZE=%%~zF
        echo %COLOR_SUCCESS%TXT file: %OUTPUT_TXT% (!TXT_SIZE! bytes)%COLOR_RESET%
    )
    
    if exist "%OUTPUT_SRT%" (
        for %%F in ("%OUTPUT_SRT%") do set SRT_SIZE=%%~zF
        echo %COLOR_SUCCESS%SRT file: %OUTPUT_SRT% (!SRT_SIZE! bytes)%COLOR_RESET%
    )
    
    echo.
    echo %COLOR_INFO%You can now:%COLOR_RESET%
    echo   - Open the TXT file in any text editor
    echo   - Import the SRT file into video players or editing software
    echo   - Use the files for transcription, subtitles, or further processing
)

goto normal_exit

:show_usage
echo Usage: %~nx0 ^<input_file^> [engine] [output_folder]
echo.
echo Arguments:
echo   input_file     Input MP4/video file path
echo   engine         Speech recognition engine (whisper or alibaba_nls)
echo                  Default: whisper
echo   output_folder  Output directory for generated files
echo                  Default: same as input file directory
echo.
echo Examples:
echo   %~nx0 demo.mp4
echo   %~nx0 demo.mp4 whisper
echo   %~nx0 demo.mp4 alibaba_nls output_folder
echo   %~nx0 "C:\Videos\my video.mp4" whisper "C:\Transcripts"
echo.
echo Engines:
echo   whisper     - Local speech recognition (no internet required)
echo                 Supports multiple languages, good accuracy
echo                 Requires: faster-whisper, torch
echo.
echo   alibaba_nls - Alibaba Cloud speech recognition (internet required)
echo                 Requires: websocket-client and valid Alibaba Cloud credentials
echo                 Configure in config.yaml file
echo.
echo Notes:
echo   - Output files will be: input_name.txt and input_name.srt
echo   - For Alibaba NLS, configure credentials in config.yaml
echo   - Use quotes around file paths with spaces
echo   - First run may take longer due to model downloads (Whisper)
echo.
goto normal_exit

:error_exit
echo.
echo %COLOR_ERROR%Process terminated with errors.%COLOR_RESET%
pause
exit /b 1

:normal_exit
echo.
pause
exit /b 0