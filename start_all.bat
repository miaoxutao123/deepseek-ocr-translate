@echo off
setlocal enabledelayedexpansion

echo ==========================================
echo OCR ^& Translation System Startup
echo ==========================================
echo.

REM 创建日志目录
if not exist "logs" mkdir logs

REM 1. 检查后端环境
echo Checking backend environment...
if not exist "backend\.venv" (
    echo Error: Virtual environment not found!
    echo Please run: setup_uv.bat
    exit /b 1
)

if not exist "backend\.env" (
    echo Error: .env file not found!
    echo Please create backend\.env file
    exit /b 1
)

REM 2. 启动后端（只监听本地）
echo Starting backend...
cd backend
call .venv\Scripts\activate.bat

REM 读取 .env 配置
set BACKEND_HOST=127.0.0.1
set BACKEND_PORT=8000

if exist .env (
    for /f "tokens=1,2 delims==" %%a in ('findstr /B "HOST= PORT=" .env') do (
        if "%%a"=="HOST" set BACKEND_HOST=%%b
        if "%%a"=="PORT" set BACKEND_PORT=%%b
    )
)

echo Backend will listen on %BACKEND_HOST%:%BACKEND_PORT%

REM 后台启动后端
start "OCR-Backend" /B cmd /c "uvicorn app.main:app --host %BACKEND_HOST% --port %BACKEND_PORT% > ..\logs\backend.log 2>&1"

REM 获取进程 ID
for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq OCR-Backend*" /NH') do (
    set BACKEND_PID=%%a
    echo Backend started with PID: %%a
    echo %%a > ..\logs\backend.pid
    goto :backend_started
)

:backend_started
cd ..

REM 等待后端启动
echo Waiting for backend to initialize...
timeout /t 3 /nobreak > nul

REM 验证后端启动
curl -s http://%BACKEND_HOST%:%BACKEND_PORT%/docs > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is running
) else (
    echo [ERROR] Backend failed to start
    echo Check logs: type logs\backend.log
    exit /b 1
)

REM 3. 启动前端开发服务器
echo.
echo Starting frontend dev server on 127.0.0.1:5173...
cd frontend

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

REM 后台启动前端
start "OCR-Frontend" /B cmd /c "npm run dev > ..\logs\frontend.log 2>&1"

REM 获取进程 ID
for /f "tokens=2" %%a in ('tasklist /FI "WINDOWTITLE eq OCR-Frontend*" /NH') do (
    set FRONTEND_PID=%%a
    echo Frontend started with PID: %%a
    echo %%a > ..\logs\frontend.pid
    goto :frontend_started
)

:frontend_started
cd ..

REM 4. 等待前端启动
echo Waiting for frontend to initialize...
timeout /t 5 /nobreak > nul

echo.
echo ==========================================
echo System started successfully!
echo ==========================================
echo.
echo 📍 Access URLs:
echo    Frontend (Local):   http://127.0.0.1:5173
echo    Frontend (Network): http://%COMPUTERNAME%:5173
echo    Backend (Local):    http://%BACKEND_HOST%:%BACKEND_PORT%/docs
echo.
echo 📝 Logs:
echo    Backend:  type logs\backend.log
echo    Frontend: type logs\frontend.log
echo.
echo 🔧 Process IDs:
echo    Backend:  %BACKEND_PID%
echo    Frontend: %FRONTEND_PID%
echo.
echo ⚠️  Security Note:
echo    - Frontend: Accessible from network (0.0.0.0:5173) for development
echo    - Backend:  Only accessible locally (%BACKEND_HOST%:%BACKEND_PORT%)
echo    - External access requires Nginx proxy in production
echo.
echo 🛑 To stop services:
echo    stop_all.bat
echo.
echo Press any key to keep services running...
echo (Or close this window to stop all services)
pause > nul

REM 用户按键后停止服务
call stop_all.bat
