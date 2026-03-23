# Gaussian Splatting Setup

This document describes how to install and configure the REAL Gaussian Splatting implementation for the Spatial AI Platform.

## Overview

The platform integrates with the official **graphdeco-inria/gaussian-splatting** repository for neural scene reconstruction. This is NOT a simulation or placeholder - it uses the actual differentiable rendering and training pipeline.

## Requirements

### System Requirements

- NVIDIA GPU with CUDA support (RTX 3090 or better recommended)
- CUDA 11.8 or higher
- 16GB+ GPU memory
- 32GB+ system RAM
- Ubuntu 20.04+ or compatible Linux distribution

### Software Dependencies

- Python 3.11+
- PyTorch 2.0+ with CUDA
- CUDA Toolkit
- COLMAP (for camera pose estimation)

## Installation

### Option 1: Docker GPU Worker (Recommended)

The Gaussian Splatting repository should be installed in the GPU worker Docker image.

**Update `backend/Dockerfile.gpu`:**

```dockerfile
FROM nvidia/cuda:11.8.0-cudnn8-devel-ubuntu22.04

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3-pip \
    git \
    cmake \
    build-essential \
    libglew-dev \
    libassimp-dev \
    libboost-all-dev \
    libgtk-3-dev \
    libopencv-dev \
    libglfw3-dev \
    libavdevice-dev \
    libavcodec-dev \
    libeigen3-dev \
    libxxf86vm-dev \
    libembree-dev \
    && rm -rf /var/lib/apt/lists/*

# Clone and install Gaussian Splatting
WORKDIR /opt
RUN git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive
WORKDIR /opt/gaussian-splatting

# Install Python dependencies
RUN pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
RUN pip3 install -r requirements.txt

# Build CUDA extensions
RUN pip3 install submodules/diff-gaussian-rasterization
RUN pip3 install submodules/simple-knn

# Set environment variable
ENV GAUSSIAN_SPLATTING_PATH=/opt/gaussian-splatting

# Install platform dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

CMD ["celery", "-A", "workers.celery_app", "worker", "--loglevel=info", "--queues=gpu", "--concurrency=1"]
```

### Option 2: Manual Installation (Development)

For local development without Docker:

```bash
# Clone repository
cd /opt
git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive
cd gaussian-splatting

# Install PyTorch with CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Install dependencies
pip install -r requirements.txt

# Build CUDA extensions
pip install submodules/diff-gaussian-rasterization
pip install submodules/simple-knn

# Set environment variable
export GAUSSIAN_SPLATTING_PATH=/opt/gaussian-splatting

# Verify installation
python train.py --help
```

## Configuration

### Environment Variables

Add to your `.env` file or Docker environment:

```bash
# Path to gaussian-splatting repository
GAUSSIAN_SPLATTING_PATH=/opt/gaussian-splatting

# CUDA settings
CUDA_VISIBLE_DEVICES=0
NVIDIA_VISIBLE_DEVICES=all
NVIDIA_DRIVER_CAPABILITIES=compute,utility
```

### Docker Compose

Update `docker-compose.yml` for GPU worker:

```yaml
celery-gpu-worker:
  build:
    context: ./backend
    dockerfile: Dockerfile.gpu
  environment:
    - GAUSSIAN_SPLATTING_PATH=/opt/gaussian-splatting
    - CUDA_VISIBLE_DEVICES=0
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
```

## Usage

### Training Parameters

The platform calls Gaussian Splatting with these parameters:

```bash
python train.py \
  -s <source_dir> \
  -m <model_dir> \
  --iterations 7000 \
  --save_iterations 7000 \
  --test_iterations -1 \
  --quiet
```

Where:
- `source_dir` contains:
  - `images/` - Training frames
  - `sparse/0/` - COLMAP reconstruction (cameras.bin, images.bin, points3D.bin)
- `model_dir` - Output directory for trained model

### Expected Output

