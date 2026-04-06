# Import 3D Scene - Functionality Explanation

## What is "Import 3D Scene"?

The Import 3D Scene feature allows you to upload various 3D model formats and view them in the browser.

## Supported Formats

### Direct Preview (No Processing)
These formats can be viewed immediately after upload:
- **GLB** - Binary glTF (recommended)
- **GLTF** - Text-based glTF
- **OBJ** - Wavefront Object
- **PLY** - Polygon File Format
- **FBX** - Autodesk FBX
- **DAE** - COLLADA
- **STL** - Stereolithography

### Advanced Formats (Require Processing)
- **LAS/LAZ** - Point cloud data
- **E57** - 3D imaging data
- **IFC** - Building Information Modeling

## How It Works

### Upload Flow:
1. **Select File** → Click "Import 3D File" button
2. **Upload** → File is uploaded to MinIO storage
3. **Store** → Scene record created in database
4. **Process** (optional) → Convert to Gaussian Splatting format
5. **View** → Display in 3D viewer

### Current Issue with Your GLB File

Based on the logs, your GLB file was uploaded successfully, but the viewer is trying to load it as a Gaussian Splatting scene (requesting tiles) instead of as a direct GLB model.

## Why Your GLB Isn't Showing

The problem is in the scene data format detection:

1. **Backend stores**: `source_format: ".glb"`
2. **Frontend checks**: `scene.format` (which doesn't exist)
3. **Result**: Falls back to GaussianViewer instead of ModelViewer

## Solution Applied

I've already fixed this in the code by updating `ViewerPage.tsx` to check both `scene.format` and `scene.sourceFormat` fields.

## To Fix Your Current Scene

You have two options:

### Option 1: Re-upload the GLB file
1. Delete the current scene
2. Upload the GLB file again
3. The new code will detect it correctly

### Option 2: Update the database record
Run this command to fix the existing scene:

```bash
# Connect to MongoDB and update the scene
mongosh "mongodb+srv://rksaklani90_db_user:rksaklani90_db_user@cluster0.lelxuus.mongodb.net/spatial_ai_platform"

# Then run:
db.scenes.updateOne(
  { _id: "7970bf2e-c33d-4043-99b9-b6a268517a23" },
  { $set: { format: "glb" } }
)
```

## Expected Behavior After Fix

When you upload a GLB file:
1. ✅ File uploads to MinIO
2. ✅ Scene record created with `source_format: ".glb"`
3. ✅ Viewer detects GLB format
4. ✅ ModelViewer loads and displays the 3D model
5. ✅ You can rotate, zoom, and interact with the model

## Features Available in ModelViewer

- **Orbit Controls** - Click and drag to rotate
- **Zoom** - Scroll to zoom in/out
- **Pan** - Right-click and drag to pan
- **Camera Controls** - Use toolbar buttons:
  - Reset Camera
  - Fit to View
  - Preset Views (Top, Front, Side, Isometric)

## Troubleshooting

### Model Not Loading?
1. Check browser console for errors
2. Verify file format is supported
3. Check file size (large files may take time)
4. Ensure MinIO is running and accessible

### Black Screen?
1. Model might be too small/large - use "Fit to View" button
2. Check if model has materials/textures
3. Try different camera angles

### Performance Issues?
1. Large models (>100MB) may be slow
2. Reduce polygon count in your 3D software
3. Use GLB format (more efficient than GLTF)

## Next Steps

1. **Refresh the page** - The code fixes are now in place
2. **Try uploading a new GLB file** - It should work correctly now
3. **Use camera controls** - All toolbar buttons are now functional and draggable

## Technical Details

### File Storage
- Files stored in MinIO at: `scenes/{scene_id}/input.{ext}`
- Accessible via: `/api/v1/scenes/{scene_id}/download`

### Database Schema
```javascript
{
  _id: "scene-uuid",
  name: "filename",
  source_format: ".glb",  // Extension with dot
  format: "glb",          // Format without dot (now added)
  source_type: "import",
  status: "completed",
  storage_path: "scenes/uuid/input.glb"
}
```

### Viewer Selection Logic
```typescript
const format = scene?.format || scene?.sourceFormat;
const isModelFormat = ['glb', 'gltf', 'obj', 'ply', ...].includes(format);

if (isModelFormat) {
  // Use ModelViewer for direct 3D models
} else {
  // Use GaussianViewer for point clouds/splatting
}
```
