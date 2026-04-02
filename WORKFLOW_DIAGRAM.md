# 🔄 Platform Workflow Diagram

## Complete User Journey

```
┌─────────────────────────────────────────────────────────────────────┐
│                         LOGIN / SIGNUP                               │
│                    http://localhost:5173                             │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         DASHBOARD                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐             │
│  │ Total Scenes │  │  Processing  │  │  Completed   │             │
│  │      12      │  │      3       │  │      9       │             │
│  └──────────────┘  └──────────────┘  └──────────────┘             │
│                                                                      │
│  [New Scene Button] ← Click here to start                           │
│                                                                      │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐                      │
│  │ Scene1 │ │ Scene2 │ │ Scene3 │ │ Scene4 │  ← Scene Grid        │
│  └────────┘ └────────┘ └────────┘ └────────┘                      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Choose Upload │
                    │     Method     │
                    └────────┬───────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────────┐
│ VIDEO UPLOAD  │   │ 3D FILE IMPORT │   │ PHOTO UPLOAD     │
│               │   │                │   │                  │
│ • MP4, MOV    │   │ • GLB, GLTF    │   │ • Multiple JPGs  │
│ • AVI, WebM   │   │ • OBJ, FBX     │   │ • 20-100 photos  │
│ • MKV         │   │ • PLY, STL     │   │ • Photogrammetry │
│ • Max 5GB     │   │ • USD, DAE     │   │ • COLMAP         │
└───────┬───────┘   └────────┬───────┘   └────────┬─────────┘
        │                    │                    │
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCESSING PIPELINE                               │
│                                                                      │
│  Video Upload:                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │  Frame   │→ │  COLMAP  │→ │  Depth   │→ │ Gaussian │          │
│  │Extraction│  │  Poses   │  │Estimation│  │ Splatting│          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│   2-5 min       5-15 min      3-10 min      10-30 min              │
│                                                                      │
│  3D File Import:                                                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                         │
│  │  Parse   │→ │ Optimize │→ │  Create  │                         │
│  │   File   │  │ Geometry │  │  Tiles   │                         │
│  └──────────┘  └──────────┘  └──────────┘                         │
│   1-2 min       2-5 min       1-3 min                               │
│                                                                      │
│  Photo Upload:                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ Feature  │→ │Structure │→ │  Dense   │→ │ Gaussian │          │
│  │Detection │  │from Motion│  │  Recon   │  │ Splatting│          │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘          │
│   5-10 min      10-20 min     15-30 min     10-20 min              │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │ Scene Complete │
                    │  Status: ✅    │
                    └────────┬───────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        3D VIEWER                                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                                                             │   │
│  │                    [3D MODEL DISPLAY]                       │   │
│  │                                                             │   │
│  │         ┌─────────────────────────────────┐                │   │
│  │         │  Interactive 3D Scene           │                │   │
│  │         │  • Rotate, Pan, Zoom            │                │   │
│  │         │  • Real-time rendering          │                │   │
│  │         │  • 60 FPS performance           │                │   │
│  │         └─────────────────────────────────┘                │   │
│  │                                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  Left Toolbar:              Right Toolbar:                          │
│  ┌──────────────┐          ┌──────────────┐                        │
│  │ 🔄 Reset     │          │ 👁️ View Mode │                        │
│  │ 📐 Fit View  │          │ ✏️ Create    │                        │
│  │ 📷 Presets   │          │ ✂️ Edit      │                        │
│  │ ⚙️ Settings  │          │ 🗑️ Delete    │                        │
│  └──────────────┘          └──────────────┘                        │
│                                                                      │
│  Bottom Toolbar:                                                     │
│  ┌──────────────────────────────────────────────────────────┐      │
│  │ 📍 Point │ 📏 Distance │ 📐 Area │ ⛰️ Slope │ 📦 Volume │      │
│  └──────────────────────────────────────────────────────────┘      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌────────────────┐   ┌──────────────────┐
│ MEASUREMENTS  │   │ COLLABORATION  │   │    SHARING       │
│               │   │                │   │                  │
│ • Distance    │   │ • Live cursors │   │ • Public link    │
│ • Area        │   │ • User presence│   │ • Password       │
│ • Slope       │   │ • Real-time    │   │ • Embed code     │
│ • Volume      │   │ • Chat         │   │ • Organization   │
│ • Angle       │   │ • Follow mode  │   │ • PDF report     │
└───────────────┘   └────────────────┘   └──────────────────┘
```

