# Visual Pipeline Flow Diagrams

## Complete Data Flow

```
┌──────────────────────────────────────────────────────────────────────┐
│                           USER INTERACTION                            │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 1. Upload Video/3D File
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FRONTEND (React + TypeScript)                                        │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ UploadDialog.tsx                                                │  │
│  │ - File validation (type, size)                                  │  │
│  │ - FormData creation                                             │  │
│  │ - Progress tracking                                             │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    │ 2. POST /api/v1/scenes/upload    │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ sceneApi.ts (RTK Query)                                         │  │
│  │ - HTTP request with FormData                                    │  │
│  │ - Authentication headers                                        │  │
│  │ - Response handling                                             │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 3. HTTP Request
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  BACKEND API (FastAPI)                                                │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ scenes.py - upload_video()                                      │  │
│  │ - Validate user authentication                                  │  │
│  │ - Validate organization context                                 │  │
│  │ - Generate scene_id (UUID)                                      │  │
│  │ - Validate file type and size                                   │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    │ 4. Store file                    │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ MinIO Client                                                    │  │
│  │ Path: videos/{org_id}/{scene_id}/original.mp4                  │  │
│  │ - S3-compatible object storage                                  │  │
│  │ - Multipart upload for large files                              │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    │ 5. Create DB record              │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ MongoDB - scenes collection                                     │  │
│  │ {                                                                │  │
│  │   id: scene_id,                                                 │  │
│  │   organization_id: org_id,                                      │  │
│  │   status: "uploaded",                                           │  │
│  │   filename: "video.mp4",                                        │  │
│  │   created_at: timestamp                                         │  │
│  │ }                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    │ 6. Enqueue job                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ Celery Task Queue (Valkey broker)                               │  │
│  │ Task: process_video.delay(scene_id, org_id)                    │  │
│  │ - Async task execution                                          │  │
│  │ - Retry logic                                                   │  │
│  │ - Priority queue                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 7. Worker picks up task
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  CELERY WORKER (GPU-enabled)                                          │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 1: Frame Extraction (FFmpeg)                               │  │
│  │ - Extract frames at 3 FPS                                       │  │
│  │ - Save as JPEG to MinIO                                         │  │
│  │ - Path: frames/{scene_id}/frame_0001.jpg                       │  │
│  │ - Duration: ~30 seconds for 5-min video                         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 2: Frame Intelligence                                      │  │
│  │ - Blur Detection (Laplacian variance)                           │  │
│  │ - Motion Analysis (optical flow)                                │  │
│  │ - Coverage-based selection                                      │  │
│  │ - Filter out 30% of frames                                      │  │
│  │ - Duration: ~1 minute                                           │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 3: Camera Pose Estimation (COLMAP)                         │  │
│  │                                                                  │  │
│  │ 3a. Feature Extraction (SIFT)                                   │  │
│  │     - Detect keypoints in each frame                            │  │
│  │     - Extract 128-dim descriptors                               │  │
│  │     - GPU-accelerated                                           │  │
│  │                                                                  │  │
│  │ 3b. Feature Matching                                            │  │
│  │     - Match features between frame pairs                        │  │
│  │     - Geometric verification (RANSAC)                           │  │
│  │     - Build match graph                                         │  │
│  │                                                                  │  │
│  │ 3c. Sparse Reconstruction                                       │  │
│  │     - Incremental SfM                                           │  │
│  │     - Estimate camera intrinsics (fx, fy, cx, cy)              │  │
│  │     - Estimate camera extrinsics (R, t)                         │  │
│  │     - Triangulate 3D points                                     │  │
│  │                                                                  │  │
│  │ 3d. Bundle Adjustment                                           │  │
│  │     - Refine camera poses                                       │  │
│  │     - Refine 3D points                                          │  │
│  │     - Minimize reprojection error                               │  │
│  │                                                                  │  │
│  │ Output: cameras.bin, images.bin, points3D.bin                  │  │
│  │ Duration: ~5-10 minutes                                         │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 4: Depth Estimation (MiDaS)                                │  │
│  │ - Load MiDaS DPT-Large model                                    │  │
│  │ - Generate depth map for each frame                             │  │
│  │ - Normalize to 0-1 range                                        │  │
│  │ - Save as 16-bit PNG                                            │  │
│  │ - GPU-accelerated inference                                     │  │
│  │ - Duration: ~2 seconds per frame                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 5: 3D Reconstruction (Gaussian Splatting)                  │  │
│  │                                                                  │  │
│  │ 5a. Initialize Gaussians                                        │  │
│  │     - Load COLMAP sparse points                                 │  │
│  │     - Create Gaussian at each point                             │  │
│  │     - Initialize parameters:                                    │  │
│  │       * Position: from point cloud                              │  │
│  │       * Scale: from point density                               │  │
│  │       * Rotation: identity                                      │  │
│  │       * Color: from point color                                 │  │
│  │       * Opacity: 0.5                                            │  │
│  │                                                                  │  │
│  │ 5b. Training Loop (7000 iterations)                             │  │
│  │     For each iteration:                                         │  │
│  │       - Select random training view                             │  │
│  │       - Render from camera pose                                 │  │
│  │       - Compute photometric loss:                               │  │
│  │         loss = 0.8*L1 + 0.2*SSIM                               │  │
│  │       - Backpropagate gradients                                 │  │
│  │       - Update Gaussian parameters                              │  │
│  │       - Every 100 iters: densify & prune                        │  │
│  │                                                                  │  │
│  │ 5c. Save Model                                                  │  │
│  │     - Export to PLY format                                      │  │
│  │     - Upload to MinIO                                           │  │
│  │                                                                  │  │
│  │ Duration: ~30-60 minutes on RTX 3090                            │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 6: Scene Optimization                                      │  │
│  │ - Prune low-opacity Gaussians (α < 0.05)                       │  │
│  │ - Merge nearby Gaussians (distance < 0.01m)                    │  │
│  │ - Generate LOD levels (100%, 50%, 20%)                         │  │
│  │ - Vector quantization (8-bit)                                   │  │
│  │ - Target: 50% size reduction, PSNR > 30dB                      │  │
│  │ - Duration: ~5 minutes                                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ STEP 7: Scene Tiling (Octree)                                   │  │
│  │ - Build octree spatial structure                                │  │
│  │ - Max 100K Gaussians per tile                                   │  │
│  │ - Generate tile IDs: L{level}_X{x}_Y{y}_Z{z}_{lod}            │  │
│  │ - Save tiles to MinIO                                           │  │
│  │ - Store metadata in MongoDB                                     │  │
│  │ - Duration: ~5 minutes                                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                    │                                   │
│                                    │ 8. Update status                 │
│                                    ▼                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ MongoDB Update                                                  │  │
│  │ { status: "completed", progress: 100 }                         │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ 9. User opens viewer
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│  FRONTEND VIEWER                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │ ViewerPage.tsx → GaussianViewer.tsx                             │  │
│  │                                                                  │  │
│  │ 1. Initialize Three.js                                          │  │
│  │    - Create scene, camera, renderer                             │  │
│  │    - Add orbit controls                                         │  │
│  │    - Start animation loop                                       │  │
│  │                                                                  │  │
│  │ 2. Request visible tiles                                        │  │
│  │    POST /api/v1/scenes/{scene_id}/tiles                        │  │
│  │    Body: {                                                       │  │
│  │      camera_position: [x, y, z],                                │  │
│  │      camera_direction: [dx, dy, dz],                            │  │
│  │      fov: 75,                                                   │  │
│  │      bandwidth: 10                                              │  │
│  │    }                                                             │  │
│  │                                                                  │  │
│  │ 3. Backend performs:                                            │  │
│  │    - Frustum culling (filter visible tiles)                     │  │
│  │    - Distance-based prioritization                              │  │
│  │    - LOD selection (high/med/low)                               │  │
│  │    - Bandwidth adaptation                                       │  │
│  │                                                                  │  │
│  │ 4. Load tiles progressively                                     │  │
│  │    For each tile:                                               │  │
│  │      - Download PLY from MinIO                                  │  │
│  │      - Parse Gaussian data                                      │  │
│  │      - Create Three.js geometry                                 │  │
│  │      - Apply custom shader                                      │  │
│  │      - Add to scene                                             │  │
│  │                                                                  │  │
│  │ 5. Render loop                                                  │  │
│  │    - Update camera on user interaction                          │  │
│  │    - Request new tiles if camera moved                          │  │
│  │    - Render Gaussians with custom shader                        │  │
│  │    - Target: 30-60 FPS                                          │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

## COLMAP Detailed Flow

```
Input: Video Frames
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Feature Extraction (SIFT)                                    │
│                                                               │
│ For each frame:                                              │
│   1. Convert to grayscale                                    │
│   2. Build scale-space pyramid                               │
│   3. Detect keypoints (DoG)                                  │
│   4. Extract 128-dim descriptors                             │
│                                                               │
│ Output: database.db with features                            │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Feature Matching                                             │
│                                                               │
│ For each frame pair:                                         │
│   1. Match descriptors (nearest neighbor)                    │
│   2. Geometric verification (RANSAC)                         │
│   3. Estimate fundamental matrix                             │
│   4. Store verified matches                                  │
│                                                               │
│ Output: Match graph in database.db                           │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Incremental Reconstruction                                   │
│                                                               │
│ 1. Initialize with best image pair                          │
│ 2. For each new image:                                       │
│      a. Estimate pose (PnP + RANSAC)                        │
│      b. Triangulate new 3D points                           │
│      c. Bundle adjustment (local)                           │
│ 3. Global bundle adjustment                                  │
│                                                               │
│ Output: Sparse 3D model                                      │
│   - cameras.bin (intrinsics)                                 │
│   - images.bin (extrinsics)                                  │
│   - points3D.bin (3D points)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Gaussian Splatting Training Loop

