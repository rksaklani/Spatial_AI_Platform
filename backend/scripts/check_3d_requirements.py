"""
Check 3D Pipeline Requirements

This script checks what's already installed and what still needs to be installed
for the full 3D reconstruction pipeline.
"""

import subprocess
import sys
import os

def check_command(cmd, name):
    """Check if a command is available."""
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        return True, result.stdout.split('\n')[0] if result.stdout else "Installed"
    except FileNotFoundError:
        return False, "Not found in PATH"
    except Exception as e:
        return False, str(e)

def check_python_package(package_name, import_name=None):
    """Check if a Python package is installed."""
    if import_name is None:
        import_name = package_name
    
    try:
        __import__(import_name)
        return True, "Installed"
    except ImportError:
        return False, "Not installed"

print("="*70)
print("3D PIPELINE REQUIREMENTS CHECK")
print("="*70)

# System Requirements
print("\n1. SYSTEM REQUIREMENTS")
print("-" * 70)

# Visual Studio
print("\n   Visual Studio Build Tools:")
print("   → Check manually: Open 'Visual Studio Installer'")
print("   → Required: Desktop development with C++")

# CUDA
print("\n   NVIDIA GPU & CUDA:")
cuda_ok, cuda_info = check_command(["nvidia-smi"], "nvidia-smi")
if cuda_ok:
    print(f"   ✓ NVIDIA GPU detected")
    nvcc_ok, nvcc_info = check_command(["nvcc", "--version"], "nvcc")
    if nvcc_ok:
        print(f"   ✓ CUDA Toolkit: {nvcc_info}")
    else:
        print(f"   ✗ CUDA Toolkit (nvcc): {nvcc_info}")
else:
    print(f"   ✗ NVIDIA GPU: {cuda_info}")

# CMake
print("\n   CMake:")
cmake_ok, cmake_info = check_command(["cmake", "--version"], "cmake")
if cmake_ok:
    print(f"   ✓ {cmake_info}")
else:
    print(f"   ✗ CMake: {cmake_info}")

# vcpkg
print("\n   vcpkg:")
vcpkg_path = "C:\\vcpkg\\vcpkg.exe"
if os.path.exists(vcpkg_path):
    print(f"   ✓ vcpkg found at {vcpkg_path}")
else:
    print(f"   ✗ vcpkg not found at {vcpkg_path}")

# 2. COLMAP
print("\n2. COLMAP")
print("-" * 70)
colmap_ok, colmap_info = check_command(["colmap", "-h"], "colmap")
if colmap_ok:
    print(f"   ✓ COLMAP installed")
else:
    print(f"   ✗ COLMAP: {colmap_info}")
    print("   → Download from: https://github.com/colmap/colmap/releases")

# 3. Python Dependencies
print("\n3. PYTHON DEPENDENCIES")
print("-" * 70)

# PyTorch
torch_ok, torch_info = check_python_package("torch")
if torch_ok:
    try:
        import torch
        print(f"   ✓ PyTorch {torch.__version__}")
        if torch.cuda.is_available():
            print(f"   ✓ CUDA available: {torch.cuda.get_device_name(0)}")
            print(f"   ✓ CUDA version: {torch.version.cuda}")
        else:
            print(f"   ⚠ PyTorch installed but CUDA not available")
    except Exception as e:
        print(f"   ⚠ PyTorch installed but error checking CUDA: {e}")
else:
    print(f"   ✗ PyTorch: {torch_info}")
    print("   → Install: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118")

# Other Python packages
packages = [
    ("opencv-python", "cv2", "OpenCV"),
    ("numpy", "numpy", "NumPy"),
    ("scipy", "scipy", "SciPy"),
    ("plyfile", "plyfile", "PLYFile"),
]

for pkg_name, import_name, display_name in packages:
    ok, info = check_python_package(pkg_name, import_name)
    if ok:
        print(f"   ✓ {display_name}")
    else:
        print(f"   ✗ {display_name}: {info}")

# 4. Gaussian Splatting
print("\n4. GAUSSIAN SPLATTING")
print("-" * 70)

gs_path = os.environ.get("GAUSSIAN_SPLATTING_PATH", "E:\\Rk_Saklani\\3d_rendering\\backend\\gaussian-splatting")
if os.path.exists(gs_path):
    print(f"   ✓ Repository found at: {gs_path}")
    
    # Check if train.py exists
    train_script = os.path.join(gs_path, "train.py")
    if os.path.exists(train_script):
        print(f"   ✓ train.py found")
    else:
        print(f"   ✗ train.py not found")
    
    # Check CUDA extensions
    diff_rast_ok, _ = check_python_package("diff_gaussian_rasterization")
    simple_knn_ok, _ = check_python_package("simple_knn")
    
    if diff_rast_ok:
        print(f"   ✓ diff-gaussian-rasterization installed")
    else:
        print(f"   ✗ diff-gaussian-rasterization not installed")
    
    if simple_knn_ok:
        print(f"   ✓ simple-knn installed")
    else:
        print(f"   ✗ simple-knn not installed")
else:
    print(f"   ✗ Repository not found at: {gs_path}")
    print("   → Clone: git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive")

# 5. FFmpeg
print("\n5. FFMPEG")
print("-" * 70)
ffmpeg_ok, ffmpeg_info = check_command(["ffmpeg", "-version"], "ffmpeg")
if ffmpeg_ok:
    print(f"   ✓ FFmpeg installed")
else:
    print(f"   ✗ FFmpeg: {ffmpeg_info}")
    print("   → Install: choco install ffmpeg")

# Summary
print("\n" + "="*70)
print("INSTALLATION SUMMARY")
print("="*70)

missing = []

if not cuda_ok:
    missing.append("CUDA Toolkit")
if not cmake_ok:
    missing.append("CMake")
if not colmap_ok:
    missing.append("COLMAP")
if not torch_ok:
    missing.append("PyTorch with CUDA")
if not os.path.exists(gs_path):
    missing.append("Gaussian Splatting repository")
if not ffmpeg_ok:
    missing.append("FFmpeg")

if missing:
    print("\n⚠ MISSING COMPONENTS:")
    for item in missing:
        print(f"   - {item}")
    print("\nFollow the installation guide:")
    print("   docs/3D_PIPELINE_INSTALLATION_WINDOWS.md")
else:
    print("\n✓ ALL COMPONENTS INSTALLED!")
    print("\nYou can now:")
    print("   1. Start the backend: uvicorn main:app --reload")
    print("   2. Start Celery worker: celery -A workers.celery_app worker --loglevel=info --pool=solo")
    print("   3. Upload a test video through the frontend")

print("\n" + "="*70)
