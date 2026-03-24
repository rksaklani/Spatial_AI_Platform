# 🚀 START HERE - 3D Pipeline Installation

## What You Have Now

✅ **Working Components:**
- Backend API (FastAPI)
- Frontend UI (React + Vite)
- Database (MongoDB Atlas)
- Storage (MinIO)
- Authentication & Authorization
- All 5 dashboard pages with API integration
- Video upload functionality
- Frame extraction (FFmpeg)

⚠️ **Missing for Full 3D Reconstruction:**
- CUDA Toolkit
- CMake
- COLMAP
- PyTorch with CUDA (you have CPU version)
- Gaussian Splatting

## Quick Installation (Choose One)

### Option 1: Automated Installation Script (Recommended)

Run the installation wizard that guides you through each step:

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
.\scripts\install_3d_pipeline.ps1
```

The script will:
1. Check what's already installed
2. Guide you through installing missing components
3. Install PyTorch with CUDA
4. Clone and build Gaussian Splatting
5. Verify everything works

**Estimated time:** 2-3 hours

### Option 2: Manual Installation

Follow the step-by-step guide:

📖 **Read:** `docs/QUICK_INSTALL_STEPS.md`

This gives you detailed instructions for each component.

### Option 3: Check Status First

See exactly what's missing on your system:

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
python scripts/check_3d_requirements.py
```

## Installation Order

If installing manually, follow this order:

1. **Visual Studio 2022** (if not installed) - 30-60 min
2. **CUDA Toolkit** - 15-20 min
3. **CMake** - 5 min
4. **COLMAP** - 10 min
5. **PyTorch with CUDA** - 10 min
6. **Gaussian Splatting** - 30-45 min

**Total:** 1.5-3 hours depending on your system

## What Each Component Does

| Component | Purpose | Required For |
|-----------|---------|--------------|
| **CUDA Toolkit** | GPU acceleration | Gaussian Splatting training |
| **CMake** | Build system | COLMAP (if building from source) |
| **COLMAP** | Camera pose estimation | 3D reconstruction from video |
| **PyTorch (CUDA)** | Deep learning framework | Depth estimation, Gaussian Splatting |
| **Gaussian Splatting** | Neural 3D reconstruction | High-quality 3D scene generation |

## After Installation

### 1. Verify Everything Works

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
python scripts/check_3d_requirements.py
```

All checks should show ✓

### 2. Start the Services

**Terminal 1: Backend**
```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
uvicorn main:app --reload
```

**Terminal 2: Celery Worker**
```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
celery -A workers.celery_app worker --loglevel=info --pool=solo
```

**Terminal 3: Frontend**
```powershell
cd E:\Rk_Saklani\3d_rendering\frontend
npm run dev
```

### 3. Test with a Video

1. Open http://localhost:5173
2. Login
3. Go to "3D Scenes"
4. Upload a SHORT video (30 seconds recommended for first test)
5. Watch the processing in Celery logs

### 4. Monitor Processing

The pipeline will:
1. Extract frames (10s)
2. Filter frames (20s)
3. Estimate camera poses with COLMAP (2-3 min)
4. Generate depth maps (30s-1 min)
5. Train Gaussian Splatting (10-20 min for 30s video)
6. Optimize and generate LODs (1 min)

**Total for 30s video:** 15-25 minutes

## Current System Status

Based on your last check:

```
✓ NVIDIA GPU detected
✓ PyTorch 2.10.0 (CPU version - needs upgrade)
✓ OpenCV, NumPy, SciPy
✓ PLYFile
✓ FFmpeg

✗ CUDA Toolkit (nvcc not in PATH)
✗ CMake
✗ COLMAP
✗ Gaussian Splatting repository
```

## Troubleshooting

### "Command not found" after installation

Restart PowerShell after installing any component that modifies PATH.

### CUDA not detected

```powershell
# Add CUDA to PATH manually
$env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"
```

### Build errors for Gaussian Splatting

1. Ensure Visual Studio 2022 with C++ tools is installed
2. Ensure CUDA is in PATH
3. Try verbose build: `pip install -e . -v`

### Out of memory during training

1. Use shorter videos (30 seconds)
2. Close other GPU applications
3. Monitor: `nvidia-smi -l 1`

## Documentation

- 📖 **Full installation guide:** `docs/3D_PIPELINE_INSTALLATION_WINDOWS.md`
- 📋 **Quick steps:** `docs/QUICK_INSTALL_STEPS.md`
- 📊 **Current status:** `docs/INSTALLATION_STATUS.md`
- 🔧 **Check script:** `backend/scripts/check_3d_requirements.py`
- 🤖 **Install script:** `backend/scripts/install_3d_pipeline.ps1`

## Need Help?

1. Run the check script to see what's missing
2. Check the troubleshooting section in the installation guide
3. Look at logs in `backend/logs/`
4. Monitor GPU: `nvidia-smi`

## What's Next?

Once everything is installed:

1. ✅ Test with 30-second video
2. ✅ Verify 3D reconstruction works
3. ✅ View result in 3D viewer
4. ✅ Try longer videos
5. ✅ Optimize settings for your GPU

---

**Ready to start?** Run the installation script:

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
.\scripts\install_3d_pipeline.ps1
```

Or check what's missing first:

```powershell
python scripts/check_3d_requirements.py
```
