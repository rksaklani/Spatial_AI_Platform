# 3D Processing Pipeline Installation Guide (Windows)

This guide will help you install COLMAP, Gaussian Splatting, and all dependencies for full 3D reconstruction.

## Prerequisites

- Windows 10/11
- NVIDIA GPU with CUDA support (GTX 1060 or better)
- 16GB+ RAM recommended
- 50GB+ free disk space

## Step 1: Install Visual Studio Build Tools

COLMAP and Gaussian Splatting require C++ compilation.

1. Download Visual Studio 2022 Community: https://visualstudio.microsoft.com/downloads/
2. During installation, select:
   - ✅ Desktop development with C++
   - ✅ C++ CMake tools for Windows
   - ✅ Windows 10/11 SDK

## Step 2: Install CUDA Toolkit

Required for GPU acceleration.

1. Check your GPU: `nvidia-smi` in PowerShell
2. Download CUDA 11.8 or 12.1: https://developer.nvidia.com/cuda-downloads
3. Install with default options
4. Verify: `nvcc --version`

## Step 3: Install CMake

1. Download CMake: https://cmake.org/download/
2. Choose "Windows x64 Installer"
3. During install, select "Add CMake to system PATH"
4. Verify: `cmake --version`

## Step 4: Install vcpkg (Package Manager)

```powershell
# Clone vcpkg
cd C:\
git clone https://github.com/Microsoft/vcpkg.git
cd vcpkg

# Bootstrap vcpkg
.\bootstrap-vcpkg.bat

# Add to PATH (run as Administrator)
[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\vcpkg", "Machine")
```

## Step 5: Install COLMAP Dependencies via vcpkg

```powershell
cd C:\vcpkg

# Install COLMAP dependencies (this takes 30-60 minutes)
.\vcpkg install ^
  ceres[suitesparse]:x64-windows ^
  eigen3:x64-windows ^
  freeimage:x64-windows ^
  glog:x64-windows ^
  gflags:x64-windows ^
  glew:x64-windows ^
  sqlite3:x64-windows ^
  qt5-base:x64-windows ^
  cgal:x64-windows

# Integrate with Visual Studio
.\vcpkg integrate install
```

## Step 6: Install COLMAP

### Option A: Pre-built Binary (Easiest)

1. Download COLMAP 3.8: https://github.com/colmap/colmap/releases
2. Extract to `C:\Program Files\COLMAP`
3. Add to PATH:
   ```powershell
   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\COLMAP", "Machine")
   ```
4. Verify: `colmap -h`

### Option B: Build from Source (Advanced)

```powershell
# Clone COLMAP
git clone https://github.com/colmap/colmap.git
cd colmap

# Create build directory
mkdir build
cd build

# Configure with CMake
cmake .. -DCMAKE_TOOLCHAIN_FILE=C:/vcpkg/scripts/buildsystems/vcpkg.cmake

# Build (takes 20-30 minutes)
cmake --build . --config Release

# Install
cmake --install . --prefix "C:\Program Files\COLMAP"
```

## Step 7: Install Python Dependencies

```powershell
cd E:\Rk_Saklani\3d_rendering\backend

# Activate venv
.\venv\Scripts\activate

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install other dependencies
pip install -r requirements.txt
```

## Step 8: Install Gaussian Splatting

```powershell
cd E:\Rk_Saklani\3d_rendering\backend

# Clone Gaussian Splatting repo
git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive
cd gaussian-splatting

# Install submodules
git submodule update --init --recursive

# Install Python package
pip install -e .

# Build CUDA extensions
cd submodules/diff-gaussian-rasterization
pip install -e .

cd ../simple-knn
pip install -e .
```

## Step 9: Verify Installation

Create a test script `backend/scripts/test_3d_pipeline.py`:

