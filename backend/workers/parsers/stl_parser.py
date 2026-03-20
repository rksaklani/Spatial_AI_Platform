"""
STL Mesh Parser (Task 15.2)

Parses STL (Stereolithography) format - both ASCII and binary.
Commonly used for 3D printing and CAD export.
"""

import numpy as np
from pathlib import Path
import struct
import logging

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
    normalize_normals,
    sample_mesh_to_points,
)

logger = logging.getLogger(__name__)


def parse_stl(file_path: str) -> ParserResult:
    """
    Parse an STL mesh file.
    
    Automatically detects ASCII vs binary format.
    
    Args:
        file_path: Path to STL file
        
    Returns:
        ParserResult with mesh data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"STL file not found: {file_path}")
    
    logger.info(f"Parsing STL file: {file_path}")
    
    try:
        import trimesh
        return _parse_with_trimesh(file_path)
    except ImportError:
        logger.warning("trimesh not available, using native parser")
        return _parse_stl_native(file_path)
    except Exception as e:
        logger.warning(f"trimesh failed: {e}, using native parser")
        return _parse_stl_native(file_path)


def _parse_with_trimesh(file_path: str) -> ParserResult:
    """Parse STL using trimesh library."""
    import trimesh
    
    mesh = trimesh.load(file_path)
    
    if isinstance(mesh, trimesh.Scene):
        meshes = [g for g in mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if meshes:
            mesh = trimesh.util.concatenate(meshes)
        else:
            raise ValueError("No valid meshes in STL file")
    
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)
    normals = normalize_normals(mesh.vertex_normals.astype(np.float32)) if mesh.vertex_normals is not None else None
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"STL has {n} vertices, {f} faces")
    
    # Sample points from mesh
    n_samples = min(100000, n * 10)
    sampled_points, _, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples, vertex_normals=normals
    )
    
    # STL has no colors - generate based on normals
    if sampled_normals is not None:
        colors = (sampled_normals + 1) / 2  # Map [-1,1] to [0,1] for visualization
    else:
        colors = np.ones((len(sampled_points), 3), dtype=np.float32) * 0.7
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=colors,
        normals=sampled_normals,
        faces=faces,
        data_type=ParsedDataType.MESH,
        point_count=len(sampled_points),
        face_count=f,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="STL",
        metadata={
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
        }
    )


def _parse_stl_native(file_path: str) -> ParserResult:
    """Native STL parser."""
    with open(file_path, 'rb') as f:
        header = f.read(80)
        
        # Check if ASCII
        try:
            header_str = header.decode('ascii', errors='ignore').lower()
            if header_str.startswith('solid') and not header_str[5:6].isspace() == False:
                return _parse_ascii_stl(file_path)
        except:
            pass
        
        # Binary STL
        num_triangles = struct.unpack('<I', f.read(4))[0]
        
        vertices = []
        face_normals = []
        
        for _ in range(num_triangles):
            # Normal (12 bytes)
            normal = struct.unpack('<3f', f.read(12))
            face_normals.append(normal)
            
            # 3 vertices (36 bytes)
            v1 = struct.unpack('<3f', f.read(12))
            v2 = struct.unpack('<3f', f.read(12))
            v3 = struct.unpack('<3f', f.read(12))
            vertices.extend([v1, v2, v3])
            
            # Attribute byte count (2 bytes, usually 0)
            f.read(2)
    
    vertices = np.array(vertices, dtype=np.float32)
    n = len(vertices)
    
    # Each 3 consecutive vertices form a triangle
    faces = np.arange(n, dtype=np.int32).reshape(-1, 3)
    f_count = len(faces)
    
    # Expand face normals to vertices
    face_normals = np.array(face_normals, dtype=np.float32)
    normals = np.repeat(face_normals, 3, axis=0)
    normals = normalize_normals(normals)
    
    logger.info(f"Native STL parser: {n} vertices, {f_count} faces")
    
    # Sample points
    n_samples = min(100000, n * 3)
    sampled_points, _, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples, vertex_normals=normals
    )
    
    colors = (sampled_normals + 1) / 2 if sampled_normals is not None else np.ones((len(sampled_points), 3)) * 0.7
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=colors.astype(np.float32),
        normals=sampled_normals,
        faces=faces,
        data_type=ParsedDataType.MESH,
        point_count=len(sampled_points),
        face_count=f_count,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="STL",
        format_version="binary",
        metadata={"parser": "native", "original_vertices": n, "original_faces": f_count}
    )


def _parse_ascii_stl(file_path: str) -> ParserResult:
    """Parse ASCII STL format."""
    vertices = []
    face_normals = []
    current_normal = None
    
    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            line = line.strip().lower()
            parts = line.split()
            
            if not parts:
                continue
            
            if parts[0] == 'facet' and len(parts) >= 5:
                current_normal = [float(parts[2]), float(parts[3]), float(parts[4])]
            elif parts[0] == 'vertex' and len(parts) >= 4:
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
                if current_normal:
                    face_normals.append(current_normal)
    
    if not vertices:
        raise ValueError("No vertices found in ASCII STL")
    
    vertices = np.array(vertices, dtype=np.float32)
    n = len(vertices)
    faces = np.arange(n, dtype=np.int32).reshape(-1, 3)
    
    normals = None
    if face_normals:
        normals = normalize_normals(np.array(face_normals, dtype=np.float32))
    
    n_samples = min(100000, n * 3)
    sampled_points, _, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples, vertex_normals=normals
    )
    
    colors = (sampled_normals + 1) / 2 if sampled_normals is not None else np.ones((len(sampled_points), 3)) * 0.7
    
    parsed_data = ParsedData(
        positions=sampled_points,
        colors=colors.astype(np.float32),
        normals=sampled_normals,
        faces=faces,
        data_type=ParsedDataType.MESH,
        point_count=len(sampled_points),
        face_count=len(faces),
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="STL",
        format_version="ascii",
        metadata={"parser": "native_ascii", "original_vertices": n}
    )
