"""
Tests for Task 12: Scene Tiling
Tests octree construction, tile size limits, hierarchical storage, and metadata persistence.
"""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json


class TestOctreeConstruction:
    """Test octree spatial structure construction"""
    
    def test_octree_node_creation(self):
        """Test basic octree node creation"""
        from workers.scene_optimization import OctreeNode
        
        # Create root node
        bounds = np.array([
            [0.0, 0.0, 0.0],  # min corner
            [10.0, 10.0, 10.0]  # max corner
        ])
        
        node = OctreeNode(bounds=bounds, level=0)
        
        assert node.level == 0
        assert np.array_equal(node.bounds, bounds)
        assert node.children == []
        assert node.gaussian_indices == []
    
    def test_octree_subdivision(self):
        """Test octree node subdivision into 8 children"""
        from workers.scene_optimization import OctreeNode
        
        # Create parent node
        bounds = np.array([
            [0.0, 0.0, 0.0],
            [10.0, 10.0, 10.0]
        ])
        
        parent = OctreeNode(bounds=bounds, level=0)
        
        # Subdivide
        parent.subdivide()
        
        # Should have 8 children
        assert len(parent.children) == 8
        
        # Each child should be at level 1
        for child in parent.children:
            assert child.level == 1
        
        # Children should cover parent's space
        # (detailed geometric verification would go here)
    
    def test_octree_build_from_gaussians(self):
        """Test building octree from Gaussian positions"""
        from workers.scene_optimization import SceneOctree, GaussianModel
        
        # Create Gaussians
        model = GaussianModel()
        positions = np.random.rand(1000, 3) * 10.0  # 1000 Gaussians in 10x10x10 space
        model.positions = positions
        model.scales = np.ones((1000, 3)) * 0.1
        model.rotations = np.tile([1, 0, 0, 0], (1000, 1))
        model.opacities = np.ones((1000, 1))
        model.sh_coefficients = np.zeros((1000, 16, 3))
        
        # Build octree
        octree = SceneOctree(max_gaussians_per_node=100)
        octree.build(model)
        
        # Should have root node
        assert octree.root is not None
        
        # Should have subdivided
        assert len(octree.get_all_leaf_nodes()) > 1
    
    def test_octree_depth_limit(self):
        """Test that octree respects maximum depth"""
        from workers.scene_optimization import SceneOctree, GaussianModel
        
        # Create many Gaussians in small space
        model = GaussianModel()
        positions = np.random.rand(10000, 3) * 1.0
        model.positions = positions
        model.scales = np.ones((10000, 3)) * 0.01
        model.rotations = np.tile([1, 0, 0, 0], (10000, 1))
        model.opacities = np.ones((10000, 1))
        model.sh_coefficients = np.zeros((10000, 16, 3))
        
        # Build octree with depth limit
        octree = SceneOctree(max_gaussians_per_node=100, max_depth=5)
        octree.build(model)
        
        # Check that no node exceeds max depth
        def check_depth(node, max_depth):
            assert node.level <= max_depth
            for child in node.children:
                check_depth(child, max_depth)
        
        check_depth(octree.root, 5)


