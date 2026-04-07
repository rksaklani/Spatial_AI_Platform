"""
Property Test for Task 14.11: PLY Round-Trip
**Validates: Requirements 20.8**

Property 1: PLY parsing round-trip
For any valid PLY scene file, parsing and then serializing SHALL produce 
a PLY file that parses to equivalent scene data.
"""
import pytest
import numpy as np
import tempfile
from pathlib import Path
from hypothesis import given, strategies as st, settings, HealthCheck
from plyfile import PlyData, PlyElement

from workers.parsers.ply_parser import parse_ply
from workers.parsers.base import ParsedDataType


def serialize_ply(parsed_data, output_path: str):
    """
    Serialize ParsedData back to PLY format.
    
    Args:
        parsed_data: ParsedData object from parse_ply
        output_path: Path to write PLY file
    """
    data = parsed_data.data
    
    # Build dtype based on available data
    dtype = [
        ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
    ]
    
    # Add normals if present
    if data.normals is not None:
        dtype.extend([
            ('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4'),
        ])
    
    # Add colors if present
    if data.colors is not None:
        dtype.extend([
            ('red', 'u1'), ('green', 'u1'), ('blue', 'u1'),
        ])
    
    # Add Gaussian properties if present
    if data.is_gaussian:
        dtype.extend([
            ('scale_0', 'f4'), ('scale_1', 'f4'), ('scale_2', 'f4'),
            ('rot_0', 'f4'), ('rot_1', 'f4'), ('rot_2', 'f4'), ('rot_3', 'f4'),
            ('opacity', 'f4'),
        ])
        
        # Add SH coefficients
        if data.sh_coeffs is not None:
            num_sh = data.sh_coeffs.shape[1]
            for i in range(min(num_sh, 3)):
                dtype.append((f'f_dc_{i}', 'f4'))
            for i in range(3, num_sh):
                dtype.append((f'f_rest_{i-3}', 'f4'))
    
    # Create structured array
    vertex_data = np.zeros(data.point_count, dtype=dtype)
    
    # Fill positions
    vertex_data['x'] = data.positions[:, 0]
    vertex_data['y'] = data.positions[:, 1]
    vertex_data['z'] = data.positions[:, 2]
    
    # Fill normals
    if data.normals is not None:
        vertex_data['nx'] = data.normals[:, 0]
        vertex_data['ny'] = data.normals[:, 1]
        vertex_data['nz'] = data.normals[:, 2]
    
    # Fill colors (convert from [0,1] to [0,255])
    if data.colors is not None:
        colors_uint8 = (data.colors * 255).astype(np.uint8)
        vertex_data['red'] = colors_uint8[:, 0]
        vertex_data['green'] = colors_uint8[:, 1]
        vertex_data['blue'] = colors_uint8[:, 2]
    
    # Fill Gaussian properties
    if data.is_gaussian:
        vertex_data['scale_0'] = data.scales[:, 0]
        vertex_data['scale_1'] = data.scales[:, 1]
        vertex_data['scale_2'] = data.scales[:, 2]
        
        vertex_data['rot_0'] = data.rotations[:, 0]
        vertex_data['rot_1'] = data.rotations[:, 1]
        vertex_data['rot_2'] = data.rotations[:, 2]
        vertex_data['rot_3'] = data.rotations[:, 3]
        
        vertex_data['opacity'] = data.opacities.flatten()
        
        if data.sh_coeffs is not None:
            num_sh = data.sh_coeffs.shape[1]
            for i in range(min(num_sh, 3)):
                vertex_data[f'f_dc_{i}'] = data.sh_coeffs[:, i]
            for i in range(3, num_sh):
                vertex_data[f'f_rest_{i-3}'] = data.sh_coeffs[:, i]
    
    # Create PLY element and write
    vertex_element = PlyElement.describe(vertex_data, 'vertex')
    
    # Add faces if present
    if data.faces is not None:
        face_dtype = [('vertex_indices', 'i4', (3,))]
        face_data = np.zeros(data.face_count, dtype=face_dtype)
        face_data['vertex_indices'] = data.faces
        face_element = PlyElement.describe(face_data, 'face')
        PlyData([vertex_element, face_element]).write(output_path)
    else:
        PlyData([vertex_element]).write(output_path)


