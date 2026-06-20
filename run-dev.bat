@echo off
setlocal

cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-dev.ps1"

if errorlevel 1 (
  echo.
  echo CampusKart failed to start. Check the error above.
  pause
)
