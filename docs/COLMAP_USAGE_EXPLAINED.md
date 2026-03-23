# COLMAP Usage in the Spatial AI Platform

## Quick Answer

**Yes, Gaussian Splatting needs COLMAP** - but only for **Phase 2 (Video Processing)**, specifically for camera pose estimation.

## Where COLMAP is Used

### Phase 2: Video Upload and Processing Pipeline

**Task 6: Camera Pose Estimation** (Phase 2)

COLMAP is used in the video processing pipeline to:

1. **Extract SIFT features** from video frames
2. **Match features** between frame pairs
3. **Perform sparse reconstruction** to calculate:
   - Camera intrinsics (focal length, principal point)
   - Camera extrinsics (rotation, translation) for each frame
   - Sparse 3D point cloud

**File:** `backend/workers/video_pipeline.py`

```python
def estimate_camera_poses(frames_dir: str, valid_frames: list, output_dir: str):
    """
    Estimate camera poses using COLMAP.
    
    Steps:
    1. colmap feature_extractor - Extract SIFT features
    2. colmap exhaustive_matcher - Match features between frames
    3. colmap mapper - Sparse reconstruction (SfM)
    
    Output:
    - sparse/0/cameras.bin - Camera intrinsics
    - sparse/0/images.bin - Camera poses
    - sparse/0/points3D.bin - Sparse point cloud
    """
```

### Phase 3: Neural Reconstruction

**Task 9: 3D Gaussian Splatting Reconstruction** (Phase 3)

Gaussian Splatting **uses the COLMAP output** from Phase 2:

**File:** `backend/workers/gaussian_splatting.py`

```python
def load_colmap_points(sparse_dir: str):
    """
    Load points from COLMAP sparse reconstruction.
    
    Reads: sparse/0/points3D.bin
    Returns: 3D points and colors for Gaussian initialization
    """

def reconstruct_scene(scene_id: str, sparse_dir: str, images_dir: str):
    """
    Train Gaussian Splatting model.
    
    Requires:
    - sparse/0/ directory with COLMAP output
    - images/ directory with training frames
    
    Process:
    1. Load COLMAP sparse points
    2. Initialize Gaussians from points
    3. Train with photometric loss
    4. Export to PLY format
    """
```

## The Complete Flow

```
Phase 2: Video Processing
┌─────────────────────────────────────────┐
│ 1. Upload Video                         │
│ 2. Extract Frames (FFmpeg)              │
│ 3. Filter Frames (blur/motion)          │
│ 4. COLMAP Camera Pose Estimation ◄──────┼─── COLMAP USED HERE
│    - Feature extraction (SIFT)          │
│    - Feature matching                   │
│    - Sparse reconstruction (SfM)        │
│    Output: cameras.bin, images.bin,     │
│            points3D.bin                  │
│ 5. Depth Estimation (MiDaS)             │
└─────────────────────────────────────────┘
                  │
                  │ COLMAP output stored in MinIO
                  ▼
Phase 3: Neural Reconstruction
┌─────────────────────────────────────────┐
│ 9. Gaussian Splatting Reconstruction    │
│    - Load COLMAP sparse points ◄────────┼─── USES COLMAP OUTPUT
│    - Initialize Gaussians               │
│    - Train model                        │
│    - Export PLY                         │
└─────────────────────────────────────────┘
```

## Why COLMAP is Needed

### For Video Input
When users upload a **video**, we need to:
1. Determine where the camera was for each frame
2. Understand the 3D structure of the scene
3. Initialize Gaussians at the correct 3D positions

**COLMAP provides:**
- Camera poses (where camera was for each frame)
- Sparse 3D points (initial scene structure)
- Camera calibration (focal length, distortion)

### For 3D File Import (Phase 4)
When users upload **3D files** (PLY, OBJ, GLTF, etc.):
- **COLMAP is NOT needed** ❌
- Files already contain 3D geometry
- Can directly load and render

## Fallback Behavior

The code includes fallback when COLMAP is not available:

```python
try:
    # Run COLMAP commands
    subprocess.run(["colmap", "feature_extractor", ...])
    subprocess.run(["colmap", "exhaustive_matcher", ...])
    subprocess.run(["colmap", "mapper", ...])
except (subprocess.CalledProcessError, FileNotFoundError) as e:
    logger.warning(f"COLMAP failed, using fallback: {e}")
    # Fallback: Create dummy camera data
    # Gaussian Splatting will use random initialization
```

**Fallback behavior:**
- Creates dummy camera poses
- Uses random point initialization for Gaussians
- Quality will be lower, but system won't crash

## Installation

### COLMAP Installation (Optional but Recommended)

**For video processing to work properly, install COLMAP:**

#### Windows:
```bash
# Download from: https://github.com/colmap/colmap/releases
# Or use vcpkg:
vcpkg install colmap
```

#### Linux:
```bash
sudo apt-get install colmap
```

#### macOS:
```bash
brew install colmap
```

### Verify Installation:
```bash
colmap -h
```

## Summary

| Phase | Task | COLMAP Usage |
|-------|------|--------------|
| Phase 2 | Video Processing | ✅ **Required** for camera pose estimation |
| Phase 3 | Gaussian Splatting | ✅ **Uses output** from Phase 2 |
| Phase 4 | 3D Import | ❌ Not needed (files have geometry) |
| Phase 5 | Web Viewer | ❌ Not needed (renders PLY files) |

**Bottom Line:**
- COLMAP is used in **Phase 2** to process videos
- Gaussian Splatting in **Phase 3** uses COLMAP's output
- For 3D file imports, COLMAP is not needed
- System has fallback if COLMAP is unavailable (lower quality)

## Alternative: Camera Metadata Import

If you have camera data from another source (photogrammetry software, etc.), you can:

1. Use **Task 15.5: Camera Metadata Import** (Phase 4)
2. Import camera poses from CSV, XML, TXT, FBX, or ABC files
3. Skip COLMAP entirely
4. Use imported camera data for Gaussian Splatting

This is useful when:
- You already have camera calibration data
- You're using professional photogrammetry equipment
- You want to bypass COLMAP for custom workflows
