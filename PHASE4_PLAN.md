# Phase 4 Implementation Plan: 3D File Import Pipeline

**Status:** Ready to Begin  
**Estimated Tasks:** 14-17 (3D Import, Extended Formats, BIM/IFC, Checkpoint)  
**Dependencies:** trimesh, plyfile, laspy, pygltflib, open3d, ifcopenshell

---

## Overview

Phase 4 enables direct import of existing 3D files (point clouds, meshes, Gaussian splats) into the platform, bypassing video reconstruction. Imported files go through the same optimization and tiling pipeline as reconstructed scenes.

---

## Task Priority Order

### 🔴 High Priority (Core MVP)

| Order | Task | Description | Effort |
|-------|------|-------------|--------|
| 1 | **14.1** | Import upload endpoint | Medium |
| 2 | **14.2** | PLY parser | Low |
| 3 | **14.6** | Gaussian SPLAT parser | Medium |
| 4 | **14.5** | GLB/GLTF parser | Medium |
| 5 | **14.4** | OBJ parser | Low |
| 6 | **14.7** | Convert to internal representation | Medium |
| 7 | **14.9** | Integration with optimization pipeline | Low |

### 🟡 Medium Priority (Extended Formats)

| Order | Task | Description | Effort |
|-------|------|-------------|--------|
| 8 | **14.3** | LAS/LAZ point cloud parser | Medium |
| 9 | **15.2** | STL parser | Low |
| 10 | **15.3** | COLLADA (DAE) parser | Medium |
| 11 | **15.1** | FBX parser | High |
| 12 | **15.4** | E57 point cloud parser | High |

### 🟢 Lower Priority (BIM/Advanced)

| Order | Task | Description | Effort |
|-------|------|-------------|--------|
| 13 | **16.1** | IFC parser | High |
| 14 | **15.5** | Camera metadata import | Medium |
| 15 | **15.6** | Texture/material import | Medium |
| 16 | **16.2-16.5** | BIM features (clash, quantity) | High |

---

## Implementation Details

### Task 14.1: Import Upload Endpoint

**File:** `backend/api/import_3d.py`

```python
# Endpoint: POST /api/v1/scenes/import
# Accept: multipart/form-data with file

SUPPORTED_FORMATS = {
    ".ply": "point_cloud",
    ".las": "point_cloud", 
    ".laz": "point_cloud",
    ".obj": "mesh",
    ".glb": "mesh",
    ".gltf": "mesh",
    ".splat": "gaussian",
    ".stl": "mesh",
    ".fbx": "mesh",
    ".dae": "mesh",
    ".e57": "point_cloud",
    ".ifc": "bim",
}

MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB
```

**Response:**
```json
{
  "scene_id": "uuid",
  "format": "ply",
  "format_type": "point_cloud",
  "file_size_bytes": 123456,
  "status": "processing"
}
```

---

### Task 14.2: PLY Parser

**File:** `backend/workers/import_parsers/ply_parser.py`

**Dependencies:** `plyfile>=1.0.0`

```python
class PLYParser:
    """Parse PLY point clouds and meshes."""
    
    def parse(self, file_path: str) -> Dict[str, np.ndarray]:
        """
        Returns:
            - positions: (N, 3) float32
            - colors: (N, 3) float32 (0-1 range)
            - normals: (N, 3) float32 (optional)
            - faces: (F, 3) int32 (for meshes)
        """
```

**Handles:**
- Binary and ASCII PLY
- Point clouds (vertex only)
- Triangle meshes (vertex + face)
- Vertex colors (RGB/RGBA)
- Vertex normals

---

### Task 14.6: Gaussian SPLAT Parser

**File:** `backend/workers/import_parsers/splat_parser.py`

```python
class SplatParser:
    """Parse Gaussian Splatting .splat files."""
    
    def parse(self, file_path: str) -> Dict[str, np.ndarray]:
        """
        Returns:
            - positions: (N, 3) float32
            - scales: (N, 3) float32
            - rotations: (N, 4) float32 (quaternion)
            - opacities: (N, 1) float32
            - sh_coeffs: (N, 48) float32 (SH DC + rest)
        """
```

**Format:** Binary format with packed Gaussian parameters

---

### Task 14.5: GLB/GLTF Parser

**File:** `backend/workers/import_parsers/gltf_parser.py`

**Dependencies:** `pygltflib>=1.16.0` or `trimesh>=4.0.0`

