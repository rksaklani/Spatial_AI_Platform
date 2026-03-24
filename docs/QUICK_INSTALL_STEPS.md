# Quick Installation Steps for 3D Pipeline

Based on your system check, here's what you need to install:

## Current Status

✓ **Already Installed:**
- NVIDIA GPU (detected)
- PyTorch 2.10.0 (CPU version)
- OpenCV, NumPy, SciPy
- FFmpeg

⚠ **Needs Installation:**
- CUDA Toolkit
- CMake
- COLMAP
- Gaussian Splatting
- PLYFile Python package
- PyTorch with CUDA (replace CPU version)

## Installation Order

### Step 1: Install CUDA Toolkit (15-20 minutes)

1. Check your GPU architecture:
   ```powershell
   nvidia-smi
   ```

2. Download CUDA 11.8 or 12.1:
   - CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive
   - CUDA 12.1: https://developer.nvidia.com/cuda-12-1-0-download-archive

3. Run installer with default options

4. Verify installation:
   ```powershell
   nvcc --version
   ```
   
   If not found, add to PATH:
   ```powershell
   $env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"
   ```

### Step 2: Install CMake (5 minutes)

1. Download CMake Windows installer:
   https://cmake.org/download/

2. During installation, select "Add CMake to system PATH"

3. Verify:
   ```powershell
   cmake --version
   ```

### Step 3: Install COLMAP (10 minutes - Pre-built Binary)

**Option A: Pre-built Binary (RECOMMENDED)**

1. Download COLMAP 3.8 Windows binary:
   https://github.com/colmap/colmap/releases/latest

2. Extract to `C:\Program Files\COLMAP`

3. Add to PATH:
   ```powershell
   # Run as Administrator
   [Environment]::SetEnvironmentVariable(
       "Path",
       $env:Path + ";C:\Program Files\COLMAP",
       "Machine"
   )
   ```

4. Restart PowerShell and verify:
   ```powershell
   colmap -h
   ```

**Option B: Using Chocolatey (if you have it)**

```powershell
choco install colmap
```

### Step 4: Install PyTorch with CUDA (10 minutes)

```powershell
cd E:\Rk_Saklani\3d_rendering\backend

# Activate venv
.\venv\Scripts\activate

# Uninstall CPU version
pip uninstall torch torchvision torchaudio

# Install CUDA version (for CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# OR for CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Verify CUDA is available
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"
```

### Step 5: Install PLYFile (1 minute)

```powershell
pip install plyfile
```

### Step 6: Clone Gaussian Splatting (5 minutes)

```powershell
cd E:\Rk_Saklani\3d_rendering\backend

# Clone repository with submodules
git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive

# If already cloned without --recursive, update submodules:
cd gaussian-splatting
git submodule update --init --recursive
```

### Step 7: Build Gaussian Splatting CUDA Extensions (15-30 minutes)

**IMPORTANT: You need Visual Studio 2022 with C++ tools installed first!**

If you don't have Visual Studio:
1. Download Visual Studio 2022 Community: https://visualstudio.microsoft.com/downloads/
2. During installation, select:
   - ✅ Desktop development with C++
   - ✅ C++ CMake tools for Windows
   - ✅ Windows 10/11 SDK

Then build the extensions:

```powershell
cd E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting

# Activate venv
..\venv\Scripts\activate

# Install main package
pip install -e .

# Build diff-gaussian-rasterization
cd submodules\diff-gaussian-rasterization
pip install -e .

# Build simple-knn
cd ..\simple-knn
pip install -e .

# Return to backend
cd ..\..\..
```

### Step 8: Update Environment Variables

Add to `backend/.env`:

```env
# GPU Configuration
CUDA_VISIBLE_DEVICES=0
GAUSSIAN_SPLATTING_PATH=E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting
```

### Step 9: Verify Installation

```powershell
cd E:\Rk_Saklani\3d_rendering\backend
python scripts/check_3d_requirements.py
```

All checks should pass!

### Step 10: Test the Pipeline

```powershell
# Terminal 1: Start backend
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
uvicorn main:app --reload

# Terminal 2: Start Celery worker
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
celery -A workers.celery_app worker --loglevel=info --pool=solo

# Terminal 3: Start frontend
cd E:\Rk_Saklani\3d_rendering\frontend
npm run dev
```

Then upload a short test video (30 seconds) through the frontend!

## Troubleshooting

### CUDA not found after installation
- Restart PowerShell
- Check PATH: `echo $env:Path`
- Manually add: `$env:Path += ";C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin"`

### COLMAP not found
- Restart PowerShell after adding to PATH
- Try full path: `& "C:\Program Files\COLMAP\colmap.exe" -h`

### Gaussian Splatting build errors
- Ensure Visual Studio 2022 with C++ tools is installed
- Ensure CUDA is in PATH
- Try building with verbose output: `pip install -e . -v`

### Out of memory during training
- Use shorter videos (30 seconds)
- Close other GPU applications
- Reduce batch size in `backend/workers/gaussian_splatting.py`

## Estimated Total Time

- **Minimum (if everything works):** 1-1.5 hours
- **Typical (with some troubleshooting):** 2-3 hours
- **Maximum (if building from source):** 4-5 hours

## Next Steps After Installation

1. Test with a 30-second video
2. Monitor Celery logs for processing
3. Check output in 3D viewer
4. Optimize settings for your GPU

## Support

If you encounter issues:
1. Run `python scripts/check_3d_requirements.py` to see what's missing
2. Check logs in `backend/logs/`
3. Verify GPU memory: `nvidia-smi`
