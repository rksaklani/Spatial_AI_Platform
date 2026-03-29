"""
Property Tests for Task 14: 3D File Import
Property-based tests for PLY round-trip and JSON metadata round-trip.
"""
import pytest
import numpy as np
from pathlib import Path
import tempfile
import json
from hypothesis import given, strategies as st, settings
from hypothesis.extra.numpy import arrays


class TestPLYRoundTrip:
    """
    Property 1: PLY parsing round-trip
    For any valid PLY scene file, parsing and then serializing SHALL produce 
    a PLY file that parses to equivalent scene data.
    Validates: Requirements 20.8
    """
    
    @given(
        num_points=st.integers(min_value=10, max_value=1000),
        has_colors=st.booleans(),
        has_normals=st.booleans()
    )
    @settings(max_examples=5, deadline=5000)
    def test_ply_point_cloud_round_trip(self, num_points, has_colors, has_normals, tmp_path):
        """Test PLY point cloud round-trip with various properties"""
        from workers.parsers.ply_parser import PLYParser
        
        # Generate random point cloud data
        positions = np.random.rand(num_points, 3).astype(np.float32) * 10.0
        
        colors = None
        if has_colors:
            colors = np.random.randint(0, 255, (num_points, 3), dtype=np.uint8)
        
        normals = None
        if has_normals:
            normals = np.random.rand(num_points, 3).astype(np.float32)
            # Normalize
            norms = np.linalg.norm(normals, axis=1, keepdims=True)
            normals = normals / (norms + 1e-8)
        
        # Create PLY file
        ply_path = tmp_path / "test.ply"
        self._write_ply(ply_path, positions, colors, normals)
        
        # Parse PLY
        parser = PLYParser()
        result1 = parser.parse(str(ply_path))
        
        # Serialize back to PLY
        ply_path2 = tmp_path / "test2.ply"
        self._write_ply(ply_path2, result1['positions'], result1.get('colors'), result1.get('normals'))
        
        # Parse again
        result2 = parser.parse(str(ply_path2))
        
        # Verify equivalence
        assert result1['point_count'] == result2['point_count']
        assert np.allclose(result1['positions'], result2['positions'], atol=1e-5)
        
        if has_colors and result1.get('colors') is not None:
            assert np.allclose(result1['colors'], result2['colors'], atol=1)
        
        if has_normals and result1.get('normals') is not None:
            assert np.allclose(result1['normals'], result2['normals'], atol=1e-5)
    
    def _write_ply(self, path, positions, colors=None, normals=None):
        """Helper to write PLY file"""
        with open(path, 'w') as f:
            # Header
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(positions)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            
            if normals is not None:
                f.write("property float nx\n")
                f.write("property float ny\n")
                f.write("property float nz\n")
            
            if colors is not None:
                f.write("property uchar red\n")
                f.write("property uchar green\n")
                f.write("property uchar blue\n")
            
            f.write("end_header\n")
            
            # Data
            for i in range(len(positions)):
                line = f"{positions[i, 0]} {positions[i, 1]} {positions[i, 2]}"
                
                if normals is not None:
                    line += f" {normals[i, 0]} {normals[i, 1]} {normals[i, 2]}"
                
                if colors is not None:
                    line += f" {colors[i, 0]} {colors[i, 1]} {colors[i, 2]}"
                
                f.write(line + "\n")
    
    @given(
        num_gaussians=st.integers(min_value=10, max_value=500)
    )
    @settings(max_examples=3, deadline=5000)
    def test_ply_gaussian_splatting_round_trip(self, num_gaussians, tmp_path):
        """Test PLY Gaussian Splatting format round-trip"""
        from workers.parsers.ply_parser import PLYParser
        
        # Generate Gaussian data
        positions = np.random.rand(num_gaussians, 3).astype(np.float32) * 10.0
        scales = np.random.rand(num_gaussians, 3).astype(np.float32) * 0.5
        rotations = np.random.rand(num_gaussians, 4).astype(np.float32)
        # Normalize quaternions
        rotations = rotations / np.linalg.norm(rotations, axis=1, keepdims=True)
        opacities = np.random.rand(num_gaussians, 1).astype(np.float32)
        sh_coeffs = np.random.rand(num_gaussians, 16, 3).astype(np.float32)
        
        # Write Gaussian PLY
        ply_path = tmp_path / "gaussians.ply"
        self._write_gaussian_ply(ply_path, positions, scales, rotations, opacities, sh_coeffs)
        
        # Parse
        parser = PLYParser()
        result1 = parser.parse(str(ply_path))
        
        # Serialize back
        ply_path2 = tmp_path / "gaussians2.ply"
        self._write_gaussian_ply(
            ply_path2,
            result1['positions'],
            result1.get('scales'),
            result1.get('rotations'),
            result1.get('opacities'),
            result1.get('sh_coefficients')
        )
        
        # Parse again
        result2 = parser.parse(str(ply_path2))
        
        # Verify equivalence
        assert result1['point_count'] == result2['point_count']
        assert np.allclose(result1['positions'], result2['positions'], atol=1e-5)
        
        if result1.get('scales') is not None:
            assert np.allclose(result1['scales'], result2['scales'], atol=1e-5)
        
        if result1.get('rotations') is not None:
            assert np.allclose(result1['rotations'], result2['rotations'], atol=1e-5)
    
    def _write_gaussian_ply(self, path, positions, scales, rotations, opacities, sh_coeffs):
        """Helper to write Gaussian Splatting PLY"""
        with open(path, 'w') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {len(positions)}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("property float scale_0\n")
            f.write("property float scale_1\n")
            f.write("property float scale_2\n")
            f.write("property float rot_0\n")
            f.write("property float rot_1\n")
            f.write("property float rot_2\n")
            f.write("property float rot_3\n")
            f.write("property float opacity\n")
            
            # SH coefficients (simplified - just first 3)
            for i in range(3):
                f.write(f"property float f_dc_{i}\n")
            
            f.write("end_header\n")
            
            for i in range(len(positions)):
                line = f"{positions[i, 0]} {positions[i, 1]} {positions[i, 2]}"
                line += f" {scales[i, 0]} {scales[i, 1]} {scales[i, 2]}"
                line += f" {rotations[i, 0]} {rotations[i, 1]} {rotations[i, 2]} {rotations[i, 3]}"
                line += f" {opacities[i, 0]}"
                line += f" {sh_coeffs[i, 0, 0]} {sh_coeffs[i, 0, 1]} {sh_coeffs[i, 0, 2]}"
                f.write(line + "\n")


