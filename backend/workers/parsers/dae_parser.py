"""
COLLADA (DAE) Parser (Task 15.3)

Parses COLLADA XML format (.dae files).
Supports geometry, materials, textures, and scene hierarchy.
"""

import numpy as np
from pathlib import Path
import xml.etree.ElementTree as ET
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

# COLLADA namespace
COLLADA_NS = {
    'c': 'http://www.collada.org/2005/11/COLLADASchema',
    'c14': 'http://www.collada.org/2008/03/COLLADASchema',
}


def parse_dae(file_path: str) -> ParserResult:
    """
    Parse a COLLADA (.dae) file.
    
    Args:
        file_path: Path to DAE file
        
    Returns:
        ParserResult with parsed data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"DAE file not found: {file_path}")
    
    logger.info(f"Parsing DAE file: {file_path}")
    
    try:
        import trimesh
        return _parse_with_trimesh(file_path)
    except ImportError:
        logger.warning("trimesh not available, using native parser")
        return _parse_dae_native(file_path)
    except Exception as e:
        logger.warning(f"trimesh failed: {e}, using native parser")
        return _parse_dae_native(file_path)


def _parse_with_trimesh(file_path: str) -> ParserResult:
    """Parse DAE using trimesh."""
    import trimesh
    
    scene_or_mesh = trimesh.load(file_path)
    
    if isinstance(scene_or_mesh, trimesh.Scene):
        meshes = [g for g in scene_or_mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("DAE file contains no valid meshes")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = scene_or_mesh
    
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"DAE has {n} vertices, {f} faces")
    
    colors = None
    if hasattr(mesh.visual, 'vertex_colors') and mesh.visual.vertex_colors is not None:
        colors = mesh.visual.vertex_colors[:, :3].astype(np.float32) / 255.0
    
    normals = None
    if mesh.vertex_normals is not None:
        normals = normalize_normals(mesh.vertex_normals.astype(np.float32))
    
    uvs = None
    if hasattr(mesh.visual, 'uv') and mesh.visual.uv is not None:
        uvs = mesh.visual.uv.astype(np.float32)
    
    n_samples = min(100000, n * 10)
    sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
        vertices, faces, n_samples,
        vertex_colors=colors,
        vertex_normals=normals
    )
    
    materials = []
    if hasattr(mesh.visual, 'material') and mesh.visual.material:
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
        format_name="COLLADA",
        materials=materials,
        metadata={
            "parser": "trimesh",
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
        }
    )


def _parse_dae_native(file_path: str) -> ParserResult:
    """Native COLLADA parser using XML."""
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    # Detect namespace
    ns = COLLADA_NS['c']
    if root.tag.startswith('{http://www.collada.org/2008'):
        ns = COLLADA_NS['c14']
    
    def find(parent, path):
        return parent.find(path.replace('c:', f'{{{ns}}}'))
    
    def findall(parent, path):
        return parent.findall(path.replace('c:', f'{{{ns}}}'))
    
    # Find all geometries
    all_vertices = []
    all_normals = []
    all_faces = []
    vertex_offset = 0
    
    geometries = findall(root, './/c:geometry')
    
    for geometry in geometries:
        mesh = find(geometry, 'c:mesh')
        if mesh is None:
            continue
        
        # Get vertex positions
        positions_source = None
        normals_source = None
        
        # Find sources
        sources = {}
        for source in findall(mesh, 'c:source'):
            source_id = source.get('id')
            float_array = find(source, 'c:float_array')
            if float_array is not None and float_array.text:
                values = [float(x) for x in float_array.text.split()]
                accessor = find(source, './/c:accessor')
                stride = int(accessor.get('stride', 3)) if accessor is not None else 3
                sources[source_id] = np.array(values, dtype=np.float32).reshape(-1, stride)
        
        # Find vertices element
        vertices_elem = find(mesh, 'c:vertices')
        if vertices_elem is not None:
            vertices_id = vertices_elem.get('id')
            for input_elem in findall(vertices_elem, 'c:input'):
                semantic = input_elem.get('semantic')
                source_ref = input_elem.get('source', '').lstrip('#')
                if semantic == 'POSITION' and source_ref in sources:
                    positions_source = sources[source_ref]
                elif semantic == 'NORMAL' and source_ref in sources:
                    normals_source = sources[source_ref]
        
        # Find triangles
        triangles = find(mesh, 'c:triangles')
        if triangles is None:
            triangles = find(mesh, 'c:polylist')
        
        if triangles is not None and positions_source is not None:
            # Get index data
            p_elem = find(triangles, 'c:p')
            if p_elem is not None and p_elem.text:
                indices = [int(x) for x in p_elem.text.split()]
                
                # Find stride (number of inputs)
                inputs = findall(triangles, 'c:input')
                stride = len(inputs)
                
                # Find position offset
                pos_offset = 0
                for input_elem in inputs:
                    if input_elem.get('semantic') == 'VERTEX':
                        pos_offset = int(input_elem.get('offset', 0))
                        break
                
                # Extract position indices
                pos_indices = indices[pos_offset::stride]
                
                # Build triangles
                if len(pos_indices) >= 3:
                    vertices = positions_source[pos_indices]
                    all_vertices.append(vertices)
                    
                    n_verts = len(vertices)
                    triangle_indices = np.arange(n_verts, dtype=np.int32).reshape(-1, 3)
                    triangle_indices = triangle_indices + vertex_offset
                    all_faces.append(triangle_indices)
                    
                    if normals_source is not None:
                        norm_offset = 0
                        for input_elem in inputs:
                            if input_elem.get('semantic') == 'NORMAL':
                                norm_offset = int(input_elem.get('offset', 0))
                                norm_indices = indices[norm_offset::stride]
                                normals = normals_source[norm_indices]
                                all_normals.append(normals)
                                break
                    
                    vertex_offset += n_verts
    
    if not all_vertices:
        raise ValueError("No geometry found in DAE file")
    
    vertices = np.concatenate(all_vertices, axis=0).astype(np.float32)
    faces = np.concatenate(all_faces, axis=0) if all_faces else None
    normals = np.concatenate(all_normals, axis=0) if all_normals else None
    
    if normals is not None:
        normals = normalize_normals(normals)
    
    n = len(vertices)
    f = len(faces) if faces is not None else 0
    
    logger.info(f"Native DAE parser: {n} vertices, {f} faces")
    
    # Sample points
    if faces is not None:
        n_samples = min(100000, n * 3)
        sampled_points, _, sampled_normals, _ = sample_mesh_to_points(
            vertices, faces, n_samples, vertex_normals=normals
        )
    else:
        sampled_points = vertices
        sampled_normals = normals
    
    # Generate colors from normals
    colors = None
    if sampled_normals is not None:
        colors = (sampled_normals + 1) / 2
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
        format_name="COLLADA",
        metadata={
            "parser": "native",
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
        }
    )