def compare_parsed_data(data1, data2, atol=1e-5):
    """
    Compare two ParsedData objects for equivalence.
    
    Args:
        data1: First ParsedData
        data2: Second ParsedData
        atol: Absolute tolerance for floating point comparison
        
    Returns:
        True if equivalent, False otherwise
    """
    # Check basic properties
    if data1.point_count != data2.point_count:
        return False
    
    if data1.data_type != data2.data_type:
        return False
    
    if data1.is_gaussian != data2.is_gaussian:
        return False
    
    # Check positions
    if not np.allclose(data1.positions, data2.positions, atol=atol):
        return False
    
    # Check colors
    if (data1.colors is None) != (data2.colors is None):
        return False
    if data1.colors is not None:
        # Colors are normalized to [0,1], allow small tolerance
        if not np.allclose(data1.colors, data2.colors, atol=0.01):
            return False
    
    # Check normals
    if (data1.normals is None) != (data2.normals is None):
        return False
    if data1.normals is not None:
        if not np.allclose(data1.normals, data2.normals, atol=atol):
            return False
    
    # Check faces
    if (data1.faces is None) != (data2.faces is None):
        return False
    if data1.faces is not None:
        if data1.face_count != data2.face_count:
            return False
        if not np.array_equal(data1.faces, data2.faces):
            return False
    
    # Check Gaussian properties
    if data1.is_gaussian:
        if not np.allclose(data1.scales, data2.scales, atol=atol):
            return False
        if not np.allclose(data1.rotations, data2.rotations, atol=atol):
            return False
        if not np.allclose(data1.opacities, data2.opacities, atol=atol):
            return False
        if data1.sh_coeffs is not None and data2.sh_coeffs is not None:
            if not np.allclose(data1.sh_coeffs, data2.sh_coeffs, atol=atol):
                return False
    
    return True