```python
class GLTFParser:
    """Parse glTF 2.0 and GLB files."""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Returns:
            - meshes: List of mesh data
            - materials: List of material definitions
            - textures: List of texture references
            - hierarchy: Scene graph structure
        """
```

**Handles:**
- GLB (binary) and GLTF (JSON + external)
- Multiple meshes and materials
- PBR materials
- Embedded textures

---

### Task 14.4: OBJ Parser  

**File:** `backend/workers/import_parsers/obj_parser.py`

**Dependencies:** `trimesh>=4.0.0`

```python
class OBJParser:
    """Parse Wavefront OBJ files with MTL materials."""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        Returns:
            - vertices: (N, 3) float32
            - faces: (F, 3) int32
            - uvs: (N, 2) float32 (optional)
            - normals: (N, 3) float32 (optional)
            - materials: Dict of MTL materials
        """
```

---

### Task 14.3: LAS/LAZ Parser

**File:** `backend/workers/import_parsers/las_parser.py`

**Dependencies:** `laspy>=2.5.0`

```python
class LASParser:
    """Parse LAS/LAZ point cloud files."""
    
    def parse(self, file_path: str) -> Dict[str, np.ndarray]:
        """
        Returns:
            - positions: (N, 3) float64 (geo-referenced)
            - colors: (N, 3) float32 (from RGB or intensity)
            - classification: (N,) int8 (ground, vegetation, etc.)
            - intensity: (N,) float32
        """
```

**Handles:**
- LAS 1.2, 1.3, 1.4
- LAZ compression (via lazrs)
- Point classifications
- GPS time

---

## New Files to Create

### Workers
```
backend/workers/
├── import_parsers/
│   ├── __init__.py
│   ├── base_parser.py       # Abstract base class
│   ├── ply_parser.py        # Task 14.2
│   ├── splat_parser.py      # Task 14.6
│   ├── gltf_parser.py       # Task 14.5
│   ├── obj_parser.py        # Task 14.4
│   ├── las_parser.py        # Task 14.3
│   ├── stl_parser.py        # Task 15.2
│   ├── fbx_parser.py        # Task 15.1
│   ├── dae_parser.py        # Task 15.3
│   ├── e57_parser.py        # Task 15.4
│   └── ifc_parser.py        # Task 16.1
└── import_pipeline.py       # Celery task for import processing
```

### API
```
backend/api/
└── import_3d.py             # Import endpoints
```

### Models
```
backend/models/
└── import_job.py            # ImportJobInDB model
```

### Tests
```
backend/tests/
├── test_task_14_import.py   # Core import tests
├── test_task_15_formats.py  # Extended format tests
└── test_task_16_bim.py      # BIM/IFC tests
```

---

## Dependencies to Add

```txt
# requirements.txt additions

# 3D File Parsing
laspy>=2.5.0              # LAS/LAZ point clouds
lazrs>=0.6.0              # LAZ decompression
pygltflib>=1.16.0         # glTF/GLB parsing
pye57>=0.4.0              # E57 point clouds (optional)
ifcopenshell>=0.8.0       # IFC/BIM parsing (optional)

# Already have:
# trimesh>=4.0.0          # OBJ, STL, GLB, DAE
# plyfile>=1.0.0          # PLY
# open3d>=0.18.0          # General 3D processing
```

---

## Celery Task Flow

```python
# backend/workers/import_pipeline.py

@celery_app.task(name="workers.import_pipeline.process_import")
def process_import(scene_id: str, job_id: str, file_path: str, format: str):
    """
    Main import pipeline task.
    
    Steps:
    1. Parse file based on format
    2. Convert to internal representation
    3. Generate initial Gaussians (for meshes/point clouds)
    4. Route to optimization pipeline
    5. Route to tiling pipeline
    """
```

---

## Internal Representation

All imported formats convert to a unified internal format:

