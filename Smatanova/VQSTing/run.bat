@echo off
rem Spusti listener klavesnic (na pozadi) + Flask appku. Staci dvojklik.
rem Listener nepotrebuje admina: Windows Raw Input je bezne uzivatelske API.
setlocal
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python nie je v PATH.
    echo Nainstaluj ho z https://www.python.org/downloads/ a pri instalacii
    echo zaskrtni "Add python.exe to PATH". Potom spusti run.bat znova.
    pause
    exit /b 1
)

echo Spustam listener klavesnic (minimalizovane okno)...
start "VQSTing listener" /min python "%~dp0tools\windows_keyboard_listener.py"

echo Spustam Flask appku...
python "%~dp0main.py"

echo.
echo Appka skoncila. Listener vypni dvojklikom na stop.bat.
pause
