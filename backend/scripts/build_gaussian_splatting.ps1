# Build Gaussian Splatting CUDA Extensions
# Run this after PyTorch with CUDA is installed

Write-Host "Building Gaussian Splatting CUDA Extensions" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$gsPath = "E:\Rk_Saklani\3d_rendering\backend\gaussian-splatting"

if (-not (Test-Path $gsPath)) {
    Write-Host "ERROR: Gaussian Splatting repository not found at: $gsPath" -ForegroundColor Red
    Write-Host "Please clone it first:" -ForegroundColor Yellow
    Write-Host "  git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive $gsPath" -ForegroundColor Cyan
    exit 1
}

# Check if PyTorch with CUDA is installed
Write-Host "Checking PyTorch installation..." -ForegroundColor Yellow
python -c "import torch; assert torch.cuda.is_available(), 'CUDA not available'; print(f'PyTorch {torch.__version__} with CUDA {torch.version.cuda}')" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyTorch with CUDA is not installed" -ForegroundColor Red
    Write-Host "Please install it first:" -ForegroundColor Yellow
    Write-Host "  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118" -ForegroundColor Cyan
    exit 1
}

Write-Host "PyTorch with CUDA is installed" -ForegroundColor Green
Write-Host ""

# Build diff-gaussian-rasterization
Write-Host "Building diff-gaussian-rasterization..." -ForegroundColor Yellow
Write-Host "This may take 10-15 minutes..." -ForegroundColor Yellow
Push-Location "$gsPath\submodules\diff-gaussian-rasterization"

pip install --no-build-isolation -e .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to build diff-gaussian-rasterization" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host "diff-gaussian-rasterization built successfully" -ForegroundColor Green
Write-Host ""

# Build simple-knn
Write-Host "Building simple-knn..." -ForegroundColor Yellow
Write-Host "This may take 5-10 minutes..." -ForegroundColor Yellow
Push-Location "$gsPath\submodules\simple-knn"

pip install --no-build-isolation -e .

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to build simple-knn" -ForegroundColor Red
    Pop-Location
    exit 1
}

Pop-Location
Write-Host "simple-knn built successfully" -ForegroundColor Green
Write-Host ""

# Verify installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
python -c "from diff_gaussian_rasterization import GaussianRasterizationSettings; print('diff-gaussian-rasterization: OK')"
python -c "import simple_knn; print('simple-knn: OK')"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host "BUILD COMPLETE!" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Gaussian Splatting CUDA extensions are ready!" -ForegroundColor Green
}
else {
    Write-Host ""
    Write-Host "Build completed but verification failed" -ForegroundColor Yellow
    Write-Host "You may need to restart PowerShell" -ForegroundColor Yellow
}
