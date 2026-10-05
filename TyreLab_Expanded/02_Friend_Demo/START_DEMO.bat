@echo off
setlocal
cd /d "%~dp0"
title Entra Intelligent Tyre Dashboard - Keep this window open
if exist .venv\Scripts\python.exe (
 .venv\Scripts\python.exe -c "import sys; assert sys.version_info[:2] in [(3,11),(3,12)]" >nul 2>&1
 if not errorlevel 1 (
  .venv\Scripts\python.exe launcher.py
  goto finished
 )
)
py -3.12 -c "import sys" >nul 2>&1
if not errorlevel 1 (
 py -3.12 launcher.py
 goto finished
)
py -3.11 -c "import sys" >nul 2>&1
if not errorlevel 1 (
 py -3.11 launcher.py
 goto finished
)
python -c "import sys; assert sys.version_info[:2] in [(3,11),(3,12)]" >nul 2>&1
if not errorlevel 1 (
 python launcher.py
 goto finished
)
echo START FAILED: Install Python 3.11 or 3.12 with the Python launcher.
echo Then double-click START_DEMO.bat again. Extract the ZIP before running.
:finished
echo.
echo If startup failed, send the error printed above. Do not close the running server window.
pause
