@echo off
REM Maverick launcher (double-click). Runs start.ps1 with ExecutionPolicy bypass.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
pause