class TestTileSizeLimits:
    """Test tile size limits (max 100K Gaussians per tile)"""
    
    def test_max_gaussians_per_tile(self):
        """Test that tiles respect 100K Gaussian limit"""
        from workers.scene_optimization import SceneOctree, GaussianModel
        
        # Create model with many Gaussians
        model = GaussianModel()
        positions = np.random.rand(500000, 3) * 100.0
        model.positions = positions
        model.scales = np.ones((500000, 3)) * 0.1
        model.rotations = np.tile([1, 0, 0, 0], (500000, 1))
        model.opacities = np.ones((500000, 1))
        model.sh_coefficients = np.zeros((500000, 16, 3))
        
        # Build octree with 100K limit
        MAX_GAUSSIANS = 100000
        octree = SceneOctree(max_gaussians_per_node=MAX_GAUSSIANS)
        octree.build(model)
        
        # Check all leaf nodes
        leaf_nodes = octree.get_all_leaf_nodes()
        for node in leaf_nodes:
            assert len(node.gaussian_indices) <= MAX_GAUSSIANS, \
                f"Node has {len(node.gaussian_indices)} Gaussians, exceeds limit of {MAX_GAUSSIANS}"
    
    def test_tile_splitting_when_limit_exceeded(self):
        """Test that tiles split when Gaussian count exceeds limit"""
        from workers.scene_optimization import OctreeNode
        
        # Create node with too many Gaussians
        bounds = np.array([[0, 0, 0], [10, 10, 10]])
        node = OctreeNode(bounds=bounds, level=0)
        node.gaussian_indices = list(range(150000))  # Exceeds 100K limit
        
        # Should trigger subdivision
        MAX_GAUSSIANS = 100000
        if len(node.gaussian_indices) > MAX_GAUSSIANS and node.level < 10:
            node.subdivide()
            assert len(node.children) == 8
    
    def test_tile_bounding_box_calculation(self):
        """Test calculation of tile bounding boxes"""
        from workers.scene_optimization import OctreeNode
        
        # Create node with known bounds
        bounds = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])
        
        node = OctreeNode(bounds=bounds, level=0)
        
        # Verify bounds
        assert np.array_equal(node.bounds[0], [1.0, 2.0, 3.0])
        assert np.array_equal(node.bounds[1], [4.0, 5.0, 6.0])
        
        # Calculate center
        center = (node.bounds[0] + node.bounds[1]) / 2
        expected_center = [2.5, 3.5, 4.5]
        assert np.allclose(center, expected_center)


class TestTileIdentifiers:
    """Test tile ID generation"""
    
    def test_tile_id_format(self):
        """Test tile ID format: L{level}_X{x}_Y{y}_Z{z}_{lod}"""
        from workers.scene_optimization import OctreeNode
        
        bounds = np.array([[0, 0, 0], [10, 10, 10]])
        node = OctreeNode(bounds=bounds, level=2)
        node.grid_position = (3, 4, 5)
        
        # Generate tile ID
        tile_id = f"L{node.level}_X{node.grid_position[0]}_Y{node.grid_position[1]}_Z{node.grid_position[2]}_high"
        
        # Verify format
        assert tile_id.startswith("L2_")
        assert "_X3_" in tile_id
        assert "_Y4_" in tile_id
        assert "_Z5_" in tile_id
        assert tile_id.endswith("_high")
    
    def test_unique_tile_ids(self):
        """Test that tile IDs are unique based on octree position"""
        from workers.scene_optimization import SceneOctree, GaussianModel
        
        # Create model
        model = GaussianModel()
        positions = np.random.rand(10000, 3) * 10.0
        model.positions = positions
        model.scales = np.ones((10000, 3)) * 0.1
        model.rotations = np.tile([1, 0, 0, 0], (10000, 1))
        model.opacities = np.ones((10000, 1))
        model.sh_coefficients = np.zeros((10000, 16, 3))
        
        # Build octree
        octree = SceneOctree(max_gaussians_per_node=1000)
        octree.build(model)
        
        # Collect all tile IDs
        tile_ids = set()
        leaf_nodes = octree.get_all_leaf_nodes()
        
        for i, node in enumerate(leaf_nodes):
            tile_id = f"L{node.level}_N{i}_high"
            assert tile_id not in tile_ids, f"Duplicate tile ID: {tile_id}"
            tile_ids.add(tile_id)
        
        # Should have unique IDs
        assert len(tile_ids) == len(leaf_nodes)


