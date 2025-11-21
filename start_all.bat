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
    echo Please run: cd backend ^&^& python -m venv .venv ^&^& .venv\Scripts\activate ^&^& pip install -r requirements.txt
    exit /b 1
)

if not exist "backend\.env" (
    echo Error: .env file not found!
    echo Please copy backend\.env.example to backend\.env and configure it
    exit /b 1
)

REM 2. 启动后端
echo Starting backend...
cd backend

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

REM 在新窗口启动后端
start "OCR-Backend" cmd /c ".venv\Scripts\activate.bat && uvicorn app.main:app --host %BACKEND_HOST% --port %BACKEND_PORT%"

cd ..

REM 等待后端启动
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

REM 验证后端启动
curl -s http://%BACKEND_HOST%:%BACKEND_PORT%/health > nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is running
) else (
    echo [WARNING] Backend may still be starting...
)

REM 3. 启动前端开发服务器
echo.
echo Starting frontend dev server...
cd frontend

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

REM 在新窗口启动前端
start "OCR-Frontend" cmd /c "npm run dev"

cd ..

REM 4. 等待前端启动
echo Waiting for frontend to initialize...
timeout /t 5 /nobreak > nul

echo.
echo ==========================================
echo System started successfully!
echo ==========================================
echo.
echo Access URLs:
echo    Frontend: http://localhost:5173
echo    Backend:  http://%BACKEND_HOST%:%BACKEND_PORT%/docs
echo.
echo Two new windows have been opened:
echo    - OCR-Backend: Backend server
echo    - OCR-Frontend: Frontend dev server
echo.
echo To stop services, close those windows or run: stop_all.bat
echo.
