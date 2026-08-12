@echo off
setlocal

for %%I in ("%~dp0..") do set "PROJECT_ROOT=%%~fI"
set "START_SCRIPT="
for %%F in ("%PROJECT_ROOT%\*.ps1") do set "START_SCRIPT=%%~fF"

if not defined START_SCRIPT (
    echo No PowerShell startup script was found in the project root.
    pause
    exit /b 1
)

rem The independent hidden PowerShell process keeps working after this window closes.
start "" /b powershell.exe -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "%START_SCRIPT%"

if errorlevel 1 (
    echo Failed to launch the project starter.
    pause
    exit /b 1
)

echo Project startup has been sent to the background.
echo Frontend: http://127.0.0.1/
echo Backend:  http://127.0.0.1:9100/docs
exit /b 0
