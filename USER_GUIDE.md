# 🎯 Complete User Guide - Spatial AI Platform

## Table of Contents
1. [Getting Started](#getting-started)
2. [Video Upload & Gaussian Splatting](#video-upload--gaussian-splatting)
3. [3D File Import (GLB, USD, FBX, etc.)](#3d-file-import)
4. [Multiple Photo Upload](#multiple-photo-upload)
5. [Viewing 3D Models in Browser](#viewing-3d-models-in-browser)
6. [Measurements & Annotations](#measurements--annotations)
7. [Collaboration Features](#collaboration-features)
8. [Sharing & Embedding](#sharing--embedding)
9. [Advanced Features](#advanced-features)

---

## Getting Started

### 1. Access the Platform
1. Open your browser and navigate to: `http://localhost:5173` (or your deployed URL)
2. Login with your credentials
3. You'll land on the **Dashboard** page

### 2. Dashboard Overview
The dashboard shows:
- **Total Scenes**: All your 3D scenes
- **Processing**: Scenes currently being processed
- **Completed**: Ready-to-view scenes
- **Scene Grid**: Visual cards for each scene
- **New Scene Button**: Upload new content (top right)

---

## Video Upload & Gaussian Splatting

### How It Works
The platform converts regular phone videos into interactive 3D Gaussian Splat scenes using AI.

### Step-by-Step Process

#### 1. Upload Video
1. Click **"New Scene"** button on dashboard
2. Choose **"Upload Video"** option
3. **Drag & drop** your video file OR click **"Choose File"**

**Supported Formats:**
- MP4 (recommended)
- MOV (iPhone videos)
- AVI
- WebM
- MKV

**File Size Limit:** 5GB

#### 2. Video Requirements
For best results, record your video with:
- **Slow, steady movements** around the object/scene
- **Good lighting** (avoid shadows)
- **Overlap**: 60-70% overlap between frames
- **Duration**: 30 seconds to 5 minutes
- **Resolution**: 1080p or higher

#### 3. Upload Progress
You'll see:
- **Upload percentage** (0-100%)
- **Upload speed** (MB/s)
- **Estimated time remaining**
- **Cancel button** (if needed)

#### 4. Processing Pipeline
After upload, the system automatically:

**Stage 1: Frame Extraction** (2-5 minutes)
- Extracts frames from video using FFmpeg
- Selects best frames for reconstruction

**Stage 2: Camera Pose Estimation** (5-15 minutes)
- Uses COLMAP to calculate camera positions
- Builds sparse 3D point cloud

**Stage 3: Depth Estimation** (3-10 minutes)
- Uses MiDaS AI model to estimate depth
- Runs on GPU (RTX 4090)

**Stage 4: 3D Reconstruction** (10-30 minutes)
- Gaussian Splatting algorithm creates 3D scene
- Generates high-quality splat file

**Stage 5: Post-Processing** (2-5 minutes)
- Creates tiles for streaming
- Generates thumbnail
- Optimizes for web viewing

**Total Time:** 20-60 minutes (depending on video length)

#### 5. View Your Scene
1. Scene status changes from "Processing" → "Completed"
2. Click on the scene card
3. Interactive 3D viewer opens!

---

## 3D File Import

### Supported Formats

#### Point Clouds ☁️
- `.ply` - Polygon File Format (most common)
- `.las` / `.laz` - LiDAR data
- `.xyz` - ASCII point cloud
- `.pcd` - Point Cloud Data
- `.pts` - Point cloud with colors

#### Meshes 🔷
- `.glb` / `.gltf` - GL Transmission Format (recommended)
- `.obj` - Wavefront OBJ
- `.fbx` - Autodesk FBX
- `.stl` - Stereolithography
- `.dae` - COLLADA
- `.3ds` - 3D Studio

#### Gaussian Splats ✨
- `.splat` - Gaussian Splatting format
- `.ply` - Gaussian PLY format

#### BIM Models 🏢
- `.ifc` - Industry Foundation Classes
- `.rvt` - Revit (requires conversion)

### How to Import

#### 1. Open Import Dialog
1. Click **"New Scene"** button
2. Select **"Import 3D File"**

#### 2. Choose Your File
1. Click **"Select File"** or drag & drop
2. System automatically detects format
3. Enter a **Scene Name** (optional - auto-fills from filename)

#### 3. File Validation
The system checks:
- ✅ Format is supported
- ✅ File size under limit (default: 500MB)
- ✅ File is not corrupted

#### 4. Import Process
1. File uploads to server
2. System processes the file:
   - **Point clouds**: Converts to streamable format
   - **Meshes**: Optimizes geometry, compresses textures
   - **BIM**: Extracts geometry and metadata
3. Creates tiles for efficient streaming
4. Generates thumbnail

#### 5. View Imported Model
- Scene appears in dashboard when complete
- Click to open in 3D viewer
- All features available (measurements, annotations, etc.)

---

## Multiple Photo Upload

### Photogrammetry from Photos
Convert multiple photos into a 3D model using photogrammetry.

### Step-by-Step

#### 1. Prepare Your Photos
**Requirements:**
- **Minimum**: 20 photos
- **Recommended**: 50-100 photos
- **Overlap**: 60-80% between consecutive photos
- **Resolution**: 12MP or higher
- **Format**: JPG, PNG

**Photography Tips:**
- Walk around the object in a circle
- Take photos every 10-15 degrees
- Include multiple heights (low, medium, high)
- Consistent lighting
- Avoid motion blur

#### 2. Upload Photos
1. Click **"New Scene"** → **"Upload Photos"**
2. Select multiple files (Ctrl+Click or Cmd+Click)
3. Or drag & drop entire folder
4. System validates all photos

#### 3. Processing
The platform uses **COLMAP + Gaussian Splatting**:

**Step 1: Feature Detection** (5-10 min)
- Finds matching points between photos

**Step 2: Structure from Motion** (10-20 min)
- Calculates camera positions
- Creates sparse point cloud

**Step 3: Dense Reconstruction** (15-30 min)
- Builds dense 3D model
- Uses GPU acceleration

**Step 4: Gaussian Splatting** (10-20 min)
- Converts to Gaussian Splat format
- Optimizes for real-time viewing

**Total Time:** 40-80 minutes

#### 4. View Result
- Scene appears as "Completed"
- Click to view in 3D
- Fully interactive with all features

---

## Viewing 3D Models in Browser

### The 3D Viewer

#### Opening a Scene
1. Click any scene card on dashboard
2. Viewer loads automatically
3. No plugins or downloads needed!

### Viewer Interface

#### Top Toolbar
- **Share Button** (top right): Share scene with others
- **FPS Counter**: Shows rendering performance
- **Rendering Mode**: Client-side or server-side

#### Left Toolbar - Camera Controls
- **Reset Camera** 🔄: Return to default view
- **Fit to View** 📐: Frame entire model
- **Preset Views**:
  - Top view (bird's eye)
  - Front view
  - Side view
  - Isometric view

#### Right Toolbar - Annotations
- **View Mode** 👁️: Navigate and inspect
- **Create Mode** ✏️: Add measurements/annotations
- **Edit Mode** ✂️: Modify existing annotations
- **Delete** 🗑️: Remove annotations

### Navigation Controls

#### Mouse Controls
- **Left Click + Drag**: Rotate camera around model
- **Right Click + Drag**: Pan camera (move left/right/up/down)
- **Scroll Wheel**: Zoom in/out
- **Double Click**: Focus on point

#### Keyboard Shortcuts
- **W/A/S/D**: Move camera
- **Q/E**: Move up/down
- **Shift**: Move faster
- **Ctrl**: Move slower
- **Space**: Reset camera
- **F**: Fit to view

#### Touch Controls (Mobile/Tablet)
- **One Finger**: Rotate
- **Two Fingers**: Pan
- **Pinch**: Zoom
- **Double Tap**: Focus

### Model Types & Rendering

#### Gaussian Splats (.splat)
- **Best for**: Photorealistic scenes from videos/photos
- **Rendering**: Real-time, 60 FPS
- **Features**: Realistic lighting, reflections
- **File Size**: Smaller than meshes

#### GLB/GLTF Models
- **Best for**: CAD models, game assets
- **Rendering**: PBR (Physically Based Rendering)
- **Features**: Textures, materials, animations
- **Supports**: Embedded textures

#### OBJ Models
- **Best for**: Simple meshes
- **Rendering**: Basic shading
- **Features**: MTL material files
- **Supports**: Texture maps

#### PLY Point Clouds
- **Best for**: LiDAR scans, raw data
- **Rendering**: Point-based
- **Features**: Color per point
- **Supports**: Normals, intensity

#### FBX Models
- **Best for**: Animation, rigged characters
- **Rendering**: Full PBR
- **Features**: Bones, animations, materials
- **Supports**: Multiple objects

### Performance Tips

#### For Large Models
1. Enable **Level of Detail (LOD)**: Automatic
2. Use **Frustum Culling**: Only render visible parts
3. Enable **Occlusion Culling**: Skip hidden objects
4. Reduce **Point Size** for point clouds

#### For Slow Computers
1. Switch to **Server Rendering** mode
2. Reduce **Quality Settings**
3. Disable **Shadows**
4. Lower **Resolution**

---

## Measurements & Annotations

### Annotation Types

#### 1. Point Annotation 📍
**Use Case**: Mark specific locations

**How to Create:**
1. Click **Annotation Toolbar** → **Point**
2. Click once on the model
3. Add label and description
4. Click **Save**

**Example Uses:**
- Mark defects
- Label parts
- Identify features

#### 2. Distance Measurement 📏
**Use Case**: Measure straight-line distance

**How to Create:**
1. Select **Distance** tool
2. Click **start point**
3. Click **end point**
4. Distance displays automatically

**Shows:**
- Distance in meters
- 3D line between points
- Editable label

#### 3. Area Measurement 📐
**Use Case**: Calculate surface area

**How to Create:**
1. Select **Area** tool
2. Click to place **3+ points** (outline the area)
3. Double-click to finish
4. Area calculates automatically

**Shows:**
- Area in m²
- Polygon outline
- Perimeter length

#### 4. Slope Measurement ⛰️
**Use Case**: Measure incline/decline

**How to Create:**
1. Select **Slope** tool
2. Click **bottom point**
3. Click **top point**
4. Slope displays automatically

**Shows:**
- Slope percentage (e.g., 15.5%)
- Slope angle in degrees (e.g., 8.8°)
- Horizontal distance
- Vertical distance (elevation change)

**Example:**
```
Slope: 15.5% (8.8°)
Horizontal: 10.5m
Vertical: 1.6m
```

#### 5. Volume Calculation 📦
**Use Case**: Calculate volume of excavation, fill, etc.

**How to Create:**
1. Select **Volume** tool
2. Click **4+ points** to define bounds
3. Double-click to finish
4. Volume calculates automatically

**Shows:**
- Volume in m³
- Width, depth, height
- Bounding box visualization

**Example:**
```
Volume: 125.50 m³
Width: 5.2m
Depth: 6.1m
Height: 4.0m
```

#### 6. Angle Measurement 📐
**Use Case**: Measure angles between surfaces

**How to Create:**
1. Select **Angle** tool
2. Click **3 points** (vertex in middle)
3. Angle displays automatically

**Shows:**
- Angle in degrees
- Arc visualization

### Annotation Features

#### Colors
- Choose from **color picker**
- Default colors for each type
- Custom RGB values

#### Labels
- Add **custom text**
- Auto-generated IDs
- Searchable

#### Visibility
- **Show/Hide** individual annotations
- **Show/Hide** by type
- **Show/Hide** all

#### Export
- Export as **JSON**
- Export as **CSV**
- Include in **PDF reports**

---

## Collaboration Features

### Real-Time Collaboration

#### How It Works
Multiple users can view and work on the same scene simultaneously.

#### Features

##### 1. Live Cursors
- See **other users' cursors** in 3D space
- Each user has a **unique color**
- Shows **username** next to cursor

##### 2. User Presence
**Collaboration Panel** (right side) shows:
- **Active users** count
- **User names**
- **Connection status**
- **User colors**

##### 3. Real-Time Annotations
- See annotations **as they're created**
- Updates appear **instantly**
- No refresh needed

##### 4. Camera Sync (Optional)
- **Follow Mode**: Follow another user's camera
- See what they're looking at
- Great for presentations

#### Using Collaboration

##### 1. Share Scene
1. Click **Share** button
2. Copy **share link**
3. Send to collaborators
4. They open link → join automatically

##### 2. Collaboration Panel
- **Top right** of viewer
- Shows all active users
- Click user to follow their camera
- Click again to unfollow

##### 3. Chat (Coming Soon)
- Text chat with collaborators
- Voice chat option
- Screen sharing

---

## Sharing & Embedding

### Sharing Options

#### 1. Public Link
**Use Case**: Share with anyone

**How to:**
1. Click **Share** button
2. Toggle **"Public Access"** ON
3. Copy link
4. Anyone with link can view

**Features:**
- No login required
- View-only access
- Can't edit or delete

#### 2. Password-Protected Share
**Use Case**: Secure sharing with clients

**How to:**
1. Click **Share** → **"Password Protected"**
2. Set **password**
3. Set **expiration date** (1 day to 1 year)
4. Copy link
5. Share link + password separately

**Features:**
- SHA-256 encrypted password
- Auto-expires after date
- Track access attempts
- Revoke anytime

**Example:**
```
Link: https://yoursite.com/share/abc123
Password: SecurePass2024
Expires: April 30, 2026
```

#### 3. Organization Sharing
**Use Case**: Share within your team

**How to:**
1. Click **Share** → **"Organization"**
2. Select **team members**
3. Set **permissions**:
   - View only
   - View + Comment
   - View + Edit

#### 4. Embed in Website
**Use Case**: Display on your website

**How to:**
1. Click **Share** → **"Embed"**
2. Customize settings:
   - **Width/Height**: Responsive or fixed
   - **Controls**: Show/hide camera controls
   - **Annotations**: Show/hide annotations
   - **Measurements**: Enable/disable
   - **Auto-rotate**: Enable/disable
3. Copy **iframe code**
4. Paste into your website HTML

**Generated Code:**
```html
<iframe
  src="https://yoursite.com/embed/scenes/abc123?controls=true&annotations=true"
  width="100%"
  height="600px"
  frameborder="0"
  allowfullscreen
  title="3D Model Viewer"
></iframe>
```

**Embed Options:**
- `controls=true/false` - Camera controls
- `annotations=true/false` - Show annotations
- `measurements=true/false` - Measurement tools
- `autoRotate=true/false` - Auto-rotate model
- `theme=light/dark` - Color theme

---

## Advanced Features

### 1. DXF/CAD Overlay
**Use Case**: Compare as-built vs as-designed

**How to:**
1. Open scene in viewer
2. Click **"Overlays"** → **"Add DXF"**
3. Upload your **.dxf** file
4. Adjust:
   - **Opacity**: 0-100%
   - **Scale**: Match real-world size
   - **Position**: Align with model
   - **Rotation**: Rotate to match
5. Toggle **layers** on/off

**Supported DXF Entities:**
- Lines
- Polylines
- Circles
- Arcs
- Ellipses
- Text
- Splines
- 3D Faces

### 2. Photogrammetry Integration
**Use Case**: Import from professional software

**Supported Tools:**
- **RealityCapture** (.rcproj, .obj, .ply)
- **Agisoft Metashape** (.psx, .ply, .obj, .las)
- **Pix4D** (.p4d, .las, .ply, .obj)

**How to:**
1. Click **"Import"** → **"Photogrammetry Project"**
2. Select **software type**
3. Upload **project file**
4. System extracts:
   - 3D model
   - Camera positions
   - Textures
   - Metadata
5. Creates optimized scene

### 3. White-Label Branding
**Use Case**: Customize for your brand

**Admin Settings:**
1. Go to **Settings** → **"Branding"**
2. Upload **logo** (PNG, SVG)
3. Upload **favicon** (.ico)
4. Set **colors**:
   - Primary color
   - Secondary color
   - Accent color
5. Set **company info**:
   - Company name
   - Tagline
   - Contact info
6. **Custom CSS** (advanced)
7. **Custom domain** (e.g., 3d.yourcompany.com)

**Applies To:**
- Login page
- Dashboard
- Viewer
- Public shares
- Embed viewer
- PDF reports

### 4. Guided Tours
**Use Case**: Create walkthrough presentations

**How to:**
1. Open scene
2. Click **"Tours"** → **"Create Tour"**
3. Add **waypoints**:
   - Click to set camera position
   - Add description
   - Set duration
4. **Preview** tour
5. **Save** and **share**

**Tour Features:**
- Auto-play
- Pause/resume
- Skip waypoints
- Voice narration (optional)

### 5. Scene Comparison
**Use Case**: Compare before/after, progress tracking

**How to:**
1. Select **2 scenes**
2. Click **"Compare"**
3. Choose mode:
   - **Side-by-side**: Two viewers
   - **Slider**: Swipe between scenes
   - **Overlay**: Transparent overlay
4. Sync cameras (optional)

### 6. PDF Reports
**Use Case**: Generate inspection reports

**How to:**
1. Open scene
2. Click **"Export"** → **"PDF Report"**
3. Select content:
   - Scene overview
   - Annotations
   - Measurements
   - Screenshots
   - Custom notes
4. **Generate** PDF
5. **Download** or **email**

**Report Includes:**
- Cover page with branding
- Scene metadata
- All measurements
- Annotation list with images
- Custom sections

---

## Tips & Best Practices

### For Best Video-to-3D Results
1. **Lighting**: Shoot in bright, even lighting
2. **Movement**: Slow, steady, circular motion
3. **Overlap**: 60-70% overlap between frames
4. **Duration**: 1-3 minutes optimal
5. **Avoid**: Reflective surfaces, moving objects

### For Best Photo Reconstruction
1. **Quantity**: 50-100 photos minimum
2. **Coverage**: All angles, multiple heights
3. **Consistency**: Same lighting, same camera
4. **Focus**: Sharp, in-focus images
5. **Avoid**: Motion blur, lens flare

### For Large Models
1. Use **LOD** (Level of Detail)
2. Enable **streaming** mode
3. Use **tiles** for point clouds
4. Compress **textures**

### For Collaboration
1. Use **stable internet** connection
2. **Communicate** via chat
3. Use **Follow Mode** for presentations
4. **Save** work frequently

---

## Troubleshooting

### Upload Fails
- **Check file size** (under 5GB for videos)
- **Check format** (supported formats only)
- **Check internet** connection
- **Try again** after a few minutes

### Processing Stuck
- **Wait**: Large files take time (up to 60 min)
- **Check status**: Look for error messages
- **Contact support**: If stuck >2 hours

### Viewer Won't Load
- **Check browser**: Use Chrome, Firefox, or Edge
- **Enable WebGL**: Required for 3D rendering
- **Update drivers**: GPU drivers
- **Clear cache**: Browser cache

### Slow Performance
- **Reduce quality**: Lower settings
- **Close tabs**: Free up memory
- **Use server rendering**: For weak GPUs
- **Upgrade hardware**: Consider better GPU

---

## Keyboard Shortcuts

### Navigation
- `W/A/S/D` - Move camera
- `Q/E` - Move up/down
- `Space` - Reset camera
- `F` - Fit to view
- `Shift` - Move faster
- `Ctrl` - Move slower

### Annotations
- `P` - Point annotation
- `L` - Line/distance
- `A` - Area
- `S` - Slope
- `V` - Volume
- `Esc` - Cancel creation
- `Delete` - Delete selected

### View
- `1` - Top view
- `2` - Front view
- `3` - Side view
- `4` - Isometric view
- `G` - Toggle grid
- `H` - Toggle annotations

### General
- `Ctrl+S` - Save
- `Ctrl+Z` - Undo
- `Ctrl+Y` - Redo
- `Ctrl+C` - Copy
- `Ctrl+V` - Paste

---

## Support

### Need Help?
- **Documentation**: Check this guide
- **Video Tutorials**: Coming soon
- **Email Support**: support@yourcompany.com
- **Live Chat**: Available 9am-5pm

### Report Issues
- **Bug Reports**: GitHub Issues
- **Feature Requests**: Feature request form
- **Feedback**: feedback@yourcompany.com

---

**Last Updated:** April 2, 2026  
**Version:** 1.0.0  
**Platform:** Spatial AI Platform
