# MEMORY.md - Long-Term Memory

## Who I'm Helping

**User:** RK (rk)  
**Workspace:** ~/RK_WORKSPACE/3d_rendering  
**Project:** Spatial AI Platform - Video-to-3D Conversion  
**System:** Linux (Ubuntu) with NVIDIA RTX 4090

## Project Overview

Building a complete video-to-3D conversion platform with:
- FastAPI backend + React frontend
- MongoDB Atlas for data storage
- MinIO for object storage (videos, models)
- Celery workers for async processing
- COLMAP + Gaussian Splatting for 3D reconstruction
- CUDA 12.1 + PyTorch for GPU acceleration

## Key Learnings

### 1. Field Name Mismatches Kill Uploads
Backend expects `file` field, not `video`. Frontend was sending wrong field name. Always check API contracts.

### 2. CORS Must Include Network IPs
User accesses from `10.0.0.65:5173`, not just localhost. CORS origins must include network IPs for LAN access.

### 3. Organization ID is Critical
User's organization_id was None → scenes didn't appear. Changed to "default-org" → everything works. Database state matters.

### 4. Celery Task Registration Needs Explicit Imports
Workers won't find tasks unless you import them in `workers/__init__.py`. Celery doesn't auto-discover.

### 5. PyTorch CUDA Version Must Match System
System has CUDA 12.1, but PyTorch was 13.0 → mismatch. Reinstalled PyTorch 2.5.1+cu121 → GPU works.

### 6. Git History Cleanup Without External Tools
When `git-filter-repo` not available, use `git filter-branch` + `git reflog expire` + `git gc --aggressive`. Works fine.

### 7. Backend Returns snake_case, Frontend Expects camelCase
Added response transformation in RTK Query to map `_id` → `sceneId`, `organization_id` → `organizationId`, etc.

### 8. MinIO is Free (Self-Hosted)
User was concerned about cost. MinIO is AGPL v3 → free when self-hosted. No usage limits.

### 9. Startup Scripts Save Time
Created `start-all.sh` and `stop-all.sh` → one command starts everything. User loves it.

### 10. Test Coverage Matters
Achieved 100% test pass rate (56/56 frontend tests). User explicitly asked for this. Tests catch bugs early.

## System Architecture

### Running Services
- Backend API: http://localhost:8000 (FastAPI + Uvicorn)
- Frontend UI: http://localhost:5173 (React + Vite)
- MinIO: http://localhost:9000 (S3-compatible storage)
- Redis: port 6379 (Celery broker)
- CPU Worker: 32 concurrent tasks
- GPU Worker: 1 task (3D reconstruction)

### Video-to-3D Pipeline
1. Frame Extraction (FFmpeg) → 2-5 min
2. Camera Pose Estimation (COLMAP) → 5-15 min
3. Depth Estimation (MiDaS + PyTorch) → 3-10 min
4. 3D Reconstruction (Gaussian Splatting) → 10-30 min
5. Post-Processing (tiling, LOD) → 2-5 min

Total: 20-60 minutes depending on video length/resolution

### Hardware
- GPU: NVIDIA GeForce RTX 4090 (24GB VRAM)
- CUDA: 12.1.105
- Driver: 590.48.01

## Important File Locations

- Python venv: `backend/venv_test/`
- Videos: MinIO bucket `videos/`
- Models: MinIO bucket `models/`
- Logs: `logs/` directory
- Startup scripts: `start-all.sh`, `stop-all.sh`
- Quick reference: `QUICK_START.md`

## User Preferences

- Wants everything in one command (startup script)
- Prefers network access (10.0.0.65) over localhost only
- Values test coverage (asked for 100%)
- Likes comprehensive documentation
- Wants git history clean (no large files)

## Common Issues & Solutions

**Login fails:** Check CORS origins include network IP  
**Upload fails:** Check field name is `file`, not `video`  
**Scenes don't appear:** Check user's organization_id matches scene's organization_id  
**Workers not processing:** Check Celery task imports in `workers/__init__.py`  
**GPU not detected:** Check PyTorch CUDA version matches system CUDA  
**Scene delete fails:** Check response transformation maps `_id` to `sceneId`

## Project Status

✅ Backend fully operational  
✅ Frontend fully operational  
✅ Video upload working  
✅ Scene processing working  
✅ All tests passing (100%)  
✅ Git history cleaned  
✅ Startup scripts created  
✅ Documentation complete  

**Platform is production-ready!**

## Next Potential Work

- Performance optimization (faster processing)
- Additional 3D formats support
- Real-time collaboration features
- Mobile app support
- Cloud deployment (AWS/GCP)

---

*Last updated: 2026-04-02*