After training, the model is saved to:
```
<model_dir>/point_cloud/iteration_7000/point_cloud.ply
```

This PLY file contains the trained Gaussian parameters:
- Positions (x, y, z)
- Scales (scale_0, scale_1, scale_2)
- Rotations (rot_0, rot_1, rot_2, rot_3 as quaternion)
- Opacity
- Spherical harmonics coefficients (f_dc_*, f_rest_*)

## Verification

### Test Installation

```bash
# Check CUDA
nvidia-smi

# Check PyTorch CUDA
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}')"

# Check Gaussian Splatting
cd /opt/gaussian-splatting
python train.py --help
```

### Test Training

Use the provided test dataset:

```bash
cd /opt/gaussian-splatting
wget https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip
unzip tandt_db.zip

python train.py -s tandt/train -m output/test --iterations 1000
```

Expected output:
- Training progress logs
- Final PSNR/SSIM metrics
- PLY file in `output/test/point_cloud/iteration_1000/`

## Integration Details

### How It Works

1. **Worker receives reconstruction task** with scene_id and job_id
2. **Downloads COLMAP data** from MinIO (sparse/0/ directory)
3. **Downloads training frames** from MinIO
4. **Prepares directory structure** expected by gaussian-splatting
5. **Calls train.py via subprocess** with proper arguments
6. **Monitors training progress** through stdout
7. **Loads trained PLY** using GaussianModel.load_ply()
8. **Applies post-processing** (pruning, merging, LOD generation)
9. **Uploads results** to MinIO

### Error Handling

The integration includes robust error handling:

- **Missing repository:** Clear error message with installation instructions
- **Missing COLMAP data:** Fails with specific file requirements
- **Training failure:** Captures stdout/stderr for debugging
- **Missing output PLY:** Checks multiple possible locations

### Performance

Expected training times on RTX 3090:
- Small scenes (< 50 frames): 10-20 minutes
- Medium scenes (50-150 frames): 30-60 minutes
- Large scenes (150+ frames): 1-2 hours

## Troubleshooting

### CUDA Out of Memory

Reduce batch size or image resolution:

```bash
# Edit train.py or add arguments
--resolution 2  # Reduce resolution by factor of 2
```

### Training Fails

Check logs:

```bash
docker logs spatial-ai-celery-gpu-worker
```

Common issues:
- COLMAP data incomplete or corrupted
- Insufficient GPU memory
- CUDA version mismatch

### Slow Training

Verify GPU is being used:

```bash
# During training, check GPU utilization
nvidia-smi -l 1
```

Should show high GPU utilization (>80%) during training.

## Production Considerations

### GPU Scaling

- Use dedicated GPU workers for reconstruction
- Queue reconstruction tasks to GPU queue
- Monitor GPU memory and adjust concurrency

### Cost Optimization

- Use spot instances for GPU workers
- Implement auto-scaling based on queue depth
- Cache trained models to avoid retraining

### Quality vs Speed

Adjust iterations based on requirements:
- Quick preview: 3000 iterations (~15 min)
- Standard quality: 7000 iterations (~30 min)
- High quality: 15000 iterations (~1 hour)

## References

- [Gaussian Splatting Paper](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/)
- [GitHub Repository](https://github.com/graphdeco-inria/gaussian-splatting)
- [COLMAP Documentation](https://colmap.github.io/)

## Migration from Fake Implementation

The previous placeholder implementation has been replaced with this real integration. Key changes:

**Removed:**
- Simulated training loop with fake PSNR/SSIM
- Fake densification logic
- Placeholder rendering

**Added:**
- Real subprocess call to train.py
- Proper COLMAP data structure handling
- Actual trained model loading
- Real metrics from training output

**Kept:**
- GaussianModel.load_ply() for loading trained models
- save_ply() for exporting
- Post-processing (pruning, merging, LOD generation)
- MinIO upload/download pipeline
- Job progress tracking
