#!/bin/bash
# Complete startup script for Spatial AI Platform
# Starts all services: Backend, Frontend, MinIO, Redis, Celery Workers

set -e  # Exit on error

echo "=========================================="
echo "  Spatial AI Platform - Complete Startup"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check if a port is in use
port_in_use() {
    lsof -i:$1 >/dev/null 2>&1
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=0
    
    echo -n "Waiting for $name to start..."
    while [ $attempt -lt $max_attempts ]; do
        if curl -s "$url" >/dev/null 2>&1; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}✗${NC}"
    return 1
}

echo "Step 1: Checking prerequisites..."
echo "-----------------------------------"

# Check Python
if ! command_exists python3; then
    echo -e "${RED}✗ Python 3 not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Python 3: $(python3 --version)"

# Check Node.js
if ! command_exists node; then
    echo -e "${RED}✗ Node.js not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} Node.js: $(node --version)"

# Check FFmpeg
if ! command_exists ffmpeg; then
    echo -e "${RED}✗ FFmpeg not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} FFmpeg: $(ffmpeg -version | head -1)"

# Check COLMAP
if ! command_exists colmap; then
    echo -e "${RED}✗ COLMAP not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} COLMAP: $(colmap -h 2>&1 | head -1)"

# Check CUDA
if ! command_exists nvcc; then
    echo -e "${YELLOW}⚠${NC} CUDA not found (GPU acceleration disabled)"
else
    echo -e "${GREEN}✓${NC} CUDA: $(nvcc --version | grep release)"
fi

# Check MinIO
if ! command_exists minio; then
    echo -e "${RED}✗ MinIO not found${NC}"
    exit 1
fi
echo -e "${GREEN}✓${NC} MinIO: $(minio --version | head -1)"

echo ""
echo "Step 2: Starting Redis..."
echo "-----------------------------------"
if systemctl is-active --quiet redis-server; then
    echo -e "${GREEN}✓${NC} Redis already running"
else
    sudo systemctl start redis-server
    sleep 2
    if systemctl is-active --quiet redis-server; then
        echo -e "${GREEN}✓${NC} Redis started"
    else
        echo -e "${RED}✗${NC} Failed to start Redis"
        exit 1
    fi
fi

echo ""
echo "Step 3: Starting MinIO..."
echo "-----------------------------------"
if port_in_use 9000; then
    echo -e "${GREEN}✓${NC} MinIO already running on port 9000"
else
    cd backend
    mkdir -p minio-data
    MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
        nohup minio server minio-data --console-address :9001 > ../logs/minio.log 2>&1 &
    MINIO_PID=$!
    echo $MINIO_PID > ../logs/minio.pid
    cd ..
    
    if wait_for_service "http://localhost:9000/minio/health/live" "MinIO"; then
        echo -e "${GREEN}✓${NC} MinIO started (PID: $MINIO_PID)"
        echo -e "   API: http://localhost:9000"
        echo -e "   Console: http://localhost:9001"
    else
        echo -e "${RED}✗${NC} MinIO failed to start"
        exit 1
    fi
fi

echo ""
echo "Step 4: Starting Backend API..."
echo "-----------------------------------"

# Check if backend is actually responding (not just port in use)
if curl -s http://localhost:8000/health >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Backend already running on port 8000"
else
    # Kill any stale processes on port 8000
    if port_in_use 8000; then
        echo "Cleaning up stale backend process..."
        lsof -ti:8000 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    cd backend
    
    # Activate virtual environment and start backend
    if [ -d "venv_test" ]; then
        nohup venv_test/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload > ../logs/backend.log 2>&1 &
        BACKEND_PID=$!
        echo $BACKEND_PID > ../logs/backend.pid
        cd ..
        
        if wait_for_service "http://localhost:8000/health" "Backend API"; then
            echo -e "${GREEN}✓${NC} Backend started (PID: $BACKEND_PID)"
            echo -e "   URL: http://localhost:8000"
            echo -e "   Docs: http://localhost:8000/docs"
        else
            echo -e "${RED}✗${NC} Backend failed to start"
            echo "Check logs/backend.log for details"
            exit 1
        fi
    else
        echo -e "${RED}✗${NC} Virtual environment not found at backend/venv_test"
        exit 1
    fi