```python
class ImportedScene:
    """Internal representation for imported 3D data."""
    
    # Point/Gaussian data
    positions: np.ndarray      # (N, 3) float32
    colors: np.ndarray         # (N, 3) float32 (optional)
    normals: np.ndarray        # (N, 3) float32 (optional)
    
    # Gaussian-specific (if from .splat)
    scales: np.ndarray         # (N, 3) float32 (optional)
    rotations: np.ndarray      # (N, 4) float32 (optional)
    opacities: np.ndarray      # (N, 1) float32 (optional)
    sh_coeffs: np.ndarray      # (N, 48) float32 (optional)
    
    # Mesh-specific (if from OBJ/GLB/etc)
    faces: np.ndarray          # (F, 3) int32 (optional)
    uvs: np.ndarray            # (N, 2) float32 (optional)
    
    # Metadata
    source_format: str
    bounding_box: BoundingBox
    point_count: int
    has_colors: bool
    has_normals: bool
    is_gaussian: bool
    is_mesh: bool
```

---

## Conversion Strategy

| Source Format | Conversion Method |
|---------------|-------------------|
| `.splat` | Direct load as Gaussians |
| `.ply` (Gaussian) | Direct load if has Gaussian attributes |
| `.ply` (points) | Initialize Gaussians from points |
| `.ply` (mesh) | Sample surface → Initialize Gaussians |
| `.obj`, `.glb`, `.stl` | Sample mesh surface → Initialize Gaussians |
| `.las`, `.laz`, `.e57` | Subsample if needed → Initialize Gaussians |
| `.ifc` | Extract geometry → Convert meshes |

---

## Suggested Implementation Order

### Week 1: Core Import (Tasks 14.1-14.7)
```
Day 1: 14.1 - Import endpoint + validation
Day 2: 14.2 - PLY parser (reuse existing plyfile code)
Day 3: 14.6 - SPLAT parser (custom binary format)
Day 4: 14.5 - GLTF/GLB parser (using trimesh)
Day 5: 14.4 - OBJ parser (using trimesh)
Day 6: 14.7 - Internal conversion + 14.9 - Pipeline integration
Day 7: 14.10* - Tests for core formats
```

### Week 2: Extended Formats (Tasks 14.3, 15.1-15.4)
```
Day 1: 14.3 - LAS/LAZ parser
Day 2: 15.2 - STL parser (trivial with trimesh)
Day 3: 15.3 - COLLADA/DAE parser
Day 4-5: 15.1 - FBX parser (complex)
Day 6-7: 15.4 - E57 parser (complex)
```

### Week 3: BIM/IFC + Polish (Tasks 15.5-16.5)
```
Day 1-2: 16.1 - IFC parser
Day 3: 15.5 - Camera metadata import
Day 4: 15.6 - Texture/material import
Day 5-6: 16.2-16.5 - BIM features
Day 7: 17 - Checkpoint verification
```

---

## Test Strategy

### Unit Tests
```python
# test_task_14_import.py

class TestPLYParser:
    def test_parse_ascii_ply()
    def test_parse_binary_ply()
    def test_parse_mesh_ply()
    def test_parse_colored_ply()

class TestSplatParser:
    def test_parse_splat_file()
    def test_gaussian_parameters_valid()

class TestGLTFParser:
    def test_parse_glb()
    def test_parse_gltf_with_textures()
    def test_extract_materials()

class TestImportEndpoint:
    def test_upload_ply()
    def test_upload_unsupported_format()
    def test_file_size_limit()
```

### Integration Tests
```python
class TestImportPipeline:
    def test_ply_to_tiles()       # PLY → Gaussians → Optimize → Tile
    def test_splat_to_tiles()     # SPLAT → Optimize → Tile
    def test_glb_to_tiles()       # GLB → Sample → Gaussians → Tile
```

---

## Success Criteria

1. ✅ Upload PLY, OBJ, GLB, SPLAT files via API
2. ✅ Parse all core formats without errors
3. ✅ Convert to Gaussian representation
4. ✅ Route through existing optimization pipeline
5. ✅ Generate tiles identical to video-reconstructed scenes
6. ✅ Conversion time < 60s for files < 100MB
7. ✅ Support files up to 5GB

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| FBX SDK licensing | Use open-source FBX loader or skip for MVP |
| E57 complexity | Use pye57 library, defer if problematic |
| IFC file size | Stream parsing, memory mapping |
| Large point clouds | Subsample on import, LOD from start |

---

## Getting Started

```bash
# 1. Add new dependencies
pip install laspy lazrs pygltflib

# 2. Create parser directory
mkdir -p backend/workers/import_parsers

# 3. Start with PLY parser (already have plyfile)
# Extend existing code from gaussian_splatting.py

# 4. Create import endpoint
touch backend/api/import_3d.py
```

Ready to begin Phase 4 implementation!
