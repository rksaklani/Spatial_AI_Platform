"""
FBX Parser (Task 15.1)

Parses Autodesk FBX format for meshes and animations.
Uses trimesh or Open3D for parsing - FBX is a complex proprietary format.

Note: Full FBX support requires Autodesk FBX SDK or libraries that interface with it.
"""

import numpy as np
from pathlib import Path
import logging

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
    MaterialInfo,
    normalize_normals,
    sample_mesh_to_points,
)

logger = logging.getLogger(__name__)


def parse_fbx(file_path: str) -> ParserResult:
    """
    Parse an FBX file.
    
    FBX is a complex format - this uses available Python libraries.
    For full support, the Autodesk FBX SDK would be needed.
    
    Args:
        file_path: Path to FBX file
        
    Returns:
        ParserResult with parsed data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"FBX file not found: {file_path}")
    
    logger.info(f"Parsing FBX file: {file_path}")
    
    # Try different libraries
    errors = []
    
    # Try trimesh (uses assimp or other backends)
    try:
        return _parse_with_trimesh(file_path)
    except Exception as e:
        errors.append(f"trimesh: {e}")
    
    # Try Open3D
    try:
        return _parse_with_open3d(file_path)
    except Exception as e:
        errors.append(f"open3d: {e}")
    
    # Try pyfbx if available
    try:
        return _parse_with_pyfbx(file_path)
    except Exception as e:
        errors.append(f"pyfbx: {e}")
    
    # All methods failed
    error_msg = "FBX parsing failed with all available methods: " + "; ".join(errors)
    logger.error(error_msg)
    raise ImportError(error_msg + ". Install assimp or FBX SDK bindings.")


def _parse_with_trimesh(file_path: str) -> ParserResult:
    """Parse FBX using trimesh (requires assimp backend)."""
    import trimesh
    
    scene_or_mesh = trimesh.load(file_path)
    
    if isinstance(scene_or_mesh, trimesh.Scene):
        meshes = [g for g in scene_or_mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("FBX file contains no valid meshes")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = scene_or_mesh
    
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"FBX has {n} vertices, {f} faces")
    
    # Extract attributes
    colors = None
    if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
        colors = mesh.visual.vertex_colors[:, :3].astype(np.float32) / 255.0
    
    normals = None
    if mesh.vertex_normals is not None:
        normals = normalize_normals(mesh.vertex_normals.astype(np.float32))
    
    uvs = None
    if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
        uvs = mesh.visual.uv.astype(np.float32)
    
    # Sample points
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
        mat_info = MaterialInfo(name=getattr(mat, 'name', 'default'))
        if hasattr(mat, 'diffuse'):
            diff = mat.diffuse
            mat_info.diffuse_color = np.array(diff[:3]) / 255.0 if isinstance(diff[0], int) else np.array(diff[:3])
        materials.append(mat_info)
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces,
        uvs=uvs,
        data_type=ParsedDataType.MESH,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="FBX",
        materials=materials,
        metadata={
            "parser": "trimesh",
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
        }
    )


def _parse_with_open3d(file_path: str) -> ParserResult:
    """Parse FBX using Open3D."""
    import open3d as o3d
    
    mesh = o3d.io.read_triangle_mesh(file_path)
    
    if not mesh.has_vertices():
        raise ValueError("FBX file has no vertices")
    
    vertices = np.asarray(mesh.vertices).astype(np.float32)
    faces = np.asarray(mesh.triangles).astype(np.int32)
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"FBX (Open3D) has {n} vertices, {f} faces")
    
    colors = None
    if mesh.has_vertex_colors():
        colors = np.asarray(mesh.vertex_colors).astype(np.float32)
    
    normals = None
    if mesh.has_vertex_normals():
        normals = normalize_normals(np.asarray(mesh.vertex_normals).astype(np.float32))
    
    # Sample points
    n_samples = min(100000, n * 10)
    sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples,
        vertex_colors=colors,
        vertex_normals=normals
    )
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces,
        data_type=ParsedDataType.MESH,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="FBX",
        metadata={
            "parser": "open3d",
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
        }
    )


def _parse_with_pyfbx(file_path: str) -> ParserResult:
    """Parse FBX using pyfbx library."""
    try:
        import pyfbx
    except ImportError:
        raise ImportError("pyfbx not installed")
    
    # pyfbx is a basic FBX parser
    scene = pyfbx.parse(file_path)
    
    all_vertices = []
    all_faces = []
    vertex_offset = 0
    
    # Extract meshes from scene
    for node in scene.nodes:
        if hasattr(node, 'mesh') and node.mesh:
            mesh = node.mesh
            vertices = np.array(mesh.vertices, dtype=np.float32).reshape(-1, 3)
            all_vertices.append(vertices)
            
            if hasattr(mesh, 'indices') and mesh.indices:
                indices = np.array(mesh.indices, dtype=np.int32).reshape(-1, 3)
                indices = indices + vertex_offset
                all_faces.append(indices)
            
            vertex_offset += len(vertices)
    
    if not all_vertices:
        raise ValueError("No meshes found in FBX")
    
    vertices = np.concatenate(all_vertices, axis=0)
    faces = np.concatenate(all_faces, axis=0) if all_faces else None
    
    n = len(vertices)
    f = len(faces) if faces is not None else 0
    
    # Sample points
    if faces is not None:
        n_samples = min(100000, n * 10)
        sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
            vertices, faces, n_samples
        )
    else:
        sampled_points = vertices
        sampled_colors = None
        sampled_normals = None
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=sampled_colors,
        normals=sampled_normals,
        faces=faces,
        data_type=ParsedDataType.MESH if faces is not None else ParsedDataType.POINT_CLOUD,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="FBX",
        metadata={
            "parser": "pyfbx",
            "original_vertices": n,
            "original_faces": f,
        }
    )