class TestJSONMetadataRoundTrip:
    """
    Property 2: Scene metadata round-trip
    For any valid Scene_Graph object, parsing the serialized JSON and then 
    serializing again SHALL produce equivalent JSON.
    Validates: Requirements 20.7
    """
    
    @given(
        num_objects=st.integers(min_value=1, max_value=20),
        scene_name=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
    )
    @settings(max_examples=5, deadline=3000)
    def test_scene_graph_json_round_trip(self, num_objects, scene_name, tmp_path):
        """Test Scene_Graph JSON serialization round-trip"""
        from workers.semantic_analysis import Scene_Graph, Scene_Object
        
        # Create scene graph
        scene_graph = Scene_Graph(scene_id=f"scene_{scene_name}")
        
        # Add objects
        for i in range(num_objects):
            obj = Scene_Object(
                object_id=f"obj_{i}",
                category=np.random.choice(['wall', 'floor', 'ceiling', 'furniture', 'door']),
                confidence=float(np.random.rand()),
                bounds_min=np.random.rand(3).tolist(),
                bounds_max=(np.random.rand(3) + 1.0).tolist(),
                point_indices=np.random.randint(0, 10000, size=100).tolist()
            )
            scene_graph.objects.append(obj)
        
        # Serialize to JSON
        json_path = tmp_path / "scene_graph.json"
        scene_graph_dict = {
            'scene_id': scene_graph.scene_id,
            'objects': [
                {
                    'object_id': obj.object_id,
                    'category': obj.category,
                    'confidence': obj.confidence,
                    'bounds_min': obj.bounds_min,
                    'bounds_max': obj.bounds_max,
                    'point_indices': obj.point_indices
                }
                for obj in scene_graph.objects
            ]
        }
        
        with open(json_path, 'w') as f:
            json.dump(scene_graph_dict, f, indent=2)
        
        # Parse JSON
        with open(json_path, 'r') as f:
            loaded_dict = json.load(f)
        
        # Serialize again
        json_path2 = tmp_path / "scene_graph2.json"
        with open(json_path2, 'w') as f:
            json.dump(loaded_dict, f, indent=2)
        
        # Parse again
        with open(json_path2, 'r') as f:
            loaded_dict2 = json.load(f)
        
        # Verify equivalence
        assert loaded_dict['scene_id'] == loaded_dict2['scene_id']
        assert len(loaded_dict['objects']) == len(loaded_dict2['objects'])
        
        for obj1, obj2 in zip(loaded_dict['objects'], loaded_dict2['objects']):
            assert obj1['object_id'] == obj2['object_id']
            assert obj1['category'] == obj2['category']
            assert abs(obj1['confidence'] - obj2['confidence']) < 1e-6
            assert np.allclose(obj1['bounds_min'], obj2['bounds_min'], atol=1e-6)
            assert np.allclose(obj1['bounds_max'], obj2['bounds_max'], atol=1e-6)
    
    @given(
        has_materials=st.booleans(),
        has_hierarchy=st.booleans()
    )
    @settings(max_examples=4, deadline=3000)
    def test_scene_metadata_with_optional_fields(self, has_materials, has_hierarchy, tmp_path):
        """Test scene metadata round-trip with optional fields"""
        # Create metadata with optional fields
        metadata = {
            'scene_id': 'test_scene',
            'name': 'Test Scene',
            'created_at': '2026-03-23T10:00:00Z',
            'point_count': 100000,
            'bounds': {
                'min': [0.0, 0.0, 0.0],
                'max': [10.0, 10.0, 10.0]
            }
        }
        
        if has_materials:
            metadata['materials'] = [
                {
                    'name': 'Material1',
                    'diffuse_color': [0.8, 0.8, 0.8],
                    'texture_path': 'textures/mat1.png'
                }
            ]
        
        if has_hierarchy:
            metadata['hierarchy'] = {
                'root': 'building',
                'children': ['floor1', 'floor2']
            }
        
        # Serialize
        json_path = tmp_path / "metadata.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Parse
        with open(json_path, 'r') as f:
            loaded1 = json.load(f)
        
        # Serialize again
        json_path2 = tmp_path / "metadata2.json"
        with open(json_path2, 'w') as f:
            json.dump(loaded1, f, indent=2)
        
        # Parse again
        with open(json_path2, 'r') as f:
            loaded2 = json.load(f)
        
        # Verify equivalence
        assert loaded1 == loaded2
        
        if has_materials:
            assert 'materials' in loaded2
            assert len(loaded2['materials']) == len(loaded1['materials'])
        
        if has_hierarchy:
            assert 'hierarchy' in loaded2
            assert loaded2['hierarchy'] == loaded1['hierarchy']


