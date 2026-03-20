"""
OBJ Mesh Parser (Task 14.4)

Parses Wavefront OBJ mesh format with MTL material support.

Features:
- Vertex positions, normals, texture coordinates
- Face definitions (triangles, quads, polygons)
- MTL material file parsing
- Texture file references
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Tuple
import logging
import re

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
    MaterialInfo,
    normalize_normals,
    sample_mesh_to_points,
)

logger = logging.getLogger(__name__)


def parse_obj(file_path: str) -> ParserResult:
    """
    Parse an OBJ mesh file.
    
    Args:
        file_path: Path to OBJ file
        
    Returns:
        ParserResult with parsed mesh data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"OBJ file not found: {file_path}")
    
    logger.info(f"Parsing OBJ file: {file_path}")
    
    try:
        # Try trimesh first (handles complex OBJ files well)
        return _parse_with_trimesh(file_path)
    except ImportError:
        logger.warning("trimesh not available, using native parser")
        return _parse_obj_native(file_path)
    except Exception as e:
        logger.warning(f"trimesh failed: {e}, using native parser")
        return _parse_obj_native(file_path)


def _parse_with_trimesh(file_path: str) -> ParserResult:
    """Parse OBJ using trimesh library."""
    import trimesh
    
    # Load OBJ file
    scene_or_mesh = trimesh.load(file_path)
    
    # Handle scene with multiple meshes
    if isinstance(scene_or_mesh, trimesh.Scene):
        meshes = [g for g in scene_or_mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("OBJ file contains no valid meshes")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = scene_or_mesh
    
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"OBJ has {n} vertices, {f} faces")
    
    # Extract vertex colors
    colors = None
    if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
        colors = mesh.visual.vertex_colors[:, :3].astype(np.float32) / 255.0
    
    # Extract normals
    normals = None
    if mesh.vertex_normals is not None:
        normals = normalize_normals(mesh.vertex_normals.astype(np.float32))
    
    # Extract UVs
    uvs = None
    if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
        uvs = mesh.visual.uv.astype(np.float32)
    
    # Sample points from mesh surface
    n_samples = min(100000, n * 10)
    sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples,
        vertex_colors=colors,
        vertex_normals=normals
    )
    
    # Extract materials
    materials = []
    if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material'):
        mat = mesh.visual.material
        mat_info = MaterialInfo(
            name=getattr(mat, 'name', 'default'),
        )
        if hasattr(mat, 'diffuse'):
            mat_info.diffuse_color = np.array(mat.diffuse[:3]) / 255.0 if isinstance(mat.diffuse[0], int) else np.array(mat.diffuse[:3])
        if hasattr(mat, 'specular'):
            mat_info.specular_color = np.array(mat.specular[:3]) / 255.0 if isinstance(mat.specular[0], int) else np.array(mat.specular[:3])
        materials.append(mat_info)
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces,  # Store original faces too
        uvs=uvs,
        data_type=ParsedDataType.MESH,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="OBJ",
        materials=materials,
        metadata={
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
            "has_colors": colors is not None,
            "has_normals": normals is not None,
            "has_uvs": uvs is not None,
        }
    )