class TestPLYRoundTrip:
    """
    **Validates: Requirements 20.8**
    
    Property 1: PLY parsing round-trip
    For any valid PLY scene file, parsing and then serializing SHALL produce 
    a PLY file that parses to equivalent scene data.
    """
    
    @given(
        num_points=st.integers(min_value=10, max_value=500),
        has_colors=st.booleans(),
        has_normals=st.booleans()
    )
    @settings(max_examples=10, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ply_point_cloud_round_trip(self, num_points, has_colors, has_normals):
        """
        Test PLY point cloud round-trip with various properties.
        
        Property: parse(serialize(parse(ply))) == parse(ply)
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate random point cloud data
            positions = np.random.rand(num_points, 3).astype(np.float32) * 10.0
            
            colors = None
            if has_colors:
                # Generate colors in [0, 255] range
                colors = np.random.randint(0, 256, (num_points, 3), dtype=np.uint8)
            
            normals = None
            if has_normals:
                normals = np.random.rand(num_points, 3).astype(np.float32) * 2 - 1
                # Normalize
                norms = np.linalg.norm(normals, axis=1, keepdims=True)
                norms[norms == 0] = 1
                normals = normals / norms
            
            # Create initial PLY file
            ply_path1 = tmp_path / "test1.ply"
            self._write_simple_ply(ply_path1, positions, colors, normals)
            
            # Parse PLY (first parse)
            result1 = parse_ply(str(ply_path1))
            
            # Serialize back to PLY
            ply_path2 = tmp_path / "test2.ply"
            serialize_ply(result1, str(ply_path2))
            
            # Parse again (second parse)
            result2 = parse_ply(str(ply_path2))
            
            # Verify equivalence
            assert compare_parsed_data(result1.data, result2.data), \
                "Round-trip failed: parsed data not equivalent"
    
    @given(
        num_gaussians=st.integers(min_value=10, max_value=300)
    )
    @settings(max_examples=5, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ply_gaussian_splatting_round_trip(self, num_gaussians):
        """
        Test PLY Gaussian Splatting format round-trip.
        
        Property: parse(serialize(parse(ply))) == parse(ply)
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate Gaussian data
            positions = np.random.rand(num_gaussians, 3).astype(np.float32) * 10.0
            scales = np.abs(np.random.rand(num_gaussians, 3).astype(np.float32) * 0.5)
            
            # Generate normalized quaternions
            rotations = np.random.rand(num_gaussians, 4).astype(np.float32)
            rotations = rotations / np.linalg.norm(rotations, axis=1, keepdims=True)
            
            opacities = np.random.rand(num_gaussians, 1).astype(np.float32)
            
            # Generate SH coefficients (just DC for simplicity)
            sh_coeffs = np.random.rand(num_gaussians, 3).astype(np.float32)
            
            # Write Gaussian PLY
            ply_path1 = tmp_path / "gaussians1.ply"
            self._write_gaussian_ply(ply_path1, positions, scales, rotations, opacities, sh_coeffs)
            
            # Parse
            result1 = parse_ply(str(ply_path1))
            
            # Serialize back
            ply_path2 = tmp_path / "gaussians2.ply"
            serialize_ply(result1, str(ply_path2))
            
            # Parse again
            result2 = parse_ply(str(ply_path2))
            
            # Verify equivalence
            assert compare_parsed_data(result1.data, result2.data), \
                "Gaussian round-trip failed: parsed data not equivalent"
    
    @given(
        num_points=st.integers(min_value=10, max_value=200),
        num_faces=st.integers(min_value=5, max_value=100)
    )
    @settings(max_examples=5, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_ply_mesh_round_trip(self, num_points, num_faces):
        """
        Test PLY mesh format round-trip with faces.
        
        Property: parse(serialize(parse(ply))) == parse(ply)
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            
            # Generate mesh data
            positions = np.random.rand(num_points, 3).astype(np.float32) * 10.0
            colors = np.random.randint(0, 256, (num_points, 3), dtype=np.uint8)
            
            # Generate valid face indices
            faces = np.random.randint(0, num_points, (num_faces, 3), dtype=np.int32)
            
            # Write mesh PLY
            ply_path1 = tmp_path / "mesh1.ply"
            self._write_mesh_ply(ply_path1, positions, colors, faces)
            
            # Parse
            result1 = parse_ply(str(ply_path1))
            
            # Serialize back
            ply_path2 = tmp_path / "mesh2.ply"
            serialize_ply(result1, str(ply_path2))
            
            # Parse again
            result2 = parse_ply(str(ply_path2))
            
            # Verify equivalence
            assert compare_parsed_data(result1.data, result2.data), \
                "Mesh round-trip failed: parsed data not equivalent"
    
    def test_ply_empty_point_cloud(self, tmp_path):
        """Test round-trip with minimal point cloud (edge case)."""
        # Single point
        positions = np.array([[0.0, 0.0, 0.0]], dtype=np.float32)
        
        ply_path1 = tmp_path / "single.ply"
        self._write_simple_ply(ply_path1, positions, None, None)
        
        result1 = parse_ply(str(ply_path1))
        
        ply_path2 = tmp_path / "single2.ply"
        serialize_ply(result1, str(ply_path2))
        
        result2 = parse_ply(str(ply_path2))
        
        assert compare_parsed_data(result1.data, result2.data)
    
    def test_ply_large_coordinates(self, tmp_path):
        """Test round-trip with large coordinate values."""
        # Large coordinates
        positions = np.array([
            [1000.0, 2000.0, 3000.0],
            [-5000.0, -6000.0, -7000.0],
            [0.001, 0.002, 0.003]
        ], dtype=np.float32)
        
        ply_path1 = tmp_path / "large.ply"
        self._write_simple_ply(ply_path1, positions, None, None)
        
        result1 = parse_ply(str(ply_path1))
        
        ply_path2 = tmp_path / "large2.ply"
        serialize_ply(result1, str(ply_path2))
        
        result2 = parse_ply(str(ply_path2))
        
        assert compare_parsed_data(result1.data, result2.data)
    
    # Helper methods to write PLY files
    
    def _write_simple_ply(self, path, positions, colors=None, normals=None):
        """Write a simple PLY file with positions, optional colors and normals."""
        dtype = [('x', 'f4'), ('y', 'f4'), ('z', 'f4')]
        
        if normals is not None:
            dtype.extend([('nx', 'f4'), ('ny', 'f4'), ('nz', 'f4')])
        
        if colors is not None:
            dtype.extend([('red', 'u1'), ('green', 'u1'), ('blue', 'u1')])
        
        vertex_data = np.zeros(len(positions), dtype=dtype)
        vertex_data['x'] = positions[:, 0]
        vertex_data['y'] = positions[:, 1]
        vertex_data['z'] = positions[:, 2]
        
        if normals is not None:
            vertex_data['nx'] = normals[:, 0]
            vertex_data['ny'] = normals[:, 1]
            vertex_data['nz'] = normals[:, 2]
        
        if colors is not None:
            vertex_data['red'] = colors[:, 0]
            vertex_data['green'] = colors[:, 1]
            vertex_data['blue'] = colors[:, 2]
        
        vertex_element = PlyElement.describe(vertex_data, 'vertex')
        PlyData([vertex_element]).write(path)
    
    def _write_gaussian_ply(self, path, positions, scales, rotations, opacities, sh_coeffs):
        """Write a Gaussian Splatting PLY file."""
        dtype = [
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('scale_0', 'f4'), ('scale_1', 'f4'), ('scale_2', 'f4'),
            ('rot_0', 'f4'), ('rot_1', 'f4'), ('rot_2', 'f4'), ('rot_3', 'f4'),
            ('opacity', 'f4'),
        ]
        
        # Add SH coefficients
        num_sh = sh_coeffs.shape[1]
        for i in range(num_sh):
            dtype.append((f'f_dc_{i}', 'f4'))
        
        vertex_data = np.zeros(len(positions), dtype=dtype)
        vertex_data['x'] = positions[:, 0]
        vertex_data['y'] = positions[:, 1]
        vertex_data['z'] = positions[:, 2]
        
        vertex_data['scale_0'] = scales[:, 0]
        vertex_data['scale_1'] = scales[:, 1]
        vertex_data['scale_2'] = scales[:, 2]
        
        vertex_data['rot_0'] = rotations[:, 0]
        vertex_data['rot_1'] = rotations[:, 1]
        vertex_data['rot_2'] = rotations[:, 2]
        vertex_data['rot_3'] = rotations[:, 3]
        
        vertex_data['opacity'] = opacities.flatten()
        
        for i in range(num_sh):
            vertex_data[f'f_dc_{i}'] = sh_coeffs[:, i]
        
        vertex_element = PlyElement.describe(vertex_data, 'vertex')
        PlyData([vertex_element]).write(path)
    
    def _write_mesh_ply(self, path, positions, colors, faces):
        """Write a mesh PLY file with vertices and faces."""
        # Vertex element
        vertex_dtype = [
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('red', 'u1'), ('green', 'u1'), ('blue', 'u1')
        ]
        
        vertex_data = np.zeros(len(positions), dtype=vertex_dtype)
        vertex_data['x'] = positions[:, 0]
        vertex_data['y'] = positions[:, 1]
        vertex_data['z'] = positions[:, 2]
        vertex_data['red'] = colors[:, 0]
        vertex_data['green'] = colors[:, 1]
        vertex_data['blue'] = colors[:, 2]
        
        vertex_element = PlyElement.describe(vertex_data, 'vertex')
        
        # Face element
        face_dtype = [('vertex_indices', 'i4', (3,))]
        face_data = np.zeros(len(faces), dtype=face_dtype)
        face_data['vertex_indices'] = faces
        
        face_element = PlyElement.describe(face_data, 'face')
        
        PlyData([vertex_element, face_element]).write(path)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
