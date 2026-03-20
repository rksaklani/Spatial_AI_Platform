"""
GLTF/GLB Parser (Task 14.5)

Parses glTF 2.0 format files (JSON and binary).

Features:
- Mesh geometry extraction
- Material and texture support
- Scene hierarchy handling
- Animation data (for future use)
"""

import numpy as np
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
import struct
import base64
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

# glTF component types
GLTF_COMPONENT_TYPES = {
    5120: ('b', 1, np.int8),    # BYTE
    5121: ('B', 1, np.uint8),   # UNSIGNED_BYTE
    5122: ('h', 2, np.int16),   # SHORT
    5123: ('H', 2, np.uint16),  # UNSIGNED_SHORT
    5125: ('I', 4, np.uint32),  # UNSIGNED_INT
    5126: ('f', 4, np.float32), # FLOAT
}

# glTF accessor types
GLTF_ACCESSOR_TYPES = {
    'SCALAR': 1,
    'VEC2': 2,
    'VEC3': 3,
    'VEC4': 4,
    'MAT2': 4,
    'MAT3': 9,
    'MAT4': 16,
}


def parse_gltf(file_path: str) -> ParserResult:
    """
    Parse a glTF or GLB file.
    
    Args:
        file_path: Path to glTF/GLB file
        
    Returns:
        ParserResult with parsed data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"glTF file not found: {file_path}")
    
    logger.info(f"Parsing glTF file: {file_path}")
    
    try:
        # Try trimesh first
        return _parse_with_trimesh(file_path)
    except ImportError:
        logger.warning("trimesh not available, using native parser")
        return _parse_gltf_native(file_path)
    except Exception as e:
        logger.warning(f"trimesh failed: {e}, using native parser")
        return _parse_gltf_native(file_path)


def _parse_with_trimesh(file_path: str) -> ParserResult:
    """Parse glTF using trimesh library."""
    import trimesh
    
    # Load glTF file
    scene_or_mesh = trimesh.load(file_path)
    
    # Handle scene with multiple meshes
    if isinstance(scene_or_mesh, trimesh.Scene):
        meshes = [g for g in scene_or_mesh.geometry.values() if isinstance(g, trimesh.Trimesh)]
        if not meshes:
            raise ValueError("glTF file contains no valid meshes")
        mesh = trimesh.util.concatenate(meshes)
    else:
        mesh = scene_or_mesh
    
    vertices = mesh.vertices.astype(np.float32)
    faces = mesh.faces.astype(np.int32)
    
    n = len(vertices)
    f = len(faces)
    logger.info(f"glTF has {n} vertices, {f} faces")
    
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
    
    # Sample points from mesh
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
        
        # PBR properties
        if hasattr(mat, 'baseColorFactor'):
            mat_info.diffuse_color = np.array(mat.baseColorFactor[:3])
        elif hasattr(mat, 'diffuse'):
            color = mat.diffuse
            if isinstance(color[0], int):
                color = np.array(color[:3]) / 255.0
            mat_info.diffuse_color = np.array(color[:3])
        
        if hasattr(mat, 'roughnessFactor'):
            mat_info.roughness = mat.roughnessFactor
        if hasattr(mat, 'metallicFactor'):
            mat_info.metallic = mat.metallicFactor
        
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
        format_name="glTF",
        format_version="2.0",
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


def _parse_gltf_native(file_path: str) -> ParserResult:
    """
    Native glTF/GLB parser.
    
    Handles both JSON glTF and binary GLB formats.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()
    
    if suffix == '.glb':
        gltf_json, buffers = _parse_glb_file(file_path)
    else:
        with open(file_path, 'r', encoding='utf-8') as f:
            gltf_json = json.load(f)
        buffers = _load_gltf_buffers(gltf_json, path.parent)
    
    return _process_gltf_data(gltf_json, buffers, path.parent)


