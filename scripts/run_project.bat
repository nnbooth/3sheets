@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "ROOT=%%~fI"
set "SITE_DIR=%ROOT%"
set "SITE_PORT=8080"
set "PY_CMD="

if not exist "%SITE_DIR%\index.html" (
	echo index.html not found at "%SITE_DIR%"
	goto :end
)

where python >nul 2>nul
if not errorlevel 1 set "PY_CMD=python"

if "%PY_CMD%"=="" (
	where py >nul 2>nul
	if not errorlevel 1 set "PY_CMD=py -3"
)

if "%PY_CMD%"=="" (
	echo Python is required but was not found in PATH.
	goto :end
)

echo Starting site on http://127.0.0.1:%SITE_PORT%...
start "" cmd /k "cd /d ""%SITE_DIR%"" && %PY_CMD% -m http.server %SITE_PORT% --bind 127.0.0.1"

echo Waiting for site on port %SITE_PORT%...
powershell -NoProfile -Command "$ready=$false; while(-not $ready){ try { $client = New-Object System.Net.Sockets.TcpClient; $client.Connect('127.0.0.1', %SITE_PORT%); $client.Close(); $ready=$true } catch { Start-Sleep -Seconds 1 } }"

echo Launching site in browser...
start http://127.0.0.1:%SITE_PORT%

:end
endlocal
pause