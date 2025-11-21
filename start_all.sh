#!/bin/bash

echo "=========================================="
echo "OCR & Translation System Startup"
echo "=========================================="
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 创建日志目录
mkdir -p logs

# 1. 检查后端环境
echo "Checking backend environment..."
if [ ! -d "backend/.venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run:"
    echo "  cd backend"
    echo "  python -m venv .venv"
    echo "  source .venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

if [ ! -f "backend/.env" ]; then
    echo "Error: .env file not found!"
    echo "Please copy backend/.env.example to backend/.env and configure it"
    exit 1
fi

# 2. 启动后端
echo "Starting backend..."

# 读取 .env 配置
BACKEND_HOST=$(grep -E '^HOST=' backend/.env 2>/dev/null | head -1 | cut -d '=' -f2 | tr -d ' \r\n')
BACKEND_PORT=$(grep -E '^PORT=' backend/.env 2>/dev/null | head -1 | cut -d '=' -f2 | tr -d ' \r\n')

# 使用默认值
BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
BACKEND_PORT=${BACKEND_PORT:-8000}

echo "Backend will listen on ${BACKEND_HOST}:${BACKEND_PORT}"

# 后台启动后端
cd backend
nohup bash -c "source .venv/bin/activate && python run.py" > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo $BACKEND_PID > ../logs/backend.pid
cd ..

# 等待后端启动
echo "Waiting for backend to initialize..."
sleep 5

# 验证后端启动
if curl -s "http://${BACKEND_HOST}:${BACKEND_PORT}/health" > /dev/null 2>&1; then
    echo "[OK] Backend is running"
else
    echo "[WARNING] Backend may still be starting, check logs/backend.log"
fi

# 3. 启动前端
echo ""
echo "Starting frontend dev server..."

cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# 后台启动前端（使用 --host 确保可以外部访问）
nohup npm run dev -- --host > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
echo $FRONTEND_PID > ../logs/frontend.pid
cd ..

# 等待前端启动
echo "Waiting for frontend to initialize..."
sleep 5

# 验证前端启动
if curl -s "http://127.0.0.1:5173" > /dev/null 2>&1; then
    echo "[OK] Frontend is running"
else
    echo "[WARNING] Frontend may still be starting, check logs/frontend.log"
fi

echo ""
echo "=========================================="
echo "System started!"
echo "=========================================="
echo ""
echo "Access URLs:"
echo "   Frontend: http://localhost:5173"
echo "   Backend:  http://${BACKEND_HOST}:${BACKEND_PORT}/docs"
echo ""
echo "Logs:"
echo "   tail -f logs/backend.log"
echo "   tail -f logs/frontend.log"
echo ""
echo "Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "To stop services:"
echo "   bash stop_all.sh"
echo ""