---

## Detailed Feature Flow

### 1. Video to Gaussian Splat

```
User Action                    System Process                  Result
───────────                    ──────────────                  ──────

1. Click "New Scene"    →     Open upload dialog       →     Dialog appears
2. Drag video file      →     Validate format/size     →     File accepted
3. Click "Upload"       →     Upload to MinIO          →     Progress bar
4. Wait...              →     Extract frames (FFmpeg)  →     Status: "Extracting"
5. Wait...              →     COLMAP processing        →     Status: "Analyzing"
6. Wait...              →     Depth estimation (GPU)   →     Status: "Depth"
7. Wait...              →     Gaussian Splatting       →     Status: "Rendering"
8. Wait...              →     Create tiles & optimize  →     Status: "Finalizing"
9. Scene ready!         →     Generate thumbnail       →     Status: "Completed" ✅
10. Click scene card    →     Load viewer              →     3D scene displays
```

### 2. 3D File Import

```
User Action                    System Process                  Result
───────────                    ──────────────                  ──────

1. Click "Import 3D"    →     Show format list         →     Dialog with formats
2. Select GLB file      →     Validate file            →     File accepted
3. Enter scene name     →     Store metadata           →     Name saved
4. Click "Import"       →     Upload to server         →     Progress bar
5. Wait...              →     Parse GLB structure      →     Status: "Parsing"
6. Wait...              →     Extract meshes/textures  →     Status: "Processing"
7. Wait...              →     Optimize geometry        →     Status: "Optimizing"
8. Wait...              →     Create streaming tiles   →     Status: "Tiling"
9. Scene ready!         →     Generate thumbnail       →     Status: "Completed" ✅
10. Click scene card    →     Load viewer              →     GLB model displays
```

### 3. Measurements

```
User Action                    System Process                  Result
───────────                    ──────────────                  ──────

Distance Measurement:
1. Click "Distance" tool →    Enable click mode        →     Cursor changes
2. Click point A        →     Store 3D coordinates     →     Point marker appears
3. Click point B        →     Calculate distance       →     Line + label appears
4. View result          →     Display: "5.2m"          →     Measurement saved

Slope Measurement:
1. Click "Slope" tool   →     Enable click mode        →     Cursor changes
2. Click bottom point   →     Store coordinates        →     Point marker
3. Click top point      →     Calculate slope          →     Result displays
4. View result          →     "15.5% (8.8°)"           →     Shows percentage & degrees
                              "Horizontal: 10.5m"
                              "Vertical: 1.6m"

Volume Measurement:
1. Click "Volume" tool  →     Enable polygon mode      →     Cursor changes
2. Click 4+ points      →     Store boundary points    →     Polygon outline
3. Double-click finish  →     Calculate bounding box   →     Volume displays
4. View result          →     "125.50 m³"              →     Shows dimensions
                              "Width: 5.2m"
                              "Depth: 6.1m"
                              "Height: 4.0m"
```

### 4. Collaboration

```
User Action                    System Process                  Result
───────────                    ──────────────                  ──────

1. Open scene           →     Connect WebSocket        →     Connected
2. Share link           →     Generate share URL       →     Link copied
3. User 2 joins         →     Broadcast join event     →     User appears in panel
4. User 1 moves camera  →     Send cursor position     →     User 2 sees cursor
5. User 1 creates point →     Broadcast annotation     →     User 2 sees point
6. User 2 adds comment  →     Sync via WebSocket       →     User 1 sees comment
7. User 1 follows User 2→     Sync camera positions    →     Cameras linked
```

### 5. Sharing & Embedding