def _parse_glb_file(file_path: str) -> tuple:
    """Parse binary GLB file."""
    with open(file_path, 'rb') as f:
        # GLB header
        magic = f.read(4)
        if magic != b'glTF':
            raise ValueError("Invalid GLB magic number")
        
        version, length = struct.unpack('<II', f.read(8))
        
        if version != 2:
            logger.warning(f"GLB version {version}, expected 2")
        
        # Read chunks
        gltf_json = None
        binary_buffer = None
        
        while f.tell() < length:
            chunk_length, chunk_type = struct.unpack('<II', f.read(8))
            chunk_data = f.read(chunk_length)
            
            if chunk_type == 0x4E4F534A:  # JSON
                gltf_json = json.loads(chunk_data.decode('utf-8'))
            elif chunk_type == 0x004E4942:  # BIN
                binary_buffer = chunk_data
        
        if gltf_json is None:
            raise ValueError("GLB has no JSON chunk")
        
        buffers = []
        if binary_buffer:
            buffers.append(binary_buffer)
        
        return gltf_json, buffers


def _load_gltf_buffers(gltf: dict, base_dir: Path) -> List[bytes]:
    """Load external buffer files for glTF."""
    buffers = []
    
    for buffer_def in gltf.get('buffers', []):
        uri = buffer_def.get('uri', '')
        
        if uri.startswith('data:'):
            # Embedded base64 data
            _, data = uri.split(',', 1)
            buffers.append(base64.b64decode(data))
        elif uri:
            # External file
            buffer_path = base_dir / uri
            if buffer_path.exists():
                with open(buffer_path, 'rb') as f:
                    buffers.append(f.read())
            else:
                logger.warning(f"Buffer file not found: {buffer_path}")
                buffers.append(b'')
        else:
            buffers.append(b'')
    
    return buffers


def _get_accessor_data(gltf: dict, buffers: List[bytes], accessor_idx: int) -> np.ndarray:
    """Extract data from a glTF accessor."""
    accessor = gltf['accessors'][accessor_idx]
    buffer_view = gltf['bufferViews'][accessor['bufferView']]
    
    buffer_idx = buffer_view['buffer']
    byte_offset = buffer_view.get('byteOffset', 0) + accessor.get('byteOffset', 0)
    
    component_type = accessor['componentType']
    accessor_type = accessor['type']
    count = accessor['count']
    
    _, component_size, dtype = GLTF_COMPONENT_TYPES[component_type]
    num_components = GLTF_ACCESSOR_TYPES[accessor_type]
    
    # Read data from buffer
    buffer_data = buffers[buffer_idx]
    byte_length = count * num_components * component_size
    
    raw_data = buffer_data[byte_offset:byte_offset + byte_length]
    data = np.frombuffer(raw_data, dtype=dtype)
    
    if num_components > 1:
        data = data.reshape(count, num_components)
    
    return data.astype(np.float32) if dtype in [np.float32, np.float64] else data