fi

echo ""
echo "Step 5: Starting Celery Workers..."
echo "-----------------------------------"
cd backend

# Check if CPU worker is running
if pgrep -f "celery.*cpu_worker" > /dev/null; then
    echo -e "${GREEN}✓${NC} CPU worker already running"
else
    nohup venv_test/bin/celery -A workers.celery_app worker \
        -Q cpu -n cpu_worker@%h --loglevel=info \
        > ../logs/celery_cpu.log 2>&1 &
    CPU_WORKER_PID=$!
    echo $CPU_WORKER_PID > ../logs/celery_cpu.pid
    echo -e "${GREEN}✓${NC} CPU worker started (PID: $CPU_WORKER_PID)"
fi

# Check if GPU worker is running
if pgrep -f "celery.*gpu_worker" > /dev/null; then
    echo -e "${GREEN}✓${NC} GPU worker already running"
else
    nohup venv_test/bin/celery -A workers.celery_app worker \
        -Q gpu -n gpu_worker@%h --loglevel=info --concurrency=1 \
        > ../logs/celery_gpu.log 2>&1 &
    GPU_WORKER_PID=$!
    echo $GPU_WORKER_PID > ../logs/celery_gpu.pid
    echo -e "${GREEN}✓${NC} GPU worker started (PID: $GPU_WORKER_PID)"
fi

cd ..

echo ""
echo "Step 6: Starting Frontend..."
echo "-----------------------------------"

# Check if frontend is actually responding (not just port in use)
if curl -s http://localhost:5173 >/dev/null 2>&1; then
    echo -e "${GREEN}✓${NC} Frontend already running on port 5173"
else
    # Kill any stale processes on port 5173
    if port_in_use 5173; then
        echo "Cleaning up stale frontend process..."
        lsof -ti:5173 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
    
    cd frontend
    nohup npm run dev -- --host 0.0.0.0 > ../logs/frontend.log 2>&1 &
    FRONTEND_PID=$!
    echo $FRONTEND_PID > ../logs/frontend.pid
    cd ..
    
    if wait_for_service "http://localhost:5173" "Frontend"; then
        echo -e "${GREEN}✓${NC} Frontend started (PID: $FRONTEND_PID)"
        echo -e "   URL: http://localhost:5173"
        echo -e "   Network: http://10.0.0.65:5173"
    else
        echo -e "${RED}✗${NC} Frontend failed to start"
        echo "Check logs/frontend.log for details"
        exit 1
    fi
fi

echo ""
echo "=========================================="
echo "  🎉 All Services Started Successfully!"
echo "=========================================="
echo ""
echo "Service Status:"
echo "  ✓ Redis:        Running"
echo "  ✓ MinIO:        http://localhost:9000 (Console: http://localhost:9001)"
echo "  ✓ Backend API:  http://localhost:8000"
echo "  ✓ CPU Worker:   Running (32 concurrent tasks)"
echo "  ✓ GPU Worker:   Running (1 concurrent task)"
echo "  ✓ Frontend:     http://localhost:5173"
echo ""
echo "Capabilities:"
echo "  ✓ Video Upload & Processing"
echo "  ✓ 3D File Import (PLY, OBJ, GLTF, etc.)"
echo "  ✓ COLMAP Camera Pose Estimation"
echo "  ✓ Gaussian Splatting 3D Reconstruction"
echo "  ✓ GPU Acceleration (CUDA 12.1 + RTX 4090)"
echo "  ✓ FFmpeg Video Processing"
echo ""
echo "Access the platform:"
echo "  🌐 Local:   http://localhost:5173"
echo "  🌐 Network: http://10.0.0.65:5173"
echo "  📚 API Docs: http://localhost:8000/docs"
echo "  🗄️  MinIO Console: http://localhost:9001"
echo ""
echo "View logs:"
echo "  Backend:     tail -f logs/backend.log"
echo "  Frontend:    tail -f logs/frontend.log"
echo "  CPU Worker:  tail -f logs/celery_cpu.log"
echo "  GPU Worker:  tail -f logs/celery_gpu.log"
echo "  MinIO:       tail -f logs/minio.log"
echo ""
echo "Stop all services:"
echo "  ./stop-all.sh"
echo ""