```
User Action                    System Process                  Result
───────────                    ──────────────                  ──────

Public Share:
1. Click "Share"        →     Open share dialog        →     Dialog appears
2. Toggle "Public"      →     Generate public link     →     Link created
3. Copy link            →     Store in clipboard       →     Link copied
4. Send to client       →     Client opens link        →     View-only access

Password Protected:
1. Click "Protected"    →     Show password form       →     Form appears
2. Enter password       →     Hash with SHA-256        →     Secure hash
3. Set expiration       →     Store expiry date        →     Date saved
4. Generate link        →     Create share record      →     Link + password
5. Client accesses      →     Prompt for password      →     Password required
6. Enter password       →     Verify hash              →     Access granted

Embed:
1. Click "Embed"        →     Show embed options       →     Options panel
2. Set dimensions       →     Update iframe code       →     Code updates
3. Toggle features      →     Add query params         →     URL updated
4. Copy code            →     Copy to clipboard        →     Code copied
5. Paste in website     →     Iframe loads viewer      →     Embedded viewer
```

---

## File Format Support Matrix

```
┌─────────────────────────────────────────────────────────────────────┐
│                    SUPPORTED FILE FORMATS                            │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  VIDEO FORMATS (for Gaussian Splatting):                            │
│  ┌──────────┬──────────────┬─────────────┬──────────────┐          │
│  │ Format   │  Extension   │  Max Size   │  Recommended │          │
│  ├──────────┼──────────────┼─────────────┼──────────────┤          │
│  │ MP4      │  .mp4        │  5GB        │  ✅ Best     │          │
│  │ MOV      │  .mov        │  5GB        │  ✅ Good     │          │
│  │ AVI      │  .avi        │  5GB        │  ⚠️ Large    │          │
│  │ WebM     │  .webm       │  5GB        │  ✅ Good     │          │
│  │ MKV      │  .mkv        │  5GB        │  ✅ Good     │          │
│  └──────────┴──────────────┴─────────────┴──────────────┘          │
│                                                                      │
│  3D MODEL FORMATS:                                                   │
│  ┌──────────┬──────────────┬─────────────┬──────────────┐          │
│  │ Format   │  Extension   │  Max Size   │  Use Case    │          │
│  ├──────────┼──────────────┼─────────────┼──────────────┤          │
│  │ GLB      │  .glb        │  500MB      │  ✅ Best     │          │
│  │ GLTF     │  .gltf       │  500MB      │  ✅ Best     │          │
│  │ OBJ      │  .obj        │  500MB      │  ✅ Common   │          │
│  │ FBX      │  .fbx        │  500MB      │  ✅ Animation│          │
│  │ PLY      │  .ply        │  1GB        │  ✅ Scans    │          │
│  │ STL      │  .stl        │  500MB      │  ✅ 3D Print │          │
│  │ USD      │  .usd/.usda  │  500MB      │  ✅ Advanced │          │
│  │ DAE      │  .dae        │  500MB      │  ⚠️ Legacy   │          │
│  │ 3DS      │  .3ds        │  500MB      │  ⚠️ Legacy   │          │
│  └──────────┴──────────────┴─────────────┴──────────────┘          │
│                                                                      │
│  POINT CLOUD FORMATS:                                                │
│  ┌──────────┬──────────────┬─────────────┬──────────────┐          │
│  │ Format   │  Extension   │  Max Size   │  Use Case    │          │
│  ├──────────┼──────────────┼─────────────┼──────────────┤          │
│  │ PLY      │  .ply        │  2GB        │  ✅ Best     │          │
│  │ LAS      │  .las        │  2GB        │  ✅ LiDAR    │          │
│  │ LAZ      │  .laz        │  2GB        │  ✅ Compress │          │
│  │ XYZ      │  .xyz        │  1GB        │  ✅ Simple   │          │
│  │ PCD      │  .pcd        │  1GB        │  ✅ PCL      │          │
│  │ PTS      │  .pts        │  1GB        │  ✅ Color    │          │
│  └──────────┴──────────────┴─────────────┴──────────────┘          │
│                                                                      │
│  GAUSSIAN SPLAT FORMATS:                                             │
│  ┌──────────┬──────────────┬─────────────┬──────────────┐          │
│  │ Format   │  Extension   │  Max Size   │  Use Case    │          │
│  ├──────────┼──────────────┼─────────────┼──────────────┤          │
│  │ SPLAT    │  .splat      │  1GB        │  ✅ Native   │          │
│  │ PLY      │  .ply        │  1GB        │  ✅ Gaussian │          │
│  └──────────┴──────────────┴─────────────┴──────────────┘          │
│                                                                      │
│  BIM FORMATS:                                                        │
│  ┌──────────┬──────────────┬─────────────┬──────────────┐          │
│  │ Format   │  Extension   │  Max Size   │  Use Case    │          │
│  ├──────────┼──────────────┼─────────────┼──────────────┤          │
│  │ IFC      │  .ifc        │  500MB      │  ✅ BIM      │          │
│  │ RVT      │  .rvt        │  500MB      │  ⚠️ Convert  │          │
│  └──────────┴──────────────┴─────────────┴──────────────┘          │
│                                                                      │
│  CAD OVERLAY FORMATS:                                                │
│  ┌──────────┬──────────────┬─────────────┬──────────────┐          │
│  │ Format   │  Extension   │  Max Size   │  Use Case    │          │
│  ├──────────┼──────────────┼─────────────┼──────────────┤          │
│  │ DXF      │  .dxf        │  100MB      │  ✅ CAD      │          │
│  │ DWG      │  .dwg        │  100MB      │  ⚠️ Convert  │          │
│  └──────────┴──────────────┴─────────────┴──────────────┘          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Performance Benchmarks

```
┌─────────────────────────────────────────────────────────────────────┐
│                    PROCESSING TIMES                                  │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Video to Gaussian Splat (1080p, 60 seconds):                       │
│  ┌────────────────────────┬──────────┬──────────┬──────────┐       │
│  │ Stage                  │ CPU Time │ GPU Time │ Total    │       │
│  ├────────────────────────┼──────────┼──────────┼──────────┤       │
│  │ Frame Extraction       │ 3 min    │ -        │ 3 min    │       │
│  │ COLMAP (Poses)         │ 10 min   │ -        │ 10 min   │       │
│  │ Depth Estimation       │ -        │ 5 min    │ 5 min    │       │
│  │ Gaussian Splatting     │ -        │ 15 min   │ 15 min   │       │
│  │ Post-Processing        │ 3 min    │ -        │ 3 min    │       │
│  ├────────────────────────┼──────────┼──────────┼──────────┤       │
│  │ TOTAL                  │ 16 min   │ 20 min   │ 36 min   │       │
│  └────────────────────────┴──────────┴──────────┴──────────┘       │
│                                                                      │
│  3D File Import (GLB, 50MB):                                         │
│  ┌────────────────────────┬──────────────────────────────┐         │
│  │ Stage                  │ Time                         │         │
│  ├────────────────────────┼──────────────────────────────┤         │
│  │ Upload                 │ 30 sec (depends on network)  │         │
│  │ Parse & Validate       │ 1 min                        │         │
│  │ Optimize Geometry      │ 2 min                        │         │
│  │ Create Tiles           │ 2 min                        │         │
│  ├────────────────────────┼──────────────────────────────┤         │
│  │ TOTAL                  │ ~5-6 min                     │         │
│  └────────────────────────┴──────────────────────────────┘         │
│                                                                      │
│  Photo Reconstruction (50 photos, 12MP):                             │
│  ┌────────────────────────┬──────────┬──────────┬──────────┐       │
│  │ Stage                  │ CPU Time │ GPU Time │ Total    │       │
│  ├────────────────────────┼──────────┼──────────┼──────────┤       │
│  │ Feature Detection      │ 8 min    │ -        │ 8 min    │       │
│  │ Structure from Motion  │ 15 min   │ -        │ 15 min   │       │
│  │ Dense Reconstruction   │ -        │ 20 min   │ 20 min   │       │
│  │ Gaussian Splatting     │ -        │ 12 min   │ 12 min   │       │
│  ├────────────────────────┼──────────┼──────────┼──────────┤       │
│  │ TOTAL                  │ 23 min   │ 32 min   │ 55 min   │       │
│  └────────────────────────┴──────────┴──────────┴──────────┘       │
└─────────────────────────────────────────────────────────────────────┘
```

---

**Last Updated:** April 2, 2026  
**Version:** 1.0.0
