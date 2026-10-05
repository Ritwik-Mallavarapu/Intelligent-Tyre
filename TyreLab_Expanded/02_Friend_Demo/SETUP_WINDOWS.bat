@echo off
setlocal
cd /d "%~dp0"
set "TL_PY_CMD=py -3.12"
%TL_PY_CMD% --version >nul 2>&1
if not errorlevel 1 goto found
set "TL_PY_CMD=py -3.11"
%TL_PY_CMD% --version >nul 2>&1
if not errorlevel 1 goto found
echo Python 3.11 or 3.12 with the Python launcher is required.
echo Download from https://www.python.org/downloads/windows/
echo Install the Python launcher, then run this setup again.
pause
exit /b 1
:found
%TL_PY_CMD% -m venv .venv
if errorlevel 1 goto fail
.venv\Scripts\python.exe -m pip install --disable-pip-version-check -r requirements.txt
if errorlevel 1 goto fail
.venv\Scripts\python.exe CHECK_INSTALLATION.py
if errorlevel 1 goto fail
echo.
echo Setup complete. Double-click START_DEMO.bat.
echo Keep the console open and select modes on the website.
pause
exit /b 0
:fail
echo.
echo SETUP FAILED. Read the error above.
echo Check internet access and extract all files to a writable folder.
echo Do not run the setup from inside the ZIP.
pause
exit /b 1
