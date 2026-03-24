# Complete Pipeline Guide: Frontend to Backend to 3D Rendering

## Overview

This guide explains the complete data flow from user input in the frontend through backend processing (including COLMAP photogrammetry) to final 3D model rendering in the browser.

---

## Table of Contents

1. [Pipeline Architecture](#pipeline-architecture)
2. [Frontend Input Flow](#frontend-input-flow)
3. [Backend Processing Pipeline](#backend-processing-pipeline)
4. [COLMAP Integration](#colmap-integration)
5. [3D Reconstruction with Gaussian Splatting](#3d-reconstruction)
6. [Browser Rendering](#browser-rendering)
7. [Use Cases](#use-cases)

---

## Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React)                         │
├─────────────────────────────────────────────────────────────────┤
│  User Upload → API Call → Status Polling → Tile Streaming       │
│  (Video/3D)    (REST)     (WebSocket)      (Progressive Load)   │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI)                           │
├─────────────────────────────────────────────────────────────────┤
│  Upload API → MinIO Storage → Celery Queue → GPU Workers        │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│  1. Frame Extraction (FFmpeg)                                    │
│  2. Frame Intelligence (Blur/Motion Detection)                   │
│  3. Camera Pose Estimation (COLMAP)                              │
│  4. Depth Estimation (MiDaS)                                     │
│  5. 3D Reconstruction (Gaussian Splatting)                       │
│  6. Scene Optimization (Pruning/LOD)                             │
│  7. Tiling (Octree Spatial Partitioning)                         │
└────────────┬────────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STORAGE & SERVING                             │
├─────────────────────────────────────────────────────────────────┤
│  MinIO (Tiles) → Valkey (Cache) → Streaming API → Frontend      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Frontend Input Flow

### Step 1: User Uploads Video or 3D File

**Location**: `frontend/src/components/dashboard/UploadDialog.tsx`

```typescript
// User selects file
const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
  const file = event.target.files?.[0];
  if (!file) return;
  
  // Validate file type and size
  const validVideoTypes = ['video/mp4', 'video/quicktime', 'video/x-msvideo'];
  const valid3DTypes = ['.ply', '.las', '.obj', '.gltf', '.glb', '.splat'];
  
  if (file.size > 5 * 1024 * 1024 * 1024) { // 5GB limit
    alert('File too large. Maximum size is 5GB');
    return;
  }
  
  uploadFile(file);
};
```

### Step 2: Frontend Sends File to Backend

**Location**: `frontend/src/store/api/sceneApi.ts`

```typescript
// RTK Query mutation for upload
export const sceneApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    uploadVideo: builder.mutation<Scene, FormData>({
      query: (formData) => ({
        url: '/scenes/upload',
        method: 'POST',
        body: formData,
      }),
    }),
  }),
});

// Usage in component
const [uploadVideo, { isLoading }] = useUploadVideoMutation();

const uploadFile = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', file.name);
  
  try {
    const result = await uploadVideo(formData).unwrap();
    console.log('Scene created:', result.scene_id);
    // Navigate to scene viewer or show processing status
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

---

## Backend Processing Pipeline

### Step 1: Upload API Receives File

**Location**: `backend/api/scenes.py`

```python
from fastapi import APIRouter, UploadFile, File, Depends
from uuid import uuid4

router = APIRouter()

@router.post("/scenes/upload")
async def upload_video(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    org_context: Organization = Depends(get_organization_context)
):
    # Generate unique scene ID
    scene_id = str(uuid4())
    
    # Validate file
    if file.content_type not in ['video/mp4', 'video/quicktime']:
        raise HTTPException(400, "Invalid file type")
    
    # Store to MinIO
    file_path = f"videos/{org_context.id}/{scene_id}/original.mp4"
    await minio_client.upload_file(file.file, "videos", file_path)
    
    # Create scene record in MongoDB
    scene = Scene(
        id=scene_id,
        organization_id=org_context.id,
        user_id=current_user.id,
        filename=file.filename,
        status="uploaded",
        file_size=file.size,
        created_at=datetime.utcnow()
    )
    await scenes_collection.insert_one(scene.dict())
    
    # Enqueue processing job
    from workers.video_pipeline import process_video
    job = process_video.delay(scene_id, org_context.id)
    
    return {"scene_id": scene_id, "job_id": job.id, "status": "queued"}
```

### Step 2: Celery Worker Processes Video

**Location**: `backend/workers/video_pipeline.py`

```python
from celery import Task
from workers.celery_app import celery_app

@celery_app.task(bind=True, name='process_video')
def process_video(self: Task, scene_id: str, org_id: str):
    """
    Complete video processing pipeline
    """
    try:
        # Update status
        update_scene_status(scene_id, "processing")
        
        # Step 1: Extract frames
        frames = extract_frames(scene_id, org_id)
        update_scene_status(scene_id, "extracting_frames", 
                          progress=20)
        
        # Step 2: Filter frames (blur/motion detection)
        valid_frames = filter_frames(frames)
        update_scene_status(scene_id, "filtering_frames", 
                          progress=30)
        
        # Step 3: Estimate camera poses with COLMAP
        camera_data = estimate_camera_poses(scene_id, valid_frames)
        update_scene_status(scene_id, "estimating_poses", 
                          progress=50)
        
        # Step 4: Estimate depth maps
        depth_maps = estimate_depth_maps(scene_id, valid_frames)
        update_scene_status(scene_id, "estimating_depth", 
                          progress=60)
        
        # Step 5: 3D Reconstruction (Gaussian Splatting)
        gaussian_model = reconstruct_scene(scene_id, camera_data, 
                                          valid_frames, depth_maps)
        update_scene_status(scene_id, "reconstructing", 
                          progress=80)
        
        # Step 6: Optimize and tile
        tiles = optimize_and_tile(scene_id, gaussian_model)
        update_scene_status(scene_id, "optimizing", 
                          progress=95)
        
        # Final status
        update_scene_status(scene_id, "completed", progress=100)
        
        return {"status": "success", "scene_id": scene_id}
        
    except Exception as e:
        update_scene_status(scene_id, "failed", error=str(e))
        raise
```

---

## COLMAP Integration

### What is COLMAP?

COLMAP is a photogrammetry software that reconstructs 3D structure from 2D images using Structure-from-Motion (SfM).

**Key Concepts**:
- **Feature Detection**: Finds distinctive points in images (SIFT features)
- **Feature Matching**: Matches features across multiple images
- **Camera Pose Estimation**: Calculates camera position and orientation
- **Sparse Reconstruction**: Creates 3D point cloud from matched features
- **Bundle Adjustment**: Refines camera poses and 3D points

### COLMAP Pipeline Implementation

**Location**: `backend/workers/video_pipeline.py`


```python
def estimate_camera_poses(scene_id: str, frames: List[str]) -> dict:
    """
    Use COLMAP to estimate camera poses from video frames
    
    COLMAP Pipeline:
    1. Feature Extraction (SIFT)
    2. Feature Matching
    3. Sparse Reconstruction
    4. Bundle Adjustment
    """
    import subprocess
    import os
    
    # Create workspace directory
    workspace = f"/tmp/colmap_{scene_id}"
    os.makedirs(workspace, exist_ok=True)
    os.makedirs(f"{workspace}/images", exist_ok=True)
    os.makedirs(f"{workspace}/sparse", exist_ok=True)
    
    # Download frames from MinIO to workspace
    for frame_path in frames:
        local_path = f"{workspace}/images/{os.path.basename(frame_path)}"
        minio_client.download_file("frames", frame_path, local_path)
    
    # Step 1: Feature Extraction
    # Detects SIFT keypoints in each image
    subprocess.run([
        "colmap", "feature_extractor",
        "--database_path", f"{workspace}/database.db",
        "--image_path", f"{workspace}/images",
        "--ImageReader.single_camera", "1",  # Assume single camera
        "--SiftExtraction.use_gpu", "1"      # Use GPU acceleration
    ], check=True)
    
    # Step 2: Feature Matching
    # Matches features between image pairs
    subprocess.run([
        "colmap", "exhaustive_matcher",
        "--database_path", f"{workspace}/database.db",
        "--SiftMatching.use_gpu", "1"
    ], check=True)
    
    # Step 3: Sparse Reconstruction
    # Estimates camera poses and creates sparse 3D point cloud
    subprocess.run([
        "colmap", "mapper",
        "--database_path", f"{workspace}/database.db",
        "--image_path", f"{workspace}/images",
        "--output_path", f"{workspace}/sparse"
    ], check=True)
    
    # Step 4: Bundle Adjustment (optional refinement)
    subprocess.run([
        "colmap", "bundle_adjuster",
        "--input_path", f"{workspace}/sparse/0",
        "--output_path", f"{workspace}/sparse/0"
    ], check=True)
    
    # Parse COLMAP output
    camera_data = parse_colmap_output(f"{workspace}/sparse/0")
    
    # Upload sparse reconstruction to MinIO
    upload_sparse_data(scene_id, f"{workspace}/sparse/0")
    
    return camera_data

def parse_colmap_output(sparse_path: str) -> dict:
    """
    Parse COLMAP binary files (cameras.bin, images.bin, points3D.bin)
    """
    from colmap_utils import read_cameras_binary, read_images_binary, read_points3D_binary
    
    cameras = read_cameras_binary(f"{sparse_path}/cameras.bin")
    images = read_images_binary(f"{sparse_path}/images.bin")
    points3d = read_points3D_binary(f"{sparse_path}/points3D.bin")
    
    return {
        "cameras": cameras,      # Camera intrinsics (focal length, principal point)
        "images": images,        # Camera extrinsics (rotation, translation)
        "points3d": points3d,    # Sparse 3D point cloud
        "num_cameras": len(cameras),
        "num_images": len(images),
        "num_points": len(points3d)
    }
```

### Understanding Camera Parameters

**Intrinsics** (Internal camera properties):
- `fx, fy`: Focal length in pixels
- `cx, cy`: Principal point (image center)
- `k1, k2, k3`: Radial distortion coefficients

**Extrinsics** (Camera pose in 3D space):
- `R`: 3x3 rotation matrix
- `t`: 3x1 translation vector
- Together they define camera position and orientation

---

## 3D Reconstruction with Gaussian Splatting

### What is Gaussian Splatting?

Gaussian Splatting represents 3D scenes as a collection of 3D Gaussians (ellipsoids) with properties:
- **Position** (x, y, z): Center of the Gaussian
- **Covariance** (scale + rotation): Shape and orientation
- **Color** (SH coefficients): View-dependent appearance
- **Opacity** (α): Transparency

### Reconstruction Pipeline

**Location**: `backend/workers/gaussian_splatting.py`

```python
def reconstruct_scene(scene_id: str, camera_data: dict, 
                     frames: List[str], depth_maps: List[str]) -> GaussianModel:
    """
    3D Gaussian Splatting reconstruction
    
    Process:
    1. Initialize Gaussians from COLMAP sparse points
    2. Train via differentiable rendering
    3. Optimize with photometric loss
    4. Adaptive density control (densify/prune)
    """
    import torch
    from gaussian_model import GaussianModel
    
    # Initialize model
    model = GaussianModel()
    
    # Step 1: Initialize from sparse point cloud
    sparse_points = camera_data['points3d']
    model.initialize_from_points(sparse_points)
    
    # Step 2: Training loop
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
    
    for iteration in range(7000):  # 7000 iterations minimum
        # Select random training view
        camera_idx = random.randint(0, len(frames) - 1)
        camera = camera_data['images'][camera_idx]
        gt_image = load_image(frames[camera_idx])
        
        # Render from camera viewpoint
        rendered_image = model.render(camera)
        
        # Compute photometric loss (L1 + SSIM)
        loss_l1 = torch.abs(rendered_image - gt_image).mean()
        loss_ssim = 1.0 - ssim(rendered_image, gt_image)
        loss = 0.8 * loss_l1 + 0.2 * loss_ssim
        
        # Backpropagation
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        
        # Adaptive density control every 100 iterations
        if iteration % 100 == 0:
            model.densify_and_prune(
                min_opacity=0.05,
                max_screen_size=20
            )
        
        # Log progress
        if iteration % 100 == 0:
            print(f"Iteration {iteration}, Loss: {loss.item():.4f}")
    
    # Step 3: Save model
    model.save_ply(f"/tmp/{scene_id}_gaussians.ply")
    
    return model
```

### Photometric Loss Explained

**Photometric Loss** measures the difference between:
- **Rendered image**: What the model produces
- **Ground truth image**: Original video frame

```python
# L1 Loss: Pixel-wise absolute difference
loss_l1 = |rendered_pixel - gt_pixel|

# SSIM Loss: Structural similarity (perceptual quality)
loss_ssim = 1 - SSIM(rendered_image, gt_image)

# Combined loss
total_loss = 0.8 * loss_l1 + 0.2 * loss_ssim
```

This loss drives the optimization to make rendered views match the input video frames.

---

## Browser Rendering

### Step 1: Frontend Requests Scene

**Location**: `frontend/src/pages/ViewerPage.tsx`

```typescript
import { useParams } from 'react-router-dom';
import { GaussianViewer } from '../components/GaussianViewer';

export const ViewerPage = () => {
  const { sceneId } = useParams<{ sceneId: string }>();
  
  return (
    <div className="h-screen w-screen">
      <GaussianViewer sceneId={sceneId} />
    </div>
  );
};
```

### Step 2: Gaussian Viewer Component

**Location**: `frontend/src/components/GaussianViewer.tsx`

```typescript
import { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

export const GaussianViewer = ({ sceneId }: { sceneId: string }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [scene, setScene] = useState<THREE.Scene | null>(null);
  const [camera, setCamera] = useState<THREE.PerspectiveCamera | null>(null);
  const [renderer, setRenderer] = useState<THREE.WebGLRenderer | null>(null);
  
  // Initialize Three.js scene
  useEffect(() => {
    if (!canvasRef.current) return;
    
    // Create scene
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x000000);
    
    // Create camera
    const camera = new THREE.PerspectiveCamera(
      75,
      window.innerWidth / window.innerHeight,
      0.1,
      1000
    );
    camera.position.set(0, 2, 5);
    
    // Create renderer
    const renderer = new THREE.WebGLRenderer({
      canvas: canvasRef.current,
      antialias: true
    });
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    
    // Add orbit controls
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    
    setScene(scene);
    setCamera(camera);
    setRenderer(renderer);
    
    // Animation loop
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();
    
    return () => {
      renderer.dispose();
    };
  }, []);
  
  // Load scene tiles
  useEffect(() => {
    if (!scene || !camera) return;
    
    loadSceneTiles(sceneId, scene, camera);
  }, [sceneId, scene, camera]);
  
  return <canvas ref={canvasRef} />;
};
```

### Step 3: Progressive Tile Loading

```typescript
async function loadSceneTiles(
  sceneId: string, 
  scene: THREE.Scene, 
  camera: THREE.PerspectiveCamera
) {
  // Request visible tiles from backend
  const response = await fetch(`/api/v1/scenes/${sceneId}/tiles`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      camera_position: camera.position.toArray(),
      camera_direction: camera.getWorldDirection(new THREE.Vector3()).toArray(),
      fov: camera.fov,
      bandwidth: navigator.connection?.downlink || 10 // Mbps
    })
  });
  
  const { tiles } = await response.json();
  
  // Load tiles progressively by priority
  for (const tile of tiles) {
    const tileData = await loadTile(sceneId, tile.tile_id);
    const gaussianMesh = createGaussianMesh(tileData);
    scene.add(gaussianMesh);
  }
}

async function loadTile(sceneId: string, tileId: string): Promise<TileData> {
  const response = await fetch(
    `/api/v1/scenes/${sceneId}/tiles/${tileId}`
  );
  const arrayBuffer = await response.arrayBuffer();
  return parsePLY(arrayBuffer);
}
```

### Step 4: Gaussian Rendering with Custom Shader

```typescript
function createGaussianMesh(tileData: TileData): THREE.Mesh {
  // Create geometry from Gaussian data
  const geometry = new THREE.BufferGeometry();
  
  // Positions (x, y, z)
  geometry.setAttribute('position', 
    new THREE.Float32BufferAttribute(tileData.positions, 3));
  
  // Colors (r, g, b)
  geometry.setAttribute('color', 
    new THREE.Float32BufferAttribute(tileData.colors, 3));
  
  // Scales (sx, sy, sz)
  geometry.setAttribute('scale', 
    new THREE.Float32BufferAttribute(tileData.scales, 3));
  
  // Rotations (quaternion: x, y, z, w)
  geometry.setAttribute('rotation', 
    new THREE.Float32BufferAttribute(tileData.rotations, 4));
  
  // Opacity (alpha)
  geometry.setAttribute('opacity', 
    new THREE.Float32BufferAttribute(tileData.opacities, 1));
  
  // Custom shader material
  const material = new THREE.ShaderMaterial({
    vertexShader: gaussianVertexShader,
    fragmentShader: gaussianFragmentShader,
    transparent: true,
    depthWrite: false,
    blending: THREE.NormalBlending
  });
  
  return new THREE.Mesh(geometry, material);
}

// Vertex Shader (transforms Gaussians to screen space)
const gaussianVertexShader = `
  attribute vec3 scale;
  attribute vec4 rotation;
  attribute float opacity;
  
  varying vec3 vColor;
  varying float vOpacity;
  varying vec2 vUv;
  
  void main() {
    vColor = color;
    vOpacity = opacity;
    vUv = uv;
    
    // Transform Gaussian to screen space
    vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
    gl_Position = projectionMatrix * mvPosition;
    
    // Scale point size based on distance
    gl_PointSize = scale.x * (300.0 / -mvPosition.z);
  }
`;

// Fragment Shader (renders Gaussian splat)
const gaussianFragmentShader = `
  varying vec3 vColor;
  varying float vOpacity;
  varying vec2 vUv;
  
  void main() {
    // Gaussian falloff from center
    vec2 cxy = 2.0 * gl_PointCoord - 1.0;
    float r = dot(cxy, cxy);
    
    if (r > 1.0) discard; // Outside Gaussian radius
    
    // Gaussian weight
    float alpha = exp(-0.5 * r) * vOpacity;
    
    gl_FragColor = vec4(vColor, alpha);
  }
`;
```

---

## Use Cases

### Use Case 1: Construction Site Documentation

**Input**: Video walkthrough of construction site (drone or handheld)

**Pipeline**:
1. User uploads 5-minute 4K video
2. Backend extracts 900 frames (3 FPS)
3. COLMAP estimates camera poses for each frame
4. MiDaS generates depth maps
5. Gaussian Splatting creates 3D model
6. Model optimized and tiled
7. Frontend renders interactive 3D scene

**Output**: 
- Interactive 3D model viewable in browser
- Measurements and annotations
- Progress tracking over time
- PDF reports

### Use Case 2: Real Estate Virtual Tours

**Input**: Video tour of property interior

**Pipeline**:
1. Upload video of each room
2. Automatic frame extraction and filtering
3. Camera pose estimation
4. 3D reconstruction
5. Guided tour creation with narration

**Output**:
- Immersive 3D walkthrough
- Shareable links for clients
- Embedded viewer on website

### Use Case 3: Industrial Inspection

**Input**: Video of machinery or infrastructure

**Pipeline**:
1. Upload inspection video
2. 3D reconstruction
3. Defect annotation with photos
4. Measurement tools

**Output**:
- 3D model with defect markers
- Inspection reports
- Historical comparison

### Use Case 4: Architectural Visualization

**Input**: 3D CAD model (IFC, OBJ, FBX)

**Pipeline**:
1. Upload 3D file
2. Parse geometry and materials
3. Convert to Gaussian representation
4. Optimize and tile
5. Render with textures

**Output**:
- Interactive 3D visualization
- BIM metadata display
- Clash detection
- Quantity takeoffs

### Use Case 5: Photogrammetry from Photos

**Input**: Collection of photos from different angles

**Pipeline**:
1. Upload photo set (50-200 images)
2. COLMAP feature matching
3. Sparse reconstruction
4. Dense reconstruction
5. Gaussian Splatting for rendering

**Output**:
- High-quality 3D model
- Texture-mapped surfaces
- Measurements

---

## API Endpoints Summary

### Upload
```
POST /api/v1/scenes/upload
Body: multipart/form-data (video file)
Response: { scene_id, job_id, status }
```

### Status
```
GET /api/v1/scenes/{scene_id}
Response: { scene_id, status, progress, error }
```

### Tile Streaming
```
POST /api/v1/scenes/{scene_id}/tiles
Body: { camera_position, camera_direction, fov, bandwidth }
Response: { tiles: [{ tile_id, priority, lod }] }
```

### Download Tile
```
GET /api/v1/scenes/{scene_id}/tiles/{tile_id}
Response: Binary PLY data
```

---

## Performance Optimization

### Frontend
- Progressive tile loading (load closest tiles first)
- LOD selection based on distance
- Frustum culling (only load visible tiles)
- Bandwidth adaptation
- WebGL2/WebGPU rendering

### Backend
- GPU acceleration for COLMAP and Gaussian Splatting
- Celery task queue for async processing
- MinIO for scalable object storage
- Valkey caching for frequently accessed tiles
- Octree spatial indexing

---

## Monitoring and Debugging

### Check Processing Status
```bash
# Get scene status
curl http://localhost:8000/api/v1/scenes/{scene_id}

# Check Celery worker logs
docker logs backend-worker-1

# Check MinIO storage
mc ls minio/scenes/{scene_id}/
```

### Common Issues

1. **COLMAP fails**: Not enough feature matches
   - Solution: Increase video quality, reduce motion blur

2. **Gaussian Splatting slow**: GPU not detected
   - Solution: Check CUDA installation, use GPU-enabled Docker image

3. **Tiles not loading**: CORS or network issue
   - Solution: Check CORS configuration in backend

4. **Poor rendering quality**: LOD too aggressive
   - Solution: Adjust LOD thresholds in tile streaming

---

## Next Steps

1. **Test the pipeline**: Upload a sample video
2. **Monitor processing**: Watch Celery logs
3. **View results**: Open scene in browser viewer
4. **Optimize**: Adjust parameters based on results

For detailed implementation, see:
- Backend: `backend/workers/video_pipeline.py`
- Frontend: `frontend/src/components/GaussianViewer.tsx`
- API: `backend/api/scenes.py`
