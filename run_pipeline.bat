@echo off
REM ============================================================================
REM Dagster Pipeline Control Script for Windows
REM ============================================================================
REM
REM Usage:
REM   run_pipeline.bat                    - Start Dagster Web UI
REM   run_pipeline.bat install            - Install dependencies
REM   run_pipeline.bat ingestion          - Run ingestion only
REM   run_pipeline.bat complete           - Run complete pipeline
REM   run_pipeline.bat help               - Show this help
REM

setlocal enabledelayedexpansion

REM Get project root
set PROJECT_ROOT=%~dp0

REM Color codes
set "COLOR_INFO=[32m"
set "COLOR_ERROR=[31m"
set "COLOR_RESET=[0m"

REM Show menu if no argument
if "%1"=="" (
    call :show_menu
    goto end
)

REM Process arguments
if /i "%1"=="help" goto help
if /i "%1"=="install" goto install
if /i "%1"=="ui" goto ui
if /i "%1"=="ingestion" goto ingestion
if /i "%1"=="complete" goto complete
if /i "%1"=="check" goto check

echo Error: Unknown command '%1'
goto help

REM ============================================================================
REM Functions
REM ============================================================================

:help
echo.
echo ============================================================================
echo RECOMART DAGSTER PIPELINE - WINDOWS COMMAND SCRIPT
echo ============================================================================
echo.
echo Usage: run_pipeline.bat [COMMAND]
echo.
echo Commands:
echo   (none)      - Show interactive menu
echo   install     - Install dependencies (pip install -r requirements.txt)
echo   ui          - Start Dagster Web UI (http://localhost:3000)
echo   ingestion   - Run data ingestion pipeline
echo   complete    - Run complete end-to-end pipeline
echo   check       - Check Dagster installation
echo   help        - Show this help message
echo.
echo Quick Start:
echo   1. run_pipeline.bat install
echo   2. run_pipeline.bat ui
echo   3. Open http://localhost:3000 in your browser
echo.
echo For detailed docs: see docs/DAGSTER_QUICKSTART.md
echo ============================================================================
echo.
goto end

:show_menu
echo.
echo ============================================================================
echo RECOMART DAGSTER PIPELINE - INTERACTIVE MENU
echo ============================================================================
echo.
echo 1. Start Web UI (recommended)
echo 2. Install Dependencies
echo 3. Run Ingestion Only
echo 4. Run Complete Pipeline
echo 5. Check Installation
echo 6. Show Help
echo 7. Exit
echo.
set /p choice="Enter your choice (1-7): "

if "%choice%"=="1" goto ui
if "%choice%"=="2" goto install
if "%choice%"=="3" goto ingestion
if "%choice%"=="4" goto complete
if "%choice%"=="5" goto check
if "%choice%"=="6" goto help
if "%choice%"=="7" goto end

echo Invalid choice. Please select 1-7.
goto show_menu

:check
echo.
echo Checking Dagster installation...
python -m dagster --version
if errorlevel 1 (
    echo Error: Dagster not found. Run: run_pipeline.bat install
    goto end
)
echo Success: Dagster is installed and ready.
goto end

:install
echo.
echo ============================================================================
echo Installing dependencies...
echo ============================================================================
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Installation failed
    goto end
)
echo.
echo ============================================================================
echo Installation complete! Next steps:
echo   1. run_pipeline.bat ui
echo   2. Open http://localhost:3000
echo ============================================================================
goto end

:ui
echo.
echo ============================================================================
echo Starting Dagster Web UI
echo ============================================================================
echo.
echo Opening Dagster at http://localhost:3000
echo Press Ctrl+C to stop the server
echo.
cd /d "%PROJECT_ROOT%"
dagster dev
goto end

:ingestion
echo.
echo ============================================================================
echo Running Data Ingestion Pipeline
echo ============================================================================
echo.
cd /d "%PROJECT_ROOT%"
python -m dagster job execute -f src/orchestration/dagster_pipeline.py -j ingestion_job
echo.
echo Pipeline completed.
pause
goto end

:complete
echo.
echo ============================================================================
echo Running Complete End-to-End Pipeline
echo ============================================================================
echo.
echo This may take 10-15 seconds...
echo.
cd /d "%PROJECT_ROOT%"
python -m dagster job execute -f src/orchestration/dagster_pipeline.py -j complete_pipeline_job
echo.
echo Pipeline completed.
pause
goto end

:end
endlocal
exit /b 0
