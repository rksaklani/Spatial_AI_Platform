# 3D Pipeline Installation Script for Windows
# This script guides you through installing all required components

$ErrorActionPreference = "Continue"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "3D PIPELINE INSTALLATION WIZARD" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "WARNING: Not running as Administrator" -ForegroundColor Yellow
    Write-Host "Some installations may require admin privileges" -ForegroundColor Yellow
    Write-Host ""
}

# Function to check if command exists
function Test-Command {
    param($Command)
    try {
        if (Get-Command $Command -ErrorAction Stop) {
            return $true
        }
    }
    catch {
        return $false
    }
    return $false
}

# Function to prompt user
function Prompt-User {
    param($Message)
    Write-Host ""
    Write-Host $Message -ForegroundColor Yellow
    $response = Read-Host "Continue? (Y/n)"
    return ($response -eq "" -or $response -eq "Y" -or $response -eq "y")
}

# Step 1: Check Visual Studio
Write-Host "STEP 1: Visual Studio 2022" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

$vsPath = "C:\Program Files\Microsoft Visual Studio\2022\Community\Common7\IDE\devenv.exe"
if (Test-Path $vsPath) {
    Write-Host "Visual Studio 2022 found" -ForegroundColor Green
}
else {
    Write-Host "Visual Studio 2022 not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install Visual Studio 2022 Community:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://visualstudio.microsoft.com/downloads/" -ForegroundColor White
    Write-Host "2. During installation, select:" -ForegroundColor White
    Write-Host "   - Desktop development with C++" -ForegroundColor White
    Write-Host "   - C++ CMake tools for Windows" -ForegroundColor White
    Write-Host "   - Windows 10/11 SDK" -ForegroundColor White
    
    if (-not (Prompt-User "Have you installed Visual Studio 2022?")) {
        Write-Host "Installation cancelled. Please install Visual Studio first." -ForegroundColor Red
        exit 1
    }
}

# Step 2: Check CUDA
Write-Host ""
Write-Host "STEP 2: CUDA Toolkit" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

if (Test-Command "nvidia-smi") {
    Write-Host "NVIDIA GPU detected" -ForegroundColor Green
    
    if (Test-Command "nvcc") {
        $nvccVersion = nvcc --version 2>&1 | Select-String "release"
        Write-Host "CUDA Toolkit installed: $nvccVersion" -ForegroundColor Green
    }
    else {
        Write-Host "CUDA Toolkit not found (nvcc not in PATH)" -ForegroundColor Red
        Write-Host ""
        Write-Host "Please install CUDA Toolkit:" -ForegroundColor Yellow
        Write-Host "1. Download CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive" -ForegroundColor White
        Write-Host "2. Run installer with default options" -ForegroundColor White
        Write-Host "3. Restart PowerShell after installation" -ForegroundColor White
        
        if (-not (Prompt-User "Have you installed CUDA Toolkit?")) {
            Write-Host "Installation cancelled." -ForegroundColor Red
            exit 1
        }
    }
}
else {
    Write-Host "NVIDIA GPU not detected" -ForegroundColor Red
    Write-Host "This pipeline requires an NVIDIA GPU with CUDA support" -ForegroundColor Red
    exit 1
}

# Step 3: Check CMake
Write-Host ""
Write-Host "STEP 3: CMake" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

if (Test-Command "cmake") {
    $cmakeVersion = cmake --version 2>&1 | Select-Object -First 1
    Write-Host "CMake installed: $cmakeVersion" -ForegroundColor Green
}
else {
    Write-Host "CMake not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install CMake:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://cmake.org/download/" -ForegroundColor White
    Write-Host "2. Choose 'Windows x64 Installer'" -ForegroundColor White
    Write-Host "3. During install, select 'Add CMake to system PATH'" -ForegroundColor White
    Write-Host "4. Restart PowerShell after installation" -ForegroundColor White
    
    if (-not (Prompt-User "Have you installed CMake?")) {
        Write-Host "Installation cancelled." -ForegroundColor Red
        exit 1
    }
}

# Step 4: Check COLMAP
Write-Host ""
Write-Host "STEP 4: COLMAP" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

if (Test-Command "colmap") {
    Write-Host "COLMAP installed" -ForegroundColor Green
}
else {
    Write-Host "COLMAP not found" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please install COLMAP:" -ForegroundColor Yellow
    Write-Host "1. Download from: https://github.com/colmap/colmap/releases/latest" -ForegroundColor White
    Write-Host "2. Extract to: C:\Program Files\COLMAP" -ForegroundColor White
    Write-Host "3. Add to PATH (run as Administrator):" -ForegroundColor White
    Write-Host '   [Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\Program Files\COLMAP", "Machine")' -ForegroundColor Cyan
    Write-Host "4. Restart PowerShell" -ForegroundColor White
    
    if (-not (Prompt-User "Have you installed COLMAP?")) {
        Write-Host "Installation cancelled." -ForegroundColor Red
        exit 1
    }
}