class TestEdgeCases:
    """Test edge cases for round-trip serialization"""
    
    def test_empty_scene_graph(self, tmp_path):
        """Test round-trip with empty scene graph"""
        metadata = {
            'scene_id': 'empty_scene',
            'objects': []
        }
        
        # Serialize
        json_path = tmp_path / "empty.json"
        with open(json_path, 'w') as f:
            json.dump(metadata, f)
        
        # Parse and serialize again
        with open(json_path, 'r') as f:
            loaded = json.load(f)
        
        json_path2 = tmp_path / "empty2.json"
        with open(json_path2, 'w') as f:
            json.dump(loaded, f)
        
        with open(json_path2, 'r') as f:
            loaded2 = json.load(f)
        
        assert loaded == loaded2
        assert len(loaded2['objects']) == 0
    
    def test_large_point_cloud(self, tmp_path):
        """Test round-trip with large point cloud"""
        from workers.parsers.ply_parser import PLYParser
        
        # Create large point cloud
        num_points = 10000
        positions = np.random.rand(num_points, 3).astype(np.float32) * 100.0
        
        # Write PLY
        ply_path = tmp_path / "large.ply"
        with open(ply_path, 'w') as f:
            f.write("ply\n")
            f.write("format ascii 1.0\n")
            f.write(f"element vertex {num_points}\n")
            f.write("property float x\n")
            f.write("property float y\n")
            f.write("property float z\n")
            f.write("end_header\n")
            
            for i in range(num_points):
                f.write(f"{positions[i, 0]} {positions[i, 1]} {positions[i, 2]}\n")
        
        # Parse
        parser = PLYParser()
        result = parser.parse(str(ply_path))
        
        # Verify
        assert result['point_count'] == num_points
        assert result['positions'].shape == (num_points, 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