def _parse_obj_native(file_path: str) -> ParserResult:
    """
    Native OBJ parser without external dependencies.
    
    Handles:
    - v (vertices)
    - vn (normals)
    - vt (texture coordinates)
    - f (faces)
    - mtllib (material library)
    - usemtl (material usage)
    """
    path = Path(file_path)
    
    vertices: List[List[float]] = []
    normals: List[List[float]] = []
    uvs: List[List[float]] = []
    faces: List[List[Tuple[int, Optional[int], Optional[int]]]] = []
    
    current_material = None
    mtl_file = None
    materials: Dict[str, MaterialInfo] = {}
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parts = line.split()
            cmd = parts[0]
            
            if cmd == 'v':
                # Vertex position
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
            elif cmd == 'vn':
                # Vertex normal
                normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
                
            elif cmd == 'vt':
                # Texture coordinate
                u = float(parts[1])
                v = float(parts[2]) if len(parts) > 2 else 0.0
                uvs.append([u, v])
                
            elif cmd == 'f':
                # Face definition
                face_verts = []
                for vert_str in parts[1:]:
                    # Format: v, v/vt, v/vt/vn, or v//vn
                    indices = vert_str.split('/')
                    v_idx = int(indices[0])
                    vt_idx = int(indices[1]) if len(indices) > 1 and indices[1] else None
                    vn_idx = int(indices[2]) if len(indices) > 2 and indices[2] else None
                    
                    # OBJ uses 1-based indexing, negative indices are relative to end
                    if v_idx < 0:
                        v_idx = len(vertices) + v_idx + 1
                    if vt_idx and vt_idx < 0:
                        vt_idx = len(uvs) + vt_idx + 1
                    if vn_idx and vn_idx < 0:
                        vn_idx = len(normals) + vn_idx + 1
                    
                    face_verts.append((v_idx - 1, vt_idx - 1 if vt_idx else None, vn_idx - 1 if vn_idx else None))
                
                faces.append(face_verts)
                
            elif cmd == 'mtllib':
                # Material library reference
                mtl_file = ' '.join(parts[1:])
                mtl_path = path.parent / mtl_file
                if mtl_path.exists():
                    materials = _parse_mtl(str(mtl_path))
                    
            elif cmd == 'usemtl':
                # Material usage
                current_material = ' '.join(parts[1:])
    
    if not vertices:
        raise ValueError("OBJ file has no vertices")
    
    n = len(vertices)
    vertices_np = np.array(vertices, dtype=np.float32)
    
    # Convert normals
    normals_np = None
    if normals:
        normals_np = normalize_normals(np.array(normals, dtype=np.float32))
    
    # Convert uvs
    uvs_np = None
    if uvs:
        uvs_np = np.array(uvs, dtype=np.float32)
    
    # Triangulate faces
    triangles = []
    for face in faces:
        if len(face) < 3:
            continue
        
        # Fan triangulation for polygons
        v0 = face[0]
        for i in range(1, len(face) - 1):
            v1 = face[i]
            v2 = face[i + 1]
            triangles.append([v0[0], v1[0], v2[0]])
    
    faces_np = np.array(triangles, dtype=np.int32) if triangles else None
    f = len(triangles) if triangles else 0
    
    logger.info(f"Native OBJ parser: {n} vertices, {f} triangles")
    
    # Sample points from mesh surface
    if faces_np is not None:
        n_samples = min(100000, n * 10)
        sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
            vertices_np, faces_np, n_samples,
            vertex_normals=normals_np
        )
    else:
        # Point cloud (no faces)
        sampled_points = vertices_np
        sampled_colors = None
        sampled_normals = normals_np
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces_np,
        uvs=uvs_np,
        data_type=ParsedDataType.MESH if faces_np is not None else ParsedDataType.POINT_CLOUD,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    # Convert materials dict to list
    mat_list = list(materials.values())
    
    return ParserResult(
        data=parsed_data,
        format_name="OBJ",
        materials=mat_list,
        metadata={
            "parser": "native",
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
            "mtl_file": mtl_file,
            "num_materials": len(materials),
        }
    )


def _parse_mtl(file_path: str) -> Dict[str, MaterialInfo]:
    """Parse MTL material file."""
    materials: Dict[str, MaterialInfo] = {}
    current_material: Optional[MaterialInfo] = None
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split()
                cmd = parts[0].lower()
                
                if cmd == 'newmtl':
                    # New material definition
                    name = ' '.join(parts[1:])
                    current_material = MaterialInfo(name=name)
                    materials[name] = current_material
                    
                elif current_material is None:
                    continue
                    
                elif cmd == 'kd':
                    # Diffuse color
                    current_material.diffuse_color = np.array([
                        float(parts[1]), float(parts[2]), float(parts[3])
                    ], dtype=np.float32)
                    
                elif cmd == 'ks':
                    # Specular color
                    current_material.specular_color = np.array([
                        float(parts[1]), float(parts[2]), float(parts[3])
                    ], dtype=np.float32)
                    
                elif cmd == 'ka':
                    # Ambient color
                    current_material.ambient_color = np.array([
                        float(parts[1]), float(parts[2]), float(parts[3])
                    ], dtype=np.float32)
                    
                elif cmd == 'ke':
                    # Emissive color
                    current_material.emissive_color = np.array([
                        float(parts[1]), float(parts[2]), float(parts[3])
                    ], dtype=np.float32)
                    
                elif cmd in ('ns', 'shininess'):
                    # Shininess -> roughness
                    ns = float(parts[1])
                    # Convert specular exponent to roughness (rough approximation)
                    current_material.roughness = 1.0 - min(ns / 1000.0, 1.0)
                    
                elif cmd == 'd' or cmd == 'tr':
                    # Dissolve (opacity) or transparency
                    val = float(parts[1])
                    if cmd == 'tr':
                        val = 1.0 - val  # Transparency to opacity
                    current_material.opacity = val
                    
                elif cmd == 'map_kd':
                    # Diffuse texture
                    current_material.diffuse_texture = ' '.join(parts[1:])
                    
                elif cmd in ('map_bump', 'bump', 'map_kn'):
                    # Normal/bump map
                    current_material.normal_texture = ' '.join(parts[1:])
                    
                elif cmd == 'map_ns':
                    # Roughness/specular map
                    current_material.roughness_texture = ' '.join(parts[1:])
                    
    except Exception as e:
        logger.warning(f"Failed to parse MTL file {file_path}: {e}")
    
    return materials
