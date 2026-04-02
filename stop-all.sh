#!/bin/bash
# Stop all Spatial AI Platform services

echo "=========================================="
echo "  Stopping Spatial AI Platform Services"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Function to stop process by PID file
stop_by_pidfile() {
    local pidfile=$1
    local name=$2
    
    if [ -f "$pidfile" ]; then
        local pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid"
            echo -e "${GREEN}✓${NC} Stopped $name (PID: $pid)"
        else
            echo -e "${YELLOW}⚠${NC} $name not running"
        fi
        rm -f "$pidfile"
    else
        echo -e "${YELLOW}⚠${NC} $name PID file not found"
    fi
}

# Stop Frontend
echo "Stopping Frontend..."
stop_by_pidfile "logs/frontend.pid" "Frontend"

# Stop Celery Workers
echo "Stopping Celery Workers..."
stop_by_pidfile "logs/celery_gpu.pid" "GPU Worker"
stop_by_pidfile "logs/celery_cpu.pid" "CPU Worker"

# Also kill any remaining celery processes
pkill -f "celery.*worker" 2>/dev/null && echo -e "${GREEN}✓${NC} Killed remaining Celery processes"

# Stop Backend
echo "Stopping Backend..."
stop_by_pidfile "logs/backend.pid" "Backend"

# Stop MinIO
echo "Stopping MinIO..."
stop_by_pidfile "logs/minio.pid" "MinIO"

# Stop Redis (optional - comment out if you want to keep it running)
# echo "Stopping Redis..."
# sudo systemctl stop redis-server
# echo -e "${GREEN}✓${NC} Redis stopped"

echo ""
echo "=========================================="
echo "  All Services Stopped"
echo "=========================================="
echo ""
echo "Note: Redis is still running (system service)"
echo "To stop Redis: sudo systemctl stop redis-server"
echo ""
