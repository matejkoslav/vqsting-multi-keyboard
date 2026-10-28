@echo off
rem Vypne listener klavesnic podla pid suboru. Staci dvojklik.
rem Cestu k pid suboru pocita state_paths.py, rovnako ako listener.
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python nie je v PATH.
    echo Nainstaluj ho z https://www.python.org/downloads/ a pri instalacii
    echo zaskrtni "Add python.exe to PATH".
    pause
    exit /b 1
)

set "PIDFILE="
for /f "delims=" %%P in ('python -c "import state_paths;print(state_paths.pid_file())"') do set "PIDFILE=%%P"
if not defined PIDFILE (
    echo Nepodarilo sa zistit cestu k pid suboru.
    pause
    exit /b 1
)
if not exist "%PIDFILE%" (
    echo Listener nebezi.
    pause
    exit /b 0
)

set "LISTENER_PID="
set /p LISTENER_PID=<"%PIDFILE%"
if not defined LISTENER_PID (
    echo Prazdny pid subor: "%PIDFILE%"
    pause
    exit /b 1
)

taskkill /F /PID %LISTENER_PID% >nul 2>&1
if errorlevel 1 (
    echo Listener s pid %LISTENER_PID% uz nebezi.
) else (
    echo Listener zastaveny ^(pid %LISTENER_PID%^).
)
del "%PIDFILE%" >nul 2>&1
pause
