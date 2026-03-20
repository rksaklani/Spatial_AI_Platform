#!/bin/bash
# Docker startup script for Ultimate Spatial AI Platform

set -e

echo "=========================================="
echo "Ultimate Spatial AI Platform - Docker Setup"
echo "=========================================="
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "Error: Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Function to start development environment
start_dev() {
    echo "Starting development environment..."
    echo ""
    
    # Check for GPU support
    if command -v nvidia-smi &> /dev/null; then
        echo "NVIDIA GPU detected. Starting with GPU workers..."
        docker-compose --profile gpu up -d
    else
        echo "No NVIDIA GPU detected. Starting without GPU workers..."
        docker-compose up -d
    fi
    
    echo ""
    echo "Services starting... This may take a few minutes on first run."
    echo ""
    echo "Waiting for services to be healthy..."
    sleep 10
    
    echo ""
    echo "=========================================="
    echo "Services are starting!"
    echo "=========================================="
    echo ""
    echo "API Server: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
    echo "MinIO Console: http://localhost:9001"
    echo "  Username: minioadmin"
    echo "  Password: minioadmin123"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
    echo ""
}

# Function to start production environment
start_prod() {
    echo "Starting production environment..."
    echo ""
    
    # Check if .env file exists
    if [ ! -f .env ]; then
        echo "Error: .env file not found!"
        echo "Please copy .env.example to .env and configure it:"
        echo "  cp .env.example .env"
        echo "  nano .env"
        exit 1
    fi
    
    echo "Starting production services..."
    docker-compose -f docker-compose.prod.yml up -d
    
    echo ""
    echo "Services starting... This may take a few minutes."
    echo ""
    echo "To view logs: docker-compose -f docker-compose.prod.yml logs -f"
    echo "To stop: docker-compose -f docker-compose.prod.yml down"
    echo ""
}

# Function to stop services
stop_services() {
    echo "Stopping services..."
    docker-compose down
    docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
    echo "Services stopped."
}

# Function to show status
show_status() {
    echo "Service Status:"
    echo ""
    docker-compose ps
    echo ""
    echo "Resource Usage:"
    docker stats --no-stream
}

# Main menu
case "${1:-}" in
    dev)
        start_dev
        ;;
    prod)
        start_prod
        ;;
    stop)
        stop_services
        ;;
    status)
        show_status
        ;;
    *)
        echo "Usage: $0 {dev|prod|stop|status}"
        echo ""
        echo "Commands:"
        echo "  dev     - Start development environment"
        echo "  prod    - Start production environment"
        echo "  stop    - Stop all services"
        echo "  status  - Show service status"
        echo ""
        exit 1
        ;;
esac
