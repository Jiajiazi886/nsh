@echo off
setlocal
title League Project Starter
cd /d "%~dp0"

echo Starting the current frontend and backend. Please wait...
echo Keep this window open while using the project.
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-current-project.ps1"
set "TASK_EXIT_CODE=%ERRORLEVEL%"

echo.
if not "%TASK_EXIT_CODE%"=="0" (
  echo Startup failed. Please send the error text above to the developer.
  pause
) else (
  echo Project stopped. The frontend and backend are no longer running.
)
exit /b %TASK_EXIT_CODE%
