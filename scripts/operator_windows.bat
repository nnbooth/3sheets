@echo off
setlocal

set "ROOT=%~dp0.."

if "%~1"=="" goto :usage

if /I "%~1"=="status" goto :status
if /I "%~1"=="refresh-legal" goto :refresh
if /I "%~1"=="start" goto :start
if /I "%~1"=="full-refresh" goto :full
goto :usage

:status
echo Project root: %ROOT%
echo.
where node >nul 2>nul && (node -v) || echo node: missing
where npm >nul 2>nul && (npm -v) || echo npm: missing
where python >nul 2>nul && (python --version) || echo python: missing
echo.
echo Check simple-reporting-site: http://127.0.0.1:8080
goto :end

:refresh
echo Step 1/3: Generate Legal CSV dataset
python "%ROOT%\Legal\scripts\build_legal_reporting_dataset.py"
if errorlevel 1 goto :error

echo Step 2/3: Import Legal dataset into PostgreSQL
python "%ROOT%\Legal\scripts\importLegaldb.py"
if errorlevel 1 goto :error

echo Step 3/3: Build Legal reporting views
python "%ROOT%\Legal\scripts\build_legal_models.py"
if errorlevel 1 goto :error

echo.
echo Legal refresh complete.
goto :end

:start
call "%ROOT%\run_project.bat"
goto :end

:full
call "%~f0" refresh-legal
if errorlevel 1 goto :error
call "%ROOT%\run_project.bat"
goto :end

:usage
echo Usage: scripts\operator_windows.bat ^<command^>
echo.
echo Commands:
echo   status
echo   refresh-legal
echo   start
echo   full-refresh
exit /b 1

:error
echo.
echo Command failed. Review the error output above.
exit /b 1

:end
endlocal
