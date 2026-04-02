# Quick Start Guide - Spatial AI Platform

## One-Command Startup

```bash
./start-all.sh
```

This single command starts everything:
- ✅ Redis server
- ✅ MinIO object storage
- ✅ Backend API (FastAPI + Uvicorn)
- ✅ Celery workers (CPU + GPU)
- ✅ Frontend (React + Vite)

## Access the Platform

**Frontend:** http://localhost:5173  
**Backend API:** http://localhost:8000  
**API Docs:** http://localhost:8000/docs  
**MinIO Console:** http://localhost:9001  

**Default Credentials:**
- Email: `rksaklani9090@gmail.com`
- Password: `rksaklani90@test`

## Stop All Services

```bash
./stop-all.sh
```

## What's Running

### Backend Services
- **FastAPI Backend** - Port 8000
  - REST API for all operations
  - MongoDB Atlas connection
  - JWT authentication
  - File upload handling

- **MinIO** - Port 9000
  - S3-compatible object storage
  - Stores videos, 3D models, tiles
  - Console on port 9001
  - Credentials: minioadmin/minioadmin

- **Redis** - Port 6379
  - Celery message broker
  - Task queue management
  - System service (always running)

- **Celery Workers**
  - CPU Worker: 32 concurrent tasks
  - GPU Worker: 1 task (3D reconstruction)

### Frontend
- **React + Vite** - Port 5173
  - Modern UI with glassmorphism design
  - Real-time 3D viewer
  - File upload with progress
  - Scene management

## Video-to-3D Pipeline

When you upload a video, it goes through:

1. **Frame Extraction** (FFmpeg)
   - Extracts frames at optimal rate
   - Filters blurry/duplicate frames
   - Time: 2-5 minutes

2. **Camera Pose Estimation** (COLMAP)
   - Feature detection and matching
   - Structure from Motion (SfM)
   - Camera calibration
   - Time: 5-15 minutes

3. **Depth Estimation** (MiDaS + PyTorch)
   - Neural depth prediction
   - Per-frame depth maps
   - GPU accelerated
   - Time: 3-10 minutes

4. **3D Reconstruction** (Gaussian Splatting)
   - Point cloud generation
   - Gaussian fitting and optimization
   - GPU accelerated (CUDA 12.1)
   - Time: 10-30 minutes

5. **Post-Processing**
   - Tiling for streaming
   - LOD generation
   - Metadata creation
   - Time: 2-5 minutes

**Total Time:** 20-60 minutes depending on video length and resolution

## System Requirements

### Installed Components
- ✅ Python 3.10.12 with venv
- ✅ Node.js 20.x
- ✅ CUDA 12.1 Toolkit
- ✅ PyTorch 2.5.1+cu121
- ✅ COLMAP 3.7
- ✅ Gaussian Splatting (CUDA extensions)
- ✅ FFmpeg 4.4.2
- ✅ MinIO (latest)
- ✅ Redis 6.0

### Hardware
- **GPU:** NVIDIA GeForce RTX 4090
- **VRAM:** 24 GB
- **CUDA Cores:** 16,384
- **Driver:** 590.48.01

## Troubleshooting

### Services Won't Start

```bash
# Check what's using the ports
lsof -i:8000  # Backend
lsof -i:5173  # Frontend
lsof -i:9000  # MinIO

# Kill processes if needed
kill <PID>

# Try starting again
./start-all.sh
```

### Check Service Status

```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl http://localhost:5173

# Redis
redis-cli ping

# MinIO
curl http://localhost:9000/minio/health/live

# Celery workers
cd backend && venv_test/bin/celery -A workers.celery_app inspect active
```

### View Logs

```bash
# All logs in one view
tail -f logs/*.log

# Individual services
tail -f logs/backend.log
tail -f logs/frontend.log
tail -f logs/celery_cpu.log
tail -f logs/celery_gpu.log
tail -f logs/minio.log
```

### GPU Not Working

```bash
# Check GPU
nvidia-smi

# Check CUDA
nvcc --version

# Check PyTorch CUDA
cd backend && venv_test/bin/python -c "import torch; print('CUDA:', torch.cuda.is_available())"

# Test pipeline
cd backend && venv_test/bin/python test_pipeline.py
```

### Video Processing Stuck

```bash
# Check worker logs
tail -f logs/celery_cpu.log
tail -f logs/celery_gpu.log

# Check GPU usage
watch -n 1 nvidia-smi

# Restart workers
pkill -f "celery.*worker"
cd backend
venv_test/bin/celery -A workers.celery_app worker -Q cpu -n cpu_worker@%h --loglevel=info &
venv_test/bin/celery -A workers.celery_app worker -Q gpu -n gpu_worker@%h --loglevel=info --concurrency=1 &
```

## Manual Startup (If Script Fails)

### 1. Start Redis
```bash
sudo systemctl start redis-server
```

### 2. Start MinIO
```bash
cd backend
MINIO_ROOT_USER=minioadmin MINIO_ROOT_PASSWORD=minioadmin \
    minio server minio-data --console-address :9001 &
cd ..
```

### 3. Start Backend
```bash
cd backend
venv_test/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload &
cd ..
```

### 4. Start Workers
```bash
cd backend
venv_test/bin/celery -A workers.celery_app worker -Q cpu -n cpu_worker@%h --loglevel=info &
venv_test/bin/celery -A workers.celery_app worker -Q gpu -n gpu_worker@%h --loglevel=info --concurrency=1 &
cd ..
```

### 5. Start Frontend
```bash
cd frontend
npm run dev -- --host 0.0.0.0 &
cd ..
```

## Features

### Video Upload
- Drag-and-drop or file picker
- Supports: MP4, MOV, AVI, WebM, MKV
- Max size: 5GB
- Real-time upload progress

### 3D File Import
- Formats: PLY, OBJ, GLTF, GLB, STL, FBX, IFC
- Instant viewing
- No processing required

### 3D Viewer
- Interactive navigation
- Real-time rendering
- Camera controls
- FPS tracking

### Collaboration
- Multi-user organizations
- Annotations and measurements
- PDF report generation
- Public sharing links

## Performance Tips

### For Faster Processing
1. Use shorter videos (30-60 seconds) for testing
2. 1080p resolution is optimal (4K takes longer)
3. Good lighting and stable camera movement
4. Monitor GPU usage: `watch -n 1 nvidia-smi`

### Expected Processing Times (1080p)
- 30 seconds: 10-15 minutes
- 1 minute: 15-20 minutes
- 2 minutes: 20-30 minutes
- 5 minutes: 30-60 minutes

## Development

### Backend Development
```bash
cd backend
venv_test/bin/python main.py
```

### Frontend Development
```bash
cd frontend
npm run dev
```

### Run Tests
```bash
# Frontend tests
cd frontend
npm test

# Backend tests
cd backend
venv_test/bin/pytest

# Pipeline test
cd backend
venv_test/bin/python test_pipeline.py
```

## Environment Variables

Backend configuration in `backend/.env`:
- MongoDB connection
- MinIO credentials
- JWT secrets
- CORS origins
- Celery broker URL

Frontend configuration in `frontend/.env`:
- API base URL
- Feature flags

## Support

For issues or questions:
1. Check logs in `logs/` directory
2. Verify all services are running
3. Test individual components
4. Check GPU status with `nvidia-smi`

---

**Ready to create 3D magic! 🚀**