```
Initialize Gaussians from COLMAP points
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Training Iteration                                           │
│                                                               │
│ 1. Select random training view                               │
│    camera = random_choice(cameras)                           │
│                                                               │
│ 2. Render from camera                                        │
│    rendered = rasterize_gaussians(                           │
│        gaussians,                                            │
│        camera.R,  # rotation                                 │
│        camera.t,  # translation                              │
│        camera.fx, # focal length                             │
│        camera.fy                                             │
│    )                                                          │
│                                                               │
│ 3. Load ground truth image                                   │
│    gt_image = load_frame(camera.image_id)                   │
│                                                               │
│ 4. Compute loss                                              │
│    loss_l1 = |rendered - gt_image|                          │
│    loss_ssim = 1 - SSIM(rendered, gt_image)                 │
│    loss = 0.8 * loss_l1 + 0.2 * loss_ssim                  │
│                                                               │
│ 5. Backpropagation                                           │
│    loss.backward()                                           │
│    optimizer.step()                                          │
│                                                               │
│ 6. Adaptive density control (every 100 iters)                │
│    - Densify: Split large Gaussians                          │
│    - Prune: Remove low-opacity Gaussians                     │
│                                                               │
│ Repeat for 7000 iterations                                   │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
Output: Trained Gaussian Model (PLY)
```

