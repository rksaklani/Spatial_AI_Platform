@echo off
REM Start Development Environment for Windows
REM This script starts both frontend and backend services

echo.
echo 🚀 Starting Spatial AI Platform Development Environment...
echo.

REM Start Backend
echo 📦 Starting Backend...
cd backend
start "Backend Server" cmd /k "python main.py"
cd ..
timeout /t 3 /nobreak >nul
echo ✅ Backend started
echo.

REM Start Frontend
echo 🎨 Starting Frontend...
cd frontend
start "Frontend Dev Server" cmd /k "npm run dev"
cd ..
timeout /t 2 /nobreak >nul
echo ✅ Frontend started
echo.

echo ✨ Development environment is ready!
echo.
echo 📍 Frontend: http://localhost:5173
echo 📍 Backend:  http://localhost:8000
echo 📍 API Docs: http://localhost:8000/docs
echo 📍 Health:   http://localhost:8000/health
echo.
echo Press any key to exit...
pause >nul
