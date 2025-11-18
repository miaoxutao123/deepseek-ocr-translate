@echo off
echo Stopping OCR ^& Translation System...
echo.

REM 停止后端
if exist "logs\backend.pid" (
    set /p BACKEND_PID=<logs\backend.pid
    echo Stopping backend (PID: %BACKEND_PID%)...
    taskkill /PID %BACKEND_PID% /F > nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Backend stopped
    ) else (
        echo Backend process not found
    )
    del logs\backend.pid
) else (
    echo Stopping backend by window title...
    taskkill /FI "WINDOWTITLE eq OCR-Backend*" /F > nul 2>&1
)

REM 停止前端
if exist "logs\frontend.pid" (
    set /p FRONTEND_PID=<logs\frontend.pid
    echo Stopping frontend (PID: %FRONTEND_PID%)...
    taskkill /PID %FRONTEND_PID% /F > nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Frontend stopped
    ) else (
        echo Frontend process not found
    )
    del logs\frontend.pid
) else (
    echo Stopping frontend by window title...
    taskkill /FI "WINDOWTITLE eq OCR-Frontend*" /F > nul 2>&1
)

echo.
echo System stopped
pause