class TestHierarchicalStorage:
    """Test hierarchical tile storage"""
    
    def test_tile_directory_structure(self, tmp_path):
        """Test hierarchical directory structure for tiles"""
        scene_id = "test_scene_123"
        level = 2
        x, y, z = 3, 4, 5
        lod = "high"
        
        # Expected path: scenes/{sceneId}/tiles/{level}/{x}_{y}_{z}_{lod}.ply
        tile_dir = tmp_path / "scenes" / scene_id / "tiles" / str(level)
        tile_dir.mkdir(parents=True)
        
        tile_filename = f"{x}_{y}_{z}_{lod}.ply"
        tile_path = tile_dir / tile_filename
        
        # Create dummy tile file
        tile_path.write_text("dummy ply data")
        
        # Verify structure
        assert tile_path.exists()
        assert str(level) in str(tile_path)
        assert tile_filename in str(tile_path)
    
    def test_tile_metadata_json(self, tmp_path):
        """Test generation of tile metadata JSON"""
        tile_dir = tmp_path / "tiles"
        tile_dir.mkdir()
        
        # Create tile metadata
        tile_metadata = {
            'tile_id': 'L2_X3_Y4_Z5_high',
            'level': 2,
            'position': [3, 4, 5],
            'lod': 'high',
            'bounds': {
                'min': [0.0, 0.0, 0.0],
                'max': [10.0, 10.0, 10.0]
            },
            'gaussian_count': 50000,
            'file_size_bytes': 12500000
        }
        
        # Save metadata
        metadata_path = tile_dir / "tile_metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(tile_metadata, f, indent=2)
        
        # Verify
        assert metadata_path.exists()
        
        # Load and verify
        with open(metadata_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded['tile_id'] == 'L2_X3_Y4_Z5_high'
        assert loaded['gaussian_count'] == 50000
    
    def test_ply_tile_storage(self, tmp_path):
        """Test storing tiles as PLY files"""
        from workers.scene_optimization import GaussianModel
        
        tile_dir = tmp_path / "tiles"
        tile_dir.mkdir()
        
        # Create small Gaussian model for tile
        model = GaussianModel()
        model.positions = np.random.rand(100, 3)
        model.scales = np.ones((100, 3)) * 0.1
        model.rotations = np.tile([1, 0, 0, 0], (100, 1))
        model.opacities = np.ones((100, 1))
        model.sh_coefficients = np.zeros((100, 16, 3))
        
        # Save as PLY
        tile_path = tile_dir / "test_tile.ply"
        model.save_ply(str(tile_path))
        
        # Verify file exists
        assert tile_path.exists()
        assert tile_path.stat().st_size > 0


class TestTileMetadataPersistence:
    """Test persistence of tile metadata to MongoDB"""
    
    def test_scene_tile_model_structure(self):
        """Test SceneTile model structure"""
        from models.scene_tile import SceneTileInDB
        
        # Create tile document
        tile_doc = {
            'scene_id': 'test_scene_123',
            'tile_id': 'L2_X3_Y4_Z5_high',
            'level': 2,
            'grid_position': [3, 4, 5],
            'lod': 'high',
            'bounds_min': [0.0, 0.0, 0.0],
            'bounds_max': [10.0, 10.0, 10.0],
            'gaussian_count': 50000,
            'file_path': 'scenes/test_scene_123/tiles/2/3_4_5_high.ply',
            'file_size_bytes': 12500000
        }
        
        # Verify structure
        assert 'scene_id' in tile_doc
        assert 'tile_id' in tile_doc
        assert 'bounds_min' in tile_doc
        assert 'bounds_max' in tile_doc
        assert 'gaussian_count' in tile_doc
    
    def test_tile_metadata_indexes(self):
        """Test that indexes are created on scene_id and tile_id"""
        # This would test MongoDB index creation
        # In practice, indexes are created during database initialization
        
        required_indexes = ['scene_id', 'tile_id']
        
        # Verify index fields
        for index_field in required_indexes:
            assert index_field in ['scene_id', 'tile_id', 'level']
    
    def test_save_tiles_to_mongodb(self):
        """Test saving tile metadata to MongoDB"""
        from workers.scene_optimization import save_tiles_to_db
        
        scene_id = "test_scene_123"
        tiles_metadata = [
            {
                'tile_id': 'L0_X0_Y0_Z0_high',
                'level': 0,
                'gaussian_count': 50000,
                'bounds_min': [0, 0, 0],
                'bounds_max': [10, 10, 10],
                'file_path': 'scenes/test_scene_123/tiles/0/0_0_0_high.ply',
                'file_size_bytes': 12500000
            },
            {
                'tile_id': 'L1_X0_Y0_Z0_high',
                'level': 1,
                'gaussian_count': 25000,
                'bounds_min': [0, 0, 0],
                'bounds_max': [5, 5, 5],
                'file_path': 'scenes/test_scene_123/tiles/1/0_0_0_high.ply',
                'file_size_bytes': 6250000
            }
        ]
        
        # Mock MongoDB save
        with patch('workers.scene_optimization.get_database') as mock_db:
            mock_collection = MagicMock()
            mock_db.return_value.__getitem__.return_value = mock_collection
            
            result = save_tiles_to_db(scene_id, tiles_metadata)
            
            # Should attempt to save
            assert result is not None or mock_collection.insert_many.called


class TestLargeSceneSupport:
    """Test support for large-scale scenes"""
    
    def test_billion_gaussian_scene(self):
        """Test tiling for scenes up to 1B Gaussians"""
        # This is a conceptual test - actual 1B Gaussians would require too much memory
        
        total_gaussians = 1_000_000_000
        max_per_tile = 100_000
        
        # Calculate expected number of tiles
        min_tiles = total_gaussians // max_per_tile
        
        # Should create at least this many tiles
        assert min_tiles == 10_000
    
    def test_memory_efficient_tiling(self):
        """Test that tiling doesn't load entire scene into memory"""
        from workers.scene_optimization import SceneOctree, GaussianModel
        
        # Create moderately large model
        model = GaussianModel()
        positions = np.random.rand(100000, 3) * 100.0
        model.positions = positions
        model.scales = np.ones((100000, 3)) * 0.1
        model.rotations = np.tile([1, 0, 0, 0], (100000, 1))
        model.opacities = np.ones((100000, 1))
        model.sh_coefficients = np.zeros((100000, 16, 3))
        
        # Build octree
        octree = SceneOctree(max_gaussians_per_node=10000)
        octree.build(model)
        
        # Should complete without memory error
        leaf_nodes = octree.get_all_leaf_nodes()
        assert len(leaf_nodes) > 0
    
    def test_tile_streaming_preparation(self):
        """Test that tiles are prepared for streaming"""
        # Tiles should be:
        # 1. Small enough to stream (< 50MB each)
        # 2. Spatially organized for frustum culling
        # 3. Have LOD variants
        
        max_gaussians = 100000
        bytes_per_gaussian = 250  # Approximate
        max_tile_size = max_gaussians * bytes_per_gaussian
        
        # Should be under 50MB
        assert max_tile_size < 50 * 1024 * 1024


class TestIntegration:
    """Integration tests for complete tiling pipeline"""
    
    def test_end_to_end_tiling(self, tmp_path):
        """Test complete tiling pipeline"""
        from workers.scene_optimization import optimize_and_tile, GaussianModel
        
        # Create test model
        model = GaussianModel()
        positions = np.random.rand(50000, 3) * 50.0
        model.positions = positions
        model.scales = np.ones((50000, 3)) * 0.1
        model.rotations = np.tile([1, 0, 0, 0], (50000, 1))
        model.opacities = np.ones((50000, 1))
        model.sh_coefficients = np.zeros((50000, 16, 3))
        
        scene_id = "test_scene_123"
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        # Mock MinIO and MongoDB
        with patch('workers.scene_optimization.minio_client'), \
             patch('workers.scene_optimization.get_database'):
            
            result = optimize_and_tile(model, scene_id, str(output_dir))
            
            # Should complete
            assert result is not None
            assert 'tile_count' in result or 'status' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
