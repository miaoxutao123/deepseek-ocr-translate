#!/bin/bash

echo "=========================================="
echo "OCR & Translation System Startup"
echo "=========================================="
echo ""

# 创建日志目录
mkdir -p logs

# 1. 检查后端环境
echo "Checking backend environment..."
if [ ! -d "backend/.venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run: bash setup_uv.sh"
    exit 1
fi

if [ ! -f "backend/.env" ]; then
    echo "Error: .env file not found!"
    echo "Please create backend/.env file"
    exit 1
fi

# 2. 启动后端（只监听本地）
echo "Starting backend..."
cd backend
source .venv/bin/activate

# 读取 .env 配置中的 HOST 和 PORT（处理可能的空格和注释）
BACKEND_HOST=$(grep -E '^HOST=' .env 2>/dev/null | head -1 | cut -d '=' -f2 | tr -d ' \r\n')
BACKEND_PORT=$(grep -E '^PORT=' .env 2>/dev/null | head -1 | cut -d '=' -f2 | tr -d ' \r\n')

# 使用默认值如果没有配置
BACKEND_HOST=${BACKEND_HOST:-127.0.0.1}
BACKEND_PORT=${BACKEND_PORT:-8000}

echo "Backend configuration from .env:"
echo "  HOST: ${BACKEND_HOST}"
echo "  PORT: ${BACKEND_PORT}"
echo "Backend will listen on ${BACKEND_HOST}:${BACKEND_PORT}"

# 后台启动后端（使用详细日志模式）
echo "使用详细日志模式启动后端..."
export HOST=${BACKEND_HOST}
export PORT=${BACKEND_PORT}
nohup python run.py > ../logs/backend.log 2>&1 &
BACKEND_PID=$!
echo "Backend started with PID: $BACKEND_PID"
echo $BACKEND_PID > ../logs/backend.pid

cd ..

# 等待后端启动
echo "Waiting for backend to initialize..."
sleep 3

# 验证后端启动
if curl -s http://${BACKEND_HOST}:${BACKEND_PORT}/docs > /dev/null; then
    echo "✓ Backend is running"
else
    echo "✗ Backend failed to start"
    echo "Check logs: tail -f logs/backend.log"
    exit 1
fi

# 3. 启动前端开发服务器
echo ""
echo "Starting frontend dev server on 127.0.0.1:5173..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# 后台启动前端
nohup npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "Frontend started with PID: $FRONTEND_PID"
echo $FRONTEND_PID > ../logs/frontend.pid

cd ..

# 4. 等待前端启动
echo "Waiting for frontend to initialize..."
sleep 5

echo ""
echo "=========================================="
echo "System started successfully!"
echo "=========================================="
echo ""
echo "📍 Access URLs:"
echo "   Frontend (Local):   http://127.0.0.1:5173"
echo "   Frontend (Network): http://$(hostname -I | awk '{print $1}'):5173"
echo "   Backend (Local):    http://${BACKEND_HOST}:${BACKEND_PORT}/docs"
echo ""
echo "📝 Logs:"
echo "   Backend:  tail -f logs/backend.log"
echo "   Frontend: tail -f logs/frontend.log"
echo ""
echo "🔧 Process IDs:"
echo "   Backend:  $BACKEND_PID"
echo "   Frontend: $FRONTEND_PID"
echo ""
echo "⚠️  Security Note:"
echo "   - Frontend: Accessible from network (0.0.0.0:5173) for development"
echo "   - Backend:  Only accessible locally (${BACKEND_HOST}:${BACKEND_PORT})"
echo "   - External access requires Nginx proxy in production"
echo ""
echo "🛑 To stop services:"
echo "   bash stop_all.sh"
echo ""
