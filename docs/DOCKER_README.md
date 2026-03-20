# Docker Infrastructure Setup

This document describes the Docker infrastructure for the Ultimate Spatial AI Platform.

## Overview

The platform uses Docker containers for all services:
- **API Server**: FastAPI application serving REST API
- **GPU Workers**: Celery workers for GPU-intensive tasks (depth estimation, neural reconstruction)
- **CPU Workers**: Celery workers for CPU tasks (frame extraction, file processing)
- **MongoDB**: Document database for metadata and user data
- **Redis/Valkey**: Cache and message broker for Celery
- **MinIO**: S3-compatible object storage for videos, frames, and scenes

## Prerequisites

### For Development
- Docker Engine 20.10+
- Docker Compose 2.0+
- 16GB RAM minimum
- 50GB free disk space

### For GPU Workers (Optional)
- NVIDIA GPU with CUDA support
- NVIDIA Docker runtime installed
- CUDA 12.1+ compatible GPU

## Quick Start - Development

1. **Start all services (without GPU)**:
```bash
docker-compose up -d
```

2. **Start all services (with GPU)**:
```bash
docker-compose --profile gpu up -d
```

3. **Start with frontend**:
```bash
docker-compose --profile frontend up -d
```

4. **View logs**:
```bash
docker-compose logs -f api
docker-compose logs -f celery-worker
docker-compose logs -f celery-gpu-worker
```

5. **Stop all services**:
```bash
docker-compose down
```

6. **Stop and remove volumes**:
```bash
docker-compose down -v
```

## Quick Start - Production

1. **Copy environment file**:
```bash
cp .env.example .env
```

2. **Edit .env file** and set secure passwords and secrets

3. **Start production services**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

4. **View logs**:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

## Service URLs

### Development
- API Server: http://localhost:8000
- API Docs: http://localhost:8000/docs
- MinIO Console: http://localhost:9001
- MongoDB: mongodb://localhost:27017
- Redis: redis://localhost:6379

### Production
Same URLs, but use environment variables for credentials.

## Docker Images

### API Server (backend/Dockerfile)
Multi-stage build with development and production targets:
- **Base**: Python 3.11 with system dependencies
- **Dependencies**: Python packages installed
- **Development**: Hot reload enabled, runs as root
- **Production**: Optimized, runs as non-root user, 4 workers

### GPU Worker (backend/Dockerfile.gpu)
Multi-stage build with CUDA support:
- **Base**: NVIDIA CUDA 12.1 with cuDNN 8
- **Dependencies**: PyTorch with CUDA support
- **Development**: Hot reload enabled
- **Production**: Optimized, runs as non-root user

## Building Images

### Build API server for development:
```bash
docker build -t spatial-ai-api:dev --target development -f backend/Dockerfile backend/
```

### Build API server for production:
```bash
docker build -t spatial-ai-api:prod --target production -f backend/Dockerfile backend/
```

### Build GPU worker for development:
```bash
docker build -t spatial-ai-gpu-worker:dev --target development -f backend/Dockerfile.gpu backend/
```

### Build GPU worker for production:
```bash
docker build -t spatial-ai-gpu-worker:prod --target production -f backend/Dockerfile.gpu backend/
```

## Volume Management

### Development volumes:
- `mongodb_data`: MongoDB database files
- `mongodb_config`: MongoDB configuration
- `redis_data`: Redis persistence
- `minio_data`: MinIO object storage

### Backup volumes:
```bash
# Backup MongoDB
docker exec spatial-ai-mongodb mongodump --out /backup
docker cp spatial-ai-mongodb:/backup ./mongodb-backup

# Backup MinIO
docker exec spatial-ai-minio mc mirror /data ./minio-backup
```

### Restore volumes:
```bash
# Restore MongoDB
docker cp ./mongodb-backup spatial-ai-mongodb:/backup
docker exec spatial-ai-mongodb mongorestore /backup

# Restore MinIO
docker cp ./minio-backup spatial-ai-minio:/restore
docker exec spatial-ai-minio mc mirror /restore /data
```

## Networking

All services communicate via the `spatial-ai-network` bridge network.

Service hostnames within the network:
- `mongodb` - MongoDB database
- `redis` - Redis/Valkey cache
- `minio` - MinIO object storage
- `api` - FastAPI server
- `celery-worker` - CPU worker
- `celery-gpu-worker` - GPU worker

## Health Checks

All services include health checks:
- **API**: `curl http://localhost:8000/health`
- **MongoDB**: `mongosh --eval "db.adminCommand('ping')"`
- **Redis**: `valkey-cli ping`
- **MinIO**: `curl http://localhost:9000/minio/health/live`
- **Celery**: `celery -A workers.celery_app inspect ping`

## Troubleshooting

### GPU not detected:
```bash
# Check NVIDIA runtime
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# If fails, install nvidia-docker2:
# Ubuntu/Debian:
sudo apt-get install nvidia-docker2
sudo systemctl restart docker
```

### Port conflicts:
If ports are already in use, edit docker-compose.yml to change port mappings:
```yaml
ports:
  - "8001:8000"  # Change host port from 8000 to 8001
```

### Out of memory:
Increase Docker memory limit in Docker Desktop settings or add to docker-compose.yml:
```yaml
deploy:
  resources:
    limits:
      memory: 8G
```

### Permission errors:
Ensure volumes have correct permissions:
```bash
sudo chown -R 1000:1000 ./backend
```

## Security Notes

### Development:
- Default credentials are used (NOT secure)
- Services exposed on all interfaces
- Hot reload enabled

### Production:
- Use strong passwords in .env file
- Run services as non-root users
- Enable TLS/SSL for external access
- Use secrets management (Docker Secrets, Vault)
- Restrict network access with firewall rules
- Regular security updates

## Performance Tuning

### API Server:
- Adjust worker count: `--workers 4`
- Enable worker timeout: `--timeout 120`
- Use Gunicorn for production: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`

### Celery Workers:
- Adjust concurrency: `--concurrency=4`
- Set max tasks per child: `--max-tasks-per-child=100`
- Use separate queues: `--queues=cpu,gpu`

### MongoDB:
- Enable WiredTiger cache: `--wiredTigerCacheSizeGB=2`
- Add indexes for frequently queried fields
- Enable replication for high availability

### Redis:
- Adjust maxmemory: `--maxmemory 2gb`
- Set eviction policy: `--maxmemory-policy allkeys-lru`

## Monitoring

### View resource usage:
```bash
docker stats
```

### View container logs:
```bash
docker-compose logs -f --tail=100 api
```

### Access container shell:
```bash
docker exec -it spatial-ai-api bash
```

### Inspect container:
```bash
docker inspect spatial-ai-api
```

## Scaling

### Scale CPU workers:
```bash
docker-compose up -d --scale celery-worker=4
```

### Scale GPU workers:
```bash
docker-compose --profile gpu up -d --scale celery-gpu-worker=2
```

## CI/CD Integration

### Build and push images:
```bash
# Build
docker build -t myregistry/spatial-ai-api:latest --target production -f backend/Dockerfile backend/

# Push
docker push myregistry/spatial-ai-api:latest

# Deploy
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## References

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [NVIDIA Container Toolkit](https://github.com/NVIDIA/nvidia-docker)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Celery Documentation](https://docs.celeryproject.org/)