# Step 5: Install PyTorch with CUDA
Write-Host ""
Write-Host "STEP 5: PyTorch with CUDA" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

Write-Host "Installing PyTorch with CUDA support..." -ForegroundColor Yellow
Write-Host ""

# Check if venv is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "Virtual environment activated" -ForegroundColor Green
}
else {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & ".\venv\Scripts\Activate.ps1"
}

Write-Host ""
Write-Host "Uninstalling CPU version of PyTorch..." -ForegroundColor Yellow
pip uninstall torch torchvision torchaudio -y 2>&1 | Out-Null

Write-Host "Installing PyTorch with CUDA 11.8..." -ForegroundColor Yellow
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

Write-Host ""
Write-Host "Verifying PyTorch CUDA installation..." -ForegroundColor Yellow
python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}'); print(f'Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else \"N/A\"}')"

# Step 6: Clone Gaussian Splatting
Write-Host ""
Write-Host "STEP 6: Gaussian Splatting Repository" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

$gsPath = "E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting"

if (Test-Path $gsPath) {
    Write-Host "Gaussian Splatting repository already exists" -ForegroundColor Green
    
    # Check if submodules are initialized
    $submodulePath = Join-Path $gsPath "submodules\diff-gaussian-rasterization"
    if (-not (Test-Path $submodulePath)) {
        Write-Host "Initializing submodules..." -ForegroundColor Yellow
        Push-Location $gsPath
        git submodule update --init --recursive
        Pop-Location
    }
}
else {
    Write-Host "Cloning Gaussian Splatting repository..." -ForegroundColor Yellow
    git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive $gsPath
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Failed to clone repository" -ForegroundColor Red
        exit 1
    }
    
    Write-Host "Repository cloned successfully" -ForegroundColor Green
}

# Step 7: Build Gaussian Splatting
Write-Host ""
Write-Host "STEP 7: Build Gaussian Splatting CUDA Extensions" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green
Write-Host "This may take 30-45 minutes..." -ForegroundColor Yellow
Write-Host ""

if (-not (Prompt-User "Ready to build CUDA extensions?")) {
    Write-Host "Skipping build. You can build later by running:" -ForegroundColor Yellow
    Write-Host "  cd $gsPath" -ForegroundColor Cyan
    Write-Host "  pip install -e ." -ForegroundColor Cyan
    Write-Host "  cd submodules\diff-gaussian-rasterization" -ForegroundColor Cyan
    Write-Host "  pip install -e ." -ForegroundColor Cyan
    Write-Host "  cd ..\simple-knn" -ForegroundColor Cyan
    Write-Host "  pip install -e ." -ForegroundColor Cyan
    exit 0
}

Push-Location $gsPath

Write-Host "Building main package..." -ForegroundColor Yellow
pip install -e .

Write-Host ""
Write-Host "Building diff-gaussian-rasterization..." -ForegroundColor Yellow
Push-Location "submodules\diff-gaussian-rasterization"
pip install -e .
Pop-Location

Write-Host ""
Write-Host "Building simple-knn..." -ForegroundColor Yellow
Push-Location "submodules\simple-knn"
pip install -e .
Pop-Location

Pop-Location

# Step 8: Verify Installation
Write-Host ""
Write-Host "STEP 8: Verification" -ForegroundColor Green
Write-Host "----------------------------------------" -ForegroundColor Green

Write-Host "Running verification script..." -ForegroundColor Yellow
Write-Host ""

python scripts\check_3d_requirements.py

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "INSTALLATION COMPLETE!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Green
Write-Host "1. Start backend: uvicorn main:app --reload" -ForegroundColor White
Write-Host "2. Start Celery: celery -A workers.celery_app worker --loglevel=info --pool=solo" -ForegroundColor White
Write-Host "3. Start frontend: cd ..\frontend && npm run dev" -ForegroundColor White
Write-Host "4. Upload a test video (30 seconds recommended)" -ForegroundColor White
Write-Host ""
Write-Host "Documentation:" -ForegroundColor Green
Write-Host "- Installation guide: docs\3D_PIPELINE_INSTALLATION_WINDOWS.md" -ForegroundColor White
Write-Host "- Status: docs\INSTALLATION_STATUS.md" -ForegroundColor White
Write-Host ""