def _process_gltf_data(gltf: dict, buffers: List[bytes], base_dir: Path) -> ParserResult:
    """Process glTF JSON and buffers into ParsedData."""
    all_vertices = []
    all_normals = []
    all_colors = []
    all_uvs = []
    all_faces = []
    
    vertex_offset = 0
    
    # Process all meshes
    for mesh in gltf.get('meshes', []):
        for primitive in mesh.get('primitives', []):
            attributes = primitive.get('attributes', {})
            
            # Get positions (required)
            if 'POSITION' in attributes:
                positions = _get_accessor_data(gltf, buffers, attributes['POSITION'])
                all_vertices.append(positions)
                n_verts = len(positions)
            else:
                continue
            
            # Get normals
            if 'NORMAL' in attributes:
                normals = _get_accessor_data(gltf, buffers, attributes['NORMAL'])
                all_normals.append(normalize_normals(normals))
            
            # Get colors
            if 'COLOR_0' in attributes:
                colors = _get_accessor_data(gltf, buffers, attributes['COLOR_0'])
                if colors.shape[1] == 4:
                    colors = colors[:, :3]  # Drop alpha
                if colors.max() > 1.0:
                    colors = colors / 255.0
                all_colors.append(colors)
            
            # Get UVs
            if 'TEXCOORD_0' in attributes:
                uvs = _get_accessor_data(gltf, buffers, attributes['TEXCOORD_0'])
                all_uvs.append(uvs)
            
            # Get indices
            if 'indices' in primitive:
                indices = _get_accessor_data(gltf, buffers, primitive['indices'])
                indices = indices.astype(np.int32)
                
                # Reshape to triangles
                if len(indices.shape) == 1:
                    indices = indices.reshape(-1, 3)
                
                # Offset indices for merged mesh
                indices = indices + vertex_offset
                all_faces.append(indices)
            else:
                # Generate implicit indices
                n_tris = n_verts // 3
                indices = np.arange(n_verts, dtype=np.int32).reshape(-1, 3)
                indices = indices + vertex_offset
                all_faces.append(indices)
            
            vertex_offset += n_verts
    
    if not all_vertices:
        raise ValueError("glTF file has no mesh data")
    
    # Concatenate all data
    vertices = np.concatenate(all_vertices, axis=0).astype(np.float32)
    faces = np.concatenate(all_faces, axis=0).astype(np.int32) if all_faces else None
    
    normals = None
    if all_normals:
        # Pad normals arrays to match vertex count if needed
        normals = np.concatenate(all_normals, axis=0).astype(np.float32)
        if len(normals) < len(vertices):
            normals = np.pad(normals, ((0, len(vertices) - len(normals)), (0, 0)))
    
    colors = None
    if all_colors:
        colors = np.concatenate(all_colors, axis=0).astype(np.float32)
        if len(colors) < len(vertices):
            colors = np.pad(colors, ((0, len(vertices) - len(colors)), (0, 0)))
    
    uvs = None
    if all_uvs:
        uvs = np.concatenate(all_uvs, axis=0).astype(np.float32)
    
    n = len(vertices)
    f = len(faces) if faces is not None else 0
    
    logger.info(f"Native glTF parser: {n} vertices, {f} faces")
    
    # Sample points from mesh
    if faces is not None:
        n_samples = min(100000, n * 10)
        sampled_points, sampled_colors, sampled_normals, _ = sample_mesh_to_points(
            vertices, faces, n_samples,
            vertex_colors=colors,
            vertex_normals=normals
        )
    else:
        sampled_points = vertices
        sampled_colors = colors
        sampled_normals = normals
    
    # Extract materials
    materials = []
    for mat_def in gltf.get('materials', []):
        mat_info = MaterialInfo(name=mat_def.get('name', 'material'))
        
        pbr = mat_def.get('pbrMetallicRoughness', {})
        
        if 'baseColorFactor' in pbr:
            mat_info.diffuse_color = np.array(pbr['baseColorFactor'][:3], dtype=np.float32)
        
        if 'metallicFactor' in pbr:
            mat_info.metallic = pbr['metallicFactor']
        
        if 'roughnessFactor' in pbr:
            mat_info.roughness = pbr['roughnessFactor']
        
        # Texture references
        if 'baseColorTexture' in pbr:
            tex_idx = pbr['baseColorTexture'].get('index')
            if tex_idx is not None and tex_idx < len(gltf.get('textures', [])):
                texture = gltf['textures'][tex_idx]
                if 'source' in texture and texture['source'] < len(gltf.get('images', [])):
                    image = gltf['images'][texture['source']]
                    mat_info.diffuse_texture = image.get('uri', image.get('name', ''))
        
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
        format_name="glTF",
        format_version="2.0",
        materials=materials,
        metadata={
            "parser": "native",
            "original_vertices": n,
            "original_faces": f,
            "sampled_points": len(sampled_points),
            "num_meshes": len(gltf.get('meshes', [])),
            "num_materials": len(materials),
        }
    )
