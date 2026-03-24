#!/bin/bash

# Start Development Environment
# This script starts both frontend and backend services

echo "🚀 Starting Spatial AI Platform Development Environment..."
echo ""

# Check if backend is already running
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Backend is already running on port 8000"
else
    echo "📦 Starting Backend..."
    cd backend
    python main.py &
    BACKEND_PID=$!
    cd ..
    echo "✅ Backend started (PID: $BACKEND_PID)"
fi

# Wait a moment for backend to start
sleep 2

# Check if frontend is already running
if lsof -Pi :5173 -sTCP:LISTEN -t >/dev/null ; then
    echo "✅ Frontend is already running on port 5173"
else
    echo "🎨 Starting Frontend..."
    cd frontend
    npm run dev &
    FRONTEND_PID=$!
    cd ..
    echo "✅ Frontend started (PID: $FRONTEND_PID)"
fi

echo ""
echo "✨ Development environment is ready!"
echo ""
echo "📍 Frontend: http://localhost:5173"
echo "📍 Backend:  http://localhost:8000"
echo "📍 API Docs: http://localhost:8000/docs"
echo "📍 Health:   http://localhost:8000/health"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Wait for user interrupt
wait
