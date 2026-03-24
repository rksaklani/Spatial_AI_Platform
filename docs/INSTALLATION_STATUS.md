# 3D Pipeline Installation Status

Last updated: 2026-03-24

## Current Installation Status

### ✅ Already Installed

| Component | Status | Version/Info |
|-----------|--------|--------------|
| NVIDIA GPU | ✓ Installed | Detected via nvidia-smi |
| PyTorch | ✓ Installed | 2.10.0+cpu (needs CUDA version) |
| OpenCV | ✓ Installed | Working |
| NumPy | ✓ Installed | 1.26.4 |
| SciPy | ✓ Installed | Working |
| PLYFile | ✓ Installed | 1.1.3 |
| FFmpeg | ✓ Installed | Working |

### ⚠️ Needs Installation

| Component | Priority | Estimated Time | Notes |
|-----------|----------|----------------|-------|
| CUDA Toolkit | HIGH | 15-20 min | Required for GPU acceleration |
| CMake | HIGH | 5 min | Required for building COLMAP |
| COLMAP | HIGH | 10 min | Pre-built binary recommended |
| PyTorch (CUDA) | HIGH | 10 min | Replace CPU version |
| Gaussian Splatting | HIGH | 30-45 min | Requires Visual Studio + CUDA |
| Visual Studio 2022 | MEDIUM | 30-60 min | Only if not installed |

## Quick Start Installation

### Step 1: Check Visual Studio (5 minutes)

Open "Visual Studio Installer" and verify you have:
- ✅ Desktop development with C++
- ✅ C++ CMake tools for Windows
- ✅ Windows 10/11 SDK

If not installed, download from: https://visualstudio.microsoft.com/downloads/

### Step 2: Install CUDA Toolkit (15-20 minutes)

```powershell
# Check your GPU
nvidia-smi

# Download CUDA 11.8 (recommended for PyTorch compatibility)
# https://developer.nvidia.com/cuda-11-8-0-download-archive

# After installation, verify:
nvcc --version

# If not found, add to PATH:
$env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"
```

### Step 3: Install CMake (5 minutes)

```powershell
# Download from: https://cmake.org/download/
# During install, select "Add CMake to system PATH"

# Verify:
cmake --version
```

### Step 4: Install COLMAP (10 minutes)

**Option A: Pre-built Binary (EASIEST)**

```powershell
# 1. Download COLMAP 3.8 from:
#    https://github.com/colmap/colmap/releases/latest

# 2. Extract to C:\Program Files\COLMAP

# 3. Add to PATH (run as Administrator):
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\Program Files\COLMAP",
    "Machine"
)

# 4. Restart PowerShell and verify:
colmap -h
```

**Option B: Chocolatey**

```powershell
choco install colmap
```

### Step 5: Install PyTorch with CUDA (10 minutes)

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate

# Uninstall CPU version
pip uninstall torch torchvision torchaudio -y

# Install CUDA version (for CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify CUDA is available
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}, Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"
```

### Step 6: Clone Gaussian Splatting (5 minutes)

```powershell
cd E:\Rk_Saklani\3d_rendering\backend

# Clone with submodules
git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive

# Verify submodules
cd gaussian-splatting
git submodule update --init --recursive
```

### Step 7: Build Gaussian Splatting (30-45 minutes)

```powershell
cd E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting
..\venv\Scripts\activate

# Install main package
pip install -e .

# Build CUDA extensions
cd submodules\diff-gaussian-rasterization
pip install -e .

cd ..\simple-knn
pip install -e .

# Return to backend
cd ..\..\..
```

### Step 8: Verify Installation

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
python scripts/check_3d_requirements.py
```

Expected output: All checks should pass ✓

## Testing the Pipeline

### Start the Services

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

### Upload Test Video

1. Open frontend: http://localhost:5173
2. Login with your credentials
3. Navigate to "3D Scenes"
4. Upload a SHORT test video (30 seconds recommended)
5. Monitor processing in Celery logs

### Expected Processing Times

For a 30-second video (1080p, 30fps):

| Step | Time | GPU Required |
|------|------|--------------|
| Frame Extraction | 10s | No |
| Frame Filtering | 20s | No |
| COLMAP | 2-3min | No |
| Depth Estimation | 30s-1min | Yes |
| Gaussian Splatting | 10-20min | Yes |
| Optimization | 1min | Yes |
| **Total** | **15-25min** | RTX GPU |

## Troubleshooting

### CUDA not detected after installation

```powershell
# Check if CUDA is in PATH
echo $env:Path | Select-String "CUDA"

# Manually add to PATH
$env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"

# Restart PowerShell
```

### COLMAP not found

```powershell
# Try full path
& "C:\Program Files\COLMAP\colmap.exe" -h

# If works, add to PATH permanently (as Administrator)
[Environment]::SetEnvironmentVariable(
    "Path",
    $env:Path + ";C:\Program Files\COLMAP",
    "Machine"
)
```

### Gaussian Splatting build fails

Common issues:
1. Visual Studio not installed → Install VS 2022 with C++ tools
2. CUDA not in PATH → Add CUDA bin directory to PATH
3. Wrong CUDA version → Ensure CUDA 11.8 or 12.1

Try verbose build:
```powershell
pip install -e . -v
```

### Out of memory during training

1. Use shorter videos (30 seconds)
2. Close other GPU applications
3. Monitor GPU usage: `nvidia-smi -l 1`
4. Reduce iterations in code (default: 7000 → 3000)

## Next Steps After Installation

1. ✅ Verify all components with check script
2. ✅ Start all services (backend, celery, frontend)
3. ✅ Upload 30-second test video
4. ✅ Monitor Celery logs for processing
5. ✅ View result in 3D viewer
6. ✅ Optimize settings for your GPU

## Support Resources

- Installation guide: `docs/3D_PIPELINE_INSTALLATION_WINDOWS.md`
- Quick steps: `docs/QUICK_INSTALL_STEPS.md`
- Check script: `backend/scripts/check_3d_requirements.py`
- Logs: `backend/logs/`

## Configuration

Current `.env` settings:

```env
CUDA_VISIBLE_DEVICES=0
GAUSSIAN_SPLATTING_PATH=E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting
```

## Estimated Total Installation Time

- **Minimum (everything works first try):** 1.5-2 hours
- **Typical (some troubleshooting):** 2-3 hours
- **Maximum (building from source):** 4-5 hours

## Installation Checklist

- [ ] Visual Studio 2022 with C++ tools
- [ ] CUDA Toolkit 11.8 or 12.1
- [ ] CMake
- [ ] COLMAP
- [ ] PyTorch with CUDA
- [ ] Gaussian Splatting repository cloned
- [ ] Gaussian Splatting CUDA extensions built
- [ ] All checks pass in verification script
- [ ] Test video processed successfully

Once all items are checked, your 3D reconstruction pipeline is ready! 🎉