```python
import subprocess
import sys
import torch

print("="*60)
print("3D PIPELINE INSTALLATION TEST")
print("="*60)

# Test 1: COLMAP
print("\n1. Testing COLMAP...")
try:
    result = subprocess.run(["colmap", "-h"], capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✓ COLMAP installed")
    else:
        print("   ✗ COLMAP not found")
except FileNotFoundError:
    print("   ✗ COLMAP not found in PATH")

# Test 2: CUDA
print("\n2. Testing CUDA...")
if torch.cuda.is_available():
    print(f"   ✓ CUDA available: {torch.cuda.get_device_name(0)}")
    print(f"   ✓ CUDA version: {torch.version.cuda}")
else:
    print("   ✗ CUDA not available")

# Test 3: PyTorch
print("\n3. Testing PyTorch...")
print(f"   ✓ PyTorch version: {torch.__version__}")

# Test 4: Gaussian Splatting
print("\n4. Testing Gaussian Splatting...")
try:
    from diff_gaussian_rasterization import GaussianRasterizationSettings
    print("   ✓ Gaussian Splatting installed")
except ImportError as e:
    print(f"   ✗ Gaussian Splatting not installed: {e}")

# Test 5: FFmpeg
print("\n5. Testing FFmpeg...")
try:
    result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
    if result.returncode == 0:
        print("   ✓ FFmpeg installed")
    else:
        print("   ✗ FFmpeg not found")
except FileNotFoundError:
    print("   ✗ FFmpeg not found in PATH")

print("\n" + "="*60)
print("Installation test complete!")
print("="*60)
```

Run the test:
```powershell
python scripts/test_3d_pipeline.py
```

## Step 10: Install FFmpeg (Video Processing)

```powershell
# Using Chocolatey
choco install ffmpeg

# Or download from: https://ffmpeg.org/download.html
# Extract and add to PATH
```

## Step 11: Configure Backend

Update `backend/.env`:

```env
# GPU Configuration
CUDA_VISIBLE_DEVICES=0
TORCH_CUDA_ARCH_LIST="7.5;8.0;8.6"  # Adjust for your GPU

# Processing Configuration
COLMAP_PATH=C:\Program Files\COLMAP\colmap.exe
GAUSSIAN_SPLATTING_PATH=E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting
```

## Troubleshooting

### COLMAP not found
- Verify PATH: `echo $env:Path`
- Restart PowerShell after adding to PATH
- Try full path: `C:\Program Files\COLMAP\colmap.exe -h`

### CUDA errors
- Check GPU: `nvidia-smi`
- Verify CUDA version matches PyTorch: `nvcc --version`
- Reinstall PyTorch with correct CUDA version

### Gaussian Splatting build errors
- Ensure Visual Studio 2022 is installed
- Check CUDA toolkit is in PATH
- Try building with verbose output: `pip install -e . -v`

### Out of memory errors
- Reduce batch size in `backend/workers/gaussian_splatting.py`
- Close other GPU applications
- Use smaller videos for testing

## Testing the Full Pipeline

1. Start backend:
   ```powershell
   cd backend
   uvicorn main:app --reload
   ```

2. Start Celery worker:
   ```powershell
   cd backend
   celery -A workers.celery_app worker --loglevel=info --pool=solo
   ```

3. Upload a test video through the frontend

4. Monitor processing:
   - Check Celery logs
   - Check MongoDB for job status
   - Check MinIO for output files

## Expected Processing Times

For a 5-minute video (1080p, 30fps):

| Step | Time | GPU |
|------|------|-----|
| Frame Extraction | 30s | No |
| Frame Intelligence | 1min | No |
| COLMAP | 5-10min | No |
| Depth Estimation | 2-5min | Yes |
| Gaussian Splatting | 30-60min | Yes |
| Optimization | 5min | Yes |
| Tiling | 5min | No |
| **Total** | **45-80min** | RTX 3090 |

## Performance Tips

1. **Use SSD** for faster I/O
2. **Close other apps** to free GPU memory
3. **Use smaller videos** for testing (30s-1min)
4. **Monitor GPU usage**: `nvidia-smi -l 1`
5. **Check logs** for bottlenecks

## Next Steps

Once everything is installed:

1. Test with a short video (30 seconds)
2. Monitor the full pipeline
3. Check output quality in the 3D viewer
4. Optimize settings based on your GPU

## Support

If you encounter issues:

1. Check logs in `backend/logs/`
2. Run the test script above
3. Verify all dependencies are installed
4. Check GPU memory: `nvidia-smi`

## Summary

You now have:
- ✅ COLMAP for camera pose estimation
- ✅ Gaussian Splatting for 3D reconstruction
- ✅ CUDA for GPU acceleration
- ✅ All Python dependencies
- ✅ FFmpeg for video processing

The full 3D reconstruction pipeline is ready!
