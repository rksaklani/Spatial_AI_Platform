"""
PLY File Parser (Task 14.2)

Parses PLY format files including:
- ASCII and binary PLY formats
- Point clouds with positions, colors, normals
- Meshes with faces
- Gaussian Splatting data (scales, rotations, opacities, SH coefficients)
"""

import numpy as np
import struct
from pathlib import Path
from typing import Optional, Tuple, List
import logging

from workers.parsers.base import (
    ParsedData,
    ParserResult,
    ParsedDataType,
    normalize_colors,
    normalize_normals,
)

logger = logging.getLogger(__name__)


# Standard PLY property names for Gaussian Splatting
GAUSSIAN_PROPERTIES = {
    'scale_0', 'scale_1', 'scale_2',  # Scales
    'rot_0', 'rot_1', 'rot_2', 'rot_3',  # Quaternion rotation
    'opacity',  # Opacity
    'f_dc_0', 'f_dc_1', 'f_dc_2',  # DC spherical harmonics (color)
}

# SH coefficient properties (up to degree 3)
SH_PROPERTIES = [f'f_rest_{i}' for i in range(45)]  # 15 * 3 for RGB


def parse_ply(file_path: str) -> ParserResult:
    """
    Parse a PLY file.
    
    Supports:
    - ASCII PLY
    - Binary little-endian PLY
    - Binary big-endian PLY
    - Gaussian Splatting PLY
    - Standard point clouds and meshes
    
    Args:
        file_path: Path to PLY file
        
    Returns:
        ParserResult with parsed data
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"PLY file not found: {file_path}")
    
    logger.info(f"Parsing PLY file: {file_path}")
    
    try:
        # Try plyfile library first (most robust)
        return _parse_with_plyfile(file_path)
    except ImportError:
        logger.warning("plyfile not available, using fallback parser")
        return _parse_ply_fallback(file_path)
    except Exception as e:
        logger.warning(f"plyfile failed: {e}, trying fallback parser")
        return _parse_ply_fallback(file_path)


def _parse_with_plyfile(file_path: str) -> ParserResult:
    """Parse PLY using plyfile library."""
    from plyfile import PlyData
    
    plydata = PlyData.read(file_path)
    
    # Check for vertex element
    if 'vertex' not in plydata:
        raise ValueError("PLY file has no vertex element")
    
    vertex = plydata['vertex']
    vertex_data = vertex.data
    n = len(vertex_data)
    
    logger.info(f"PLY has {n} vertices")
    
    # Extract positions (required)
    positions = np.zeros((n, 3), dtype=np.float32)
    positions[:, 0] = vertex_data['x']
    positions[:, 1] = vertex_data['y']
    positions[:, 2] = vertex_data['z']
    
    # Extract colors (optional)
    colors = None
    color_names = [('red', 'green', 'blue'), ('r', 'g', 'b')]
    for r, g, b in color_names:
        if r in vertex_data.dtype.names:
            colors = np.zeros((n, 3), dtype=np.float32)
            colors[:, 0] = vertex_data[r]
            colors[:, 1] = vertex_data[g]
            colors[:, 2] = vertex_data[b]
            colors = normalize_colors(colors)
            break
    
    # Extract normals (optional)
    normals = None
    if 'nx' in vertex_data.dtype.names:
        normals = np.zeros((n, 3), dtype=np.float32)
        normals[:, 0] = vertex_data['nx']
        normals[:, 1] = vertex_data['ny']
        normals[:, 2] = vertex_data['nz']
        normals = normalize_normals(normals)
    
    # Check for Gaussian attributes
    is_gaussian = 'scale_0' in vertex_data.dtype.names or 'opacity' in vertex_data.dtype.names
    
    scales = None
    rotations = None
    opacities = None
    sh_coeffs = None
    
    if is_gaussian:
        logger.info("Detected Gaussian Splatting PLY format")
        
        # Extract scales
        if 'scale_0' in vertex_data.dtype.names:
            scales = np.zeros((n, 3), dtype=np.float32)
            scales[:, 0] = vertex_data['scale_0']
            scales[:, 1] = vertex_data['scale_1']
            scales[:, 2] = vertex_data['scale_2']
            # Scales are stored as log-scale, convert to linear
            if scales.min() < 0:  # Log-scaled
                scales = np.exp(scales)
        
        # Extract rotations (quaternion)
        if 'rot_0' in vertex_data.dtype.names:
            rotations = np.zeros((n, 4), dtype=np.float32)
            rotations[:, 0] = vertex_data['rot_0']
            rotations[:, 1] = vertex_data['rot_1']
            rotations[:, 2] = vertex_data['rot_2']
            rotations[:, 3] = vertex_data['rot_3']
            # Normalize quaternions
            norms = np.linalg.norm(rotations, axis=1, keepdims=True)
            norms[norms == 0] = 1
            rotations = rotations / norms
        
        # Extract opacities
        if 'opacity' in vertex_data.dtype.names:
            opacities = vertex_data['opacity'].reshape(-1, 1).astype(np.float32)
            # Apply sigmoid if stored as logit
            if opacities.min() < 0:
                opacities = 1.0 / (1.0 + np.exp(-opacities))
        
        # Extract SH coefficients
        if 'f_dc_0' in vertex_data.dtype.names:
            # DC coefficients (RGB)
            sh_dc = np.zeros((n, 3), dtype=np.float32)
            sh_dc[:, 0] = vertex_data['f_dc_0']
            sh_dc[:, 1] = vertex_data['f_dc_1']
            sh_dc[:, 2] = vertex_data['f_dc_2']
            
            # Rest coefficients (up to degree 3 = 15 coeffs per color)
            sh_rest = []
            for i in range(45):
                name = f'f_rest_{i}'
                if name in vertex_data.dtype.names:
                    sh_rest.append(vertex_data[name])
            
            if sh_rest:
                sh_rest = np.stack(sh_rest, axis=1).astype(np.float32)
                sh_coeffs = np.concatenate([sh_dc, sh_rest], axis=1)
            else:
                sh_coeffs = sh_dc
            
            # Compute RGB colors from SH DC coefficients
            if colors is None:
                SH_C0 = 0.28209479177387814
                colors = sh_dc * SH_C0 + 0.5
                colors = np.clip(colors, 0, 1)
    
    # Extract faces (optional)
    faces = None
    face_count = 0
    if 'face' in plydata:
        face_element = plydata['face']
        face_data = face_element.data
        face_count = len(face_data)
        
        if 'vertex_indices' in face_data.dtype.names:
            face_list = face_data['vertex_indices']
            # Handle variable-length faces (triangulate if needed)
            triangles = []
            for face in face_list:
                if len(face) == 3:
                    triangles.append(face)
                elif len(face) > 3:
                    # Fan triangulation
                    for i in range(1, len(face) - 1):
                        triangles.append([face[0], face[i], face[i + 1]])
            if triangles:
                faces = np.array(triangles, dtype=np.int32)
                face_count = len(faces)
    
    # Determine data type
    if is_gaussian:
        data_type = ParsedDataType.GAUSSIAN
    elif faces is not None:
        data_type = ParsedDataType.MESH
    else:
        data_type = ParsedDataType.POINT_CLOUD
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        normals=normals,
        faces=faces,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        sh_coeffs=sh_coeffs,
        data_type=data_type,
        is_gaussian=is_gaussian,
        point_count=n,
        face_count=face_count,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="PLY",
        format_version=None,
        metadata={
            "has_colors": colors is not None,
            "has_normals": normals is not None,
            "has_faces": faces is not None,
            "is_gaussian": is_gaussian,
            "vertex_count": n,
            "face_count": face_count,
        }
    )


def _parse_ply_fallback(file_path: str) -> ParserResult:
    """
    Fallback PLY parser without plyfile dependency.
    
    Supports ASCII and binary little-endian formats.
    """
    with open(file_path, 'rb') as f:
        # Read header
        header_lines = []
        while True:
            line = f.readline().decode('ascii', errors='ignore').strip()
            header_lines.append(line)
            if line == 'end_header':
                break
        
        header = PLYHeader.parse(header_lines)
        
        # Read data based on format
        if header.format == 'ascii':
            return _read_ascii_ply(f, header)
        elif header.format == 'binary_little_endian':
            return _read_binary_ply(f, header, '<')
        elif header.format == 'binary_big_endian':
            return _read_binary_ply(f, header, '>')
        else:
            raise ValueError(f"Unknown PLY format: {header.format}")


class PLYProperty:
    """PLY property definition."""
    def __init__(self, name: str, dtype: str, is_list: bool = False, count_type: str = None):
        self.name = name
        self.dtype = dtype
        self.is_list = is_list
        self.count_type = count_type
    
    @property
    def numpy_dtype(self):
        """Convert PLY dtype to numpy dtype."""
        dtype_map = {
            'char': np.int8,
            'uchar': np.uint8,
            'short': np.int16,
            'ushort': np.uint16,
            'int': np.int32,
            'uint': np.uint32,
            'float': np.float32,
            'double': np.float64,
            'int8': np.int8,
            'uint8': np.uint8,
            'int16': np.int16,
            'uint16': np.uint16,
            'int32': np.int32,
            'uint32': np.uint32,
            'float32': np.float32,
            'float64': np.float64,
        }
        return dtype_map.get(self.dtype, np.float32)
    
    @property
    def struct_format(self):
        """Get struct format character."""
        fmt_map = {
            'char': 'b', 'uchar': 'B',
            'short': 'h', 'ushort': 'H',
            'int': 'i', 'uint': 'I',
            'float': 'f', 'double': 'd',
            'int8': 'b', 'uint8': 'B',
            'int16': 'h', 'uint16': 'H',
            'int32': 'i', 'uint32': 'I',
            'float32': 'f', 'float64': 'd',
        }
        return fmt_map.get(self.dtype, 'f')


class PLYElement:
    """PLY element definition."""
    def __init__(self, name: str, count: int):
        self.name = name
        self.count = count
        self.properties: List[PLYProperty] = []


class PLYHeader:
    """Parsed PLY header."""
    def __init__(self):
        self.format = 'ascii'
        self.version = '1.0'
        self.elements: List[PLYElement] = []
        self.comments = []
    
    @classmethod
    def parse(cls, lines: List[str]) -> 'PLYHeader':
        """Parse header lines."""
        header = cls()
        current_element = None
        
        for line in lines:
            parts = line.split()
            if not parts:
                continue
            
            if parts[0] == 'ply':
                continue
            elif parts[0] == 'format':
                header.format = parts[1]
                header.version = parts[2] if len(parts) > 2 else '1.0'
            elif parts[0] == 'comment':
                header.comments.append(' '.join(parts[1:]))
            elif parts[0] == 'element':
                current_element = PLYElement(parts[1], int(parts[2]))
                header.elements.append(current_element)
            elif parts[0] == 'property':
                if current_element is None:
                    continue
                if parts[1] == 'list':
                    prop = PLYProperty(parts[4], parts[3], is_list=True, count_type=parts[2])
                else:
                    prop = PLYProperty(parts[2], parts[1])
                current_element.properties.append(prop)
            elif parts[0] == 'end_header':
                break
        
        return header
    
    def get_element(self, name: str) -> Optional[PLYElement]:
        """Get element by name."""
        for elem in self.elements:
            if elem.name == name:
                return elem
        return None


def _read_ascii_ply(f, header: PLYHeader) -> ParserResult:
    """Read ASCII PLY data."""
    vertex_elem = header.get_element('vertex')
    face_elem = header.get_element('face')
    
    if vertex_elem is None:
        raise ValueError("No vertex element in PLY")
    
    n = vertex_elem.count
    prop_names = [p.name for p in vertex_elem.properties]
    
    # Read vertex data
    vertex_data = []
    for _ in range(n):
        line = f.readline().decode('ascii').strip()
        values = [float(v) for v in line.split()]
        vertex_data.append(values)
    
    vertex_data = np.array(vertex_data, dtype=np.float32)
    
    # Extract properties by index
    def get_prop(name):
        if name in prop_names:
            idx = prop_names.index(name)
            return vertex_data[:, idx]
        return None
    
    positions = np.stack([get_prop('x'), get_prop('y'), get_prop('z')], axis=1)
    
    colors = None
    if 'red' in prop_names:
        colors = np.stack([get_prop('red'), get_prop('green'), get_prop('blue')], axis=1)
        colors = normalize_colors(colors)
    
    normals = None
    if 'nx' in prop_names:
        normals = np.stack([get_prop('nx'), get_prop('ny'), get_prop('nz')], axis=1)
        normals = normalize_normals(normals)
    
    # Read faces if present
    faces = None
    if face_elem:
        face_list = []
        for _ in range(face_elem.count):
            line = f.readline().decode('ascii').strip()
            values = [int(v) for v in line.split()]
            count = values[0]
            indices = values[1:count + 1]
            # Triangulate if needed
            if count == 3:
                face_list.append(indices)
            elif count > 3:
                for i in range(1, count - 1):
                    face_list.append([indices[0], indices[i], indices[i + 1]])
        if face_list:
            faces = np.array(face_list, dtype=np.int32)
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        normals=normals,
        faces=faces,
        data_type=ParsedDataType.MESH if faces is not None else ParsedDataType.POINT_CLOUD,
        point_count=n,
        face_count=len(faces) if faces is not None else 0,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="PLY",
        format_version=header.version,
        metadata={"parser": "fallback_ascii"}
    )


def _read_binary_ply(f, header: PLYHeader, endian: str) -> ParserResult:
    """Read binary PLY data."""
    vertex_elem = header.get_element('vertex')
    face_elem = header.get_element('face')
    
    if vertex_elem is None:
        raise ValueError("No vertex element in PLY")
    
    n = vertex_elem.count
    prop_names = [p.name for p in vertex_elem.properties]
    
    # Build struct format for vertex
    vertex_fmt = endian + ''.join(p.struct_format for p in vertex_elem.properties)
    vertex_size = struct.calcsize(vertex_fmt)
    
    # Read all vertices at once
    vertex_bytes = f.read(n * vertex_size)
    vertex_data = np.zeros((n, len(vertex_elem.properties)), dtype=np.float32)
    
    for i in range(n):
        values = struct.unpack_from(vertex_fmt, vertex_bytes, i * vertex_size)
        vertex_data[i] = values
    
    def get_prop(name):
        if name in prop_names:
            idx = prop_names.index(name)
            return vertex_data[:, idx]
        return None
    
    positions = np.stack([get_prop('x'), get_prop('y'), get_prop('z')], axis=1).astype(np.float32)
    
    colors = None
    if 'red' in prop_names:
        colors = np.stack([get_prop('red'), get_prop('green'), get_prop('blue')], axis=1)
        colors = normalize_colors(colors)
    
    normals = None
    if 'nx' in prop_names:
        normals = np.stack([get_prop('nx'), get_prop('ny'), get_prop('nz')], axis=1)
        normals = normalize_normals(normals)
    
    # Check for Gaussian properties
    is_gaussian = 'scale_0' in prop_names
    scales = rotations = opacities = sh_coeffs = None
    
    if is_gaussian:
        if 'scale_0' in prop_names:
            scales = np.stack([get_prop('scale_0'), get_prop('scale_1'), get_prop('scale_2')], axis=1).astype(np.float32)
            if scales.min() < 0:
                scales = np.exp(scales)
        
        if 'rot_0' in prop_names:
            rotations = np.stack([get_prop('rot_0'), get_prop('rot_1'), get_prop('rot_2'), get_prop('rot_3')], axis=1).astype(np.float32)
            norms = np.linalg.norm(rotations, axis=1, keepdims=True)
            norms[norms == 0] = 1
            rotations = rotations / norms
        
        if 'opacity' in prop_names:
            opacities = get_prop('opacity').reshape(-1, 1).astype(np.float32)
            if opacities.min() < 0:
                opacities = 1.0 / (1.0 + np.exp(-opacities))
        
        if 'f_dc_0' in prop_names:
            sh_dc = np.stack([get_prop('f_dc_0'), get_prop('f_dc_1'), get_prop('f_dc_2')], axis=1).astype(np.float32)
            sh_coeffs = sh_dc
            
            if colors is None:
                SH_C0 = 0.28209479177387814
                colors = sh_dc * SH_C0 + 0.5
                colors = np.clip(colors, 0, 1)
    
    # Read faces if present
    faces = None
    if face_elem and face_elem.count > 0:
        face_prop = face_elem.properties[0] if face_elem.properties else None
        if face_prop and face_prop.is_list:
            face_list = []
            count_fmt = endian + PLYProperty('', face_prop.count_type).struct_format
            idx_fmt = endian + face_prop.struct_format
            count_size = struct.calcsize(count_fmt)
            idx_size = struct.calcsize(idx_fmt)
            
            for _ in range(face_elem.count):
                count_bytes = f.read(count_size)
                count = struct.unpack(count_fmt, count_bytes)[0]
                indices = []
                for _ in range(count):
                    idx_bytes = f.read(idx_size)
                    idx = struct.unpack(idx_fmt, idx_bytes)[0]
                    indices.append(idx)
                
                # Triangulate
                if count == 3:
                    face_list.append(indices)
                elif count > 3:
                    for i in range(1, count - 1):
                        face_list.append([indices[0], indices[i], indices[i + 1]])
            
            if face_list:
                faces = np.array(face_list, dtype=np.int32)
    
    if is_gaussian:
        data_type = ParsedDataType.GAUSSIAN
    elif faces is not None:
        data_type = ParsedDataType.MESH
    else:
        data_type = ParsedDataType.POINT_CLOUD
    
    parsed_data = ParsedData(
        positions=positions,
        colors=colors,
        normals=normals,
        faces=faces,
        scales=scales,
        rotations=rotations,
        opacities=opacities,
        sh_coeffs=sh_coeffs,
        data_type=data_type,
        is_gaussian=is_gaussian,
        point_count=n,
        face_count=len(faces) if faces is not None else 0,
    )
    
    return ParserResult(
        data=parsed_data,
        format_name="PLY",
        format_version=header.version,
        metadata={"parser": "fallback_binary", "endian": "little" if endian == '<' else "big"}
    )