## Browser Rendering Pipeline

```
User opens viewer
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Initialize Three.js Scene                                    │
│ - Create WebGL context                                       │
│ - Set up camera (PerspectiveCamera)                         │
│ - Add orbit controls                                         │
│ - Start render loop                                          │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Request Visible Tiles                                        │
│                                                               │
│ POST /api/v1/scenes/{id}/tiles                              │
│ {                                                             │
│   camera_position: [0, 2, 5],                               │
│   camera_direction: [0, 0, -1],                             │
│   fov: 75,                                                   │
│   bandwidth: 10                                              │
│ }                                                             │
│                                                               │
│ Backend Response:                                            │
│ {                                                             │
│   tiles: [                                                   │
│     { tile_id: "L0_X0_Y0_Z0_high", priority: 1 },          │
│     { tile_id: "L0_X1_Y0_Z0_med", priority: 2 },           │
│     ...                                                      │
│   ]                                                           │
│ }                                                             │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Load Tiles Progressively                                     │
│                                                               │
│ For each tile (by priority):                                 │
│   1. Download PLY file                                       │
│      GET /api/v1/scenes/{id}/tiles/{tile_id}                │
│                                                               │
│   2. Parse PLY data                                          │
│      - Extract positions (x, y, z)                           │
│      - Extract colors (r, g, b)                              │
│      - Extract scales (sx, sy, sz)                           │
│      - Extract rotations (qx, qy, qz, qw)                   │
│      - Extract opacities (α)                                 │
│                                                               │
│   3. Create Three.js geometry                                │
│      geometry = new BufferGeometry()                         │
│      geometry.setAttribute('position', positions)            │
│      geometry.setAttribute('color', colors)                  │
│      geometry.setAttribute('scale', scales)                  │
│      geometry.setAttribute('rotation', rotations)            │
│      geometry.setAttribute('opacity', opacities)             │
│                                                               │
│   4. Create custom shader material                           │
│      material = new ShaderMaterial({                         │
│        vertexShader: gaussianVS,                            │
│        fragmentShader: gaussianFS                           │
│      })                                                       │
│                                                               │
│   5. Add to scene                                            │
│      mesh = new Mesh(geometry, material)                    │
│      scene.add(mesh)                                         │
└─────────────────────────────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│ Render Loop (60 FPS)                                         │
│                                                               │
│ function animate() {                                         │
│   requestAnimationFrame(animate);                           │
│                                                               │
│   // Update controls                                         │
│   controls.update();                                         │
│                                                               │
│   // Check if camera moved significantly                     │
│   if (cameraMoved()) {                                       │
│     requestNewTiles();                                       │
│   }                                                           │
│                                                               │
│   // Render scene                                            │
│   renderer.render(scene, camera);                           │
│ }                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Data Structures

### Scene Model (MongoDB)
```javascript
{
  _id: ObjectId("..."),
  id: "uuid-v4",
  organization_id: "org-123",
  user_id: "user-456",
  filename: "construction_site.mp4",
  status: "completed",  // uploaded, processing, completed, failed
  progress: 100,
  file_size: 524288000,  // bytes
  created_at: ISODate("2024-03-24T10:00:00Z"),
  updated_at: ISODate("2024-03-24T11:30:00Z"),
  metadata: {
    duration: 300,  // seconds
    frame_count: 900,
    camera_count: 630,
    gaussian_count: 5000000,
    tile_count: 50
  }
}
```

### Tile Model (MongoDB)
```javascript
{
  _id: ObjectId("..."),
  scene_id: "uuid-v4",
  tile_id: "L0_X0_Y0_Z0_high",
  level: 0,
  x: 0,
  y: 0,
  z: 0,
  lod: "high",
  bounding_box: {
    min: [-10, -10, -10],
    max: [10, 10, 10]
  },
  gaussian_count: 95000,
  file_path: "scenes/uuid/tiles/0/0_0_0_high.ply",
  file_size: 15728640  // bytes
}
```

### Gaussian Data (PLY Format)
```
ply
format binary_little_endian 1.0
element vertex 95000
property float x
property float y
property float z
property float scale_0
property float scale_1
property float scale_2
property float rot_0
property float rot_1
property float rot_2
property float rot_3
property float opacity
property float f_dc_0  // SH color coefficients
property float f_dc_1
property float f_dc_2
end_header
[binary data...]
```
