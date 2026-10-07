@echo off
rem Double-click me on the PC: sets up everything for The Fourth Sheet (safe to run again).
rem Add -Azure after the file name to also sign in to Azure (once the business Microsoft 365 account exists).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup_pc.ps1" %*
echo.
pause
