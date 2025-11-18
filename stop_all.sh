#!/bin/bash

echo "Stopping OCR & Translation System..."
echo ""

# 读取进程 ID
if [ -f "logs/backend.pid" ]; then
    BACKEND_PID=$(cat logs/backend.pid)
    if ps -p $BACKEND_PID > /dev/null 2>&1; then
        echo "Stopping backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        echo "✓ Backend stopped"
    else
        echo "Backend process not found"
    fi
    rm logs/backend.pid
else
    echo "Stopping backend by name..."
    pkill -f "uvicorn app.main:app"
fi

if [ -f "logs/frontend.pid" ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if ps -p $FRONTEND_PID > /dev/null 2>&1; then
        echo "Stopping frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        echo "✓ Frontend stopped"
    else
        echo "Frontend process not found"
    fi
    rm logs/frontend.pid
else
    echo "Stopping frontend by name..."
    pkill -f "vite"
fi

echo ""
echo "System stopped"
