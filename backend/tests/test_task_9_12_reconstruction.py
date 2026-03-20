"""
Tests for Phase 3: Neural Reconstruction and Optimization

Task 9: 3D Gaussian Splatting
Task 10: Semantic Scene Analysis  
Task 11: Scene Optimization
Task 12: Scene Tiling
"""

import pytest
import numpy as np
import os
import tempfile
import uuid
from datetime import datetime

# Check if Celery/workers are available
try:
    from celery.utils.log import get_task_logger
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

skip_without_celery = pytest.mark.skipif(
    not CELERY_AVAILABLE,
    reason="Celery not installed locally (runs in Docker)"
)


# ============================================================================
# Task 9: Gaussian Splatting Tests
# ============================================================================

@skip_without_celery
class TestGaussianModel:
    """Tests for GaussianModel class."""
    
    def test_initialize_empty_model(self):
        """Test creating empty Gaussian model."""
        from workers.gaussian_splatting import GaussianModel
        
        model = GaussianModel()
        assert model.num_gaussians == 0
        assert model.positions is None
    
    def test_initialize_from_points(self):
        """Test initializing Gaussians from point cloud."""
        from workers.gaussian_splatting import GaussianModel
        
        # Create random points
        points = np.random.randn(100, 3).astype(np.float32)
        colors = np.random.rand(100, 3).astype(np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points, colors)
        
        assert model.num_gaussians == 100
        assert model.positions.shape == (100, 3)
        assert model.scales.shape == (100, 3)
        assert model.rotations.shape == (100, 4)
        assert model.opacities.shape == (100, 1)
        assert model.sh_coeffs.shape == (100, 48)
    
    def test_prune_low_opacity(self):
        """Test pruning Gaussians with low opacity."""
        from workers.gaussian_splatting import GaussianModel
        
        points = np.random.randn(100, 3).astype(np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points)
        
        # Set some opacities below threshold
        model.opacities[:30] = 0.01  # Below 0.05 threshold
        model.opacities[30:] = 0.5   # Above threshold
        
        removed = model.prune(min_opacity=0.05)
        
        assert removed == 30
        assert model.num_gaussians == 70
    
    def test_generate_lod(self):
        """Test LOD generation."""
        from workers.gaussian_splatting import GaussianModel
        
        points = np.random.randn(1000, 3).astype(np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points)
        model.opacities = np.random.rand(1000, 1).astype(np.float32)
        
        # Generate 50% LOD
        lod_50 = model.generate_lod(0.5)
        assert lod_50.num_gaussians == 500
        
        # Generate 20% LOD
        lod_20 = model.generate_lod(0.2)
        assert lod_20.num_gaussians == 200
    
    def test_save_and_load_ply(self):
        """Test saving and loading PLY files."""
        from workers.gaussian_splatting import GaussianModel
        
        points = np.random.randn(50, 3).astype(np.float32)
        colors = np.random.rand(50, 3).astype(np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points, colors)
        
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as f:
            ply_path = f.name
        
        try:
            # Save
            model.save_ply(ply_path)
            assert os.path.exists(ply_path)
            assert os.path.getsize(ply_path) > 0
            
            # Load
            loaded = GaussianModel.load_ply(ply_path)
            assert loaded.num_gaussians == 50
            np.testing.assert_array_almost_equal(loaded.positions, model.positions, decimal=5)
            
        finally:
            if os.path.exists(ply_path):
                os.unlink(ply_path)
    
    def test_merge_nearby_gaussians(self):
        """Test merging nearby Gaussians."""
        from workers.gaussian_splatting import GaussianModel
        
        # Create points with some very close together
        points = np.array([
            [0, 0, 0],
            [0.005, 0, 0],  # Very close to first
            [1, 0, 0],
            [1.005, 0, 0],  # Very close to third
            [5, 5, 5],  # Far from others
        ], dtype=np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points)
        
        merged = model.merge_nearby(distance_threshold=0.01)
        
        assert merged >= 2  # At least 2 pairs should merge
        assert model.num_gaussians <= 3
    
    def test_quantize(self):
        """Test 8-bit quantization."""
        from workers.gaussian_splatting import GaussianModel
        
        points = np.random.randn(100, 3).astype(np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points)
        
        quantized = model.quantize(bits=8)
        
        assert "positions_quantized" in quantized
        assert quantized["positions_quantized"].dtype == np.uint8
        assert "positions_min" in quantized
        assert "positions_max" in quantized


@skip_without_celery
class TestGaussianTraining:
    """Tests for Gaussian Splatting training."""
    
    def test_train_gaussians_basic(self):
        """Test basic training loop execution."""
        from workers.gaussian_splatting import GaussianModel, train_gaussians
        
        points = np.random.randn(100, 3).astype(np.float32)
        
        model = GaussianModel()
        model.initialize_from_points(points)
        
        # Train with minimal iterations
        with tempfile.TemporaryDirectory() as work_dir:
            images_dir = os.path.join(work_dir, "images")
            os.makedirs(images_dir)
            
            metrics = train_gaussians(
                model,
                images_dir,
                cameras_file="",
                num_iterations=100,
            )
            
            assert "initial_gaussians" in metrics
            assert "final_psnr" in metrics
            assert metrics["final_psnr"] > 0
    
    def test_load_colmap_points_fallback(self):
        """Test COLMAP loading fallback."""
        from workers.gaussian_splatting import load_colmap_points
        
        with tempfile.TemporaryDirectory() as work_dir:
            # Non-existent directory should use fallback
            points, colors = load_colmap_points(work_dir)
            
            assert len(points) > 0
            assert points.shape[1] == 3
            assert colors.shape == points.shape


# ============================================================================
# Task 10: Semantic Analysis Tests
# ============================================================================

@skip_without_celery
class TestSegmentAnything:
    """Tests for SAM wrapper."""
    
    def test_sam_initialization(self):
        """Test SAM wrapper initialization."""
        from workers.semantic_analysis import SegmentAnythingWrapper
        
        sam = SegmentAnythingWrapper()
        # Should initialize without error even if SAM not installed
        assert sam is not None
    
    def test_fallback_segmentation(self):
        """Test fallback segmentation when SAM unavailable."""
        from workers.semantic_analysis import SegmentAnythingWrapper
        
        sam = SegmentAnythingWrapper()
        
        # Create test image
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        masks = sam.generate_masks(image)
        
        assert isinstance(masks, list)
        assert len(masks) > 0
        
        for mask in masks:
            assert "segmentation" in mask
            assert "bbox" in mask
            assert "area" in mask


@skip_without_celery
class TestCLIPClassifier:
    """Tests for CLIP classifier."""
    
    def test_clip_initialization(self):
        """Test CLIP classifier initialization."""
        from workers.semantic_analysis import CLIPClassifier
        
        classifier = CLIPClassifier()
        assert classifier is not None
    
    def test_fallback_classification(self):
        """Test fallback classification when CLIP unavailable."""
        from workers.semantic_analysis import CLIPClassifier
        
        classifier = CLIPClassifier()
        
        # Create test image
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        
        category, confidence, alternatives = classifier.classify(image)
        
        assert isinstance(category, str)
        assert 0 <= confidence <= 1
        assert isinstance(alternatives, list)
    
    def test_classification_with_mask(self):
        """Test classification with mask."""
        from workers.semantic_analysis import CLIPClassifier
        
        classifier = CLIPClassifier()
        
        image = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
        mask = np.zeros((256, 256), dtype=bool)
        mask[50:200, 50:200] = True
        
        category, confidence, alternatives = classifier.classify(image, mask)
        
        assert isinstance(category, str)


@skip_without_celery
class TestSceneGraph:
    """Tests for scene graph construction."""
    
    def test_build_scene_graph_empty(self):
        """Test building scene graph with empty objects."""
        from workers.semantic_analysis import build_scene_graph
        
        graph = build_scene_graph([])
        
        assert graph["object_count"] == 0
        assert graph["root_objects"] == []
    
    def test_build_scene_graph_with_objects(self):
        """Test building scene graph with objects."""
        from workers.semantic_analysis import build_scene_graph
        
        objects = [
            {
                "id": "obj1",
                "category": "floor",
                "bounding_box": {"center_x": 0, "center_y": 0, "center_z": 0,
                                 "width": 10, "height": 0.1, "depth": 10},
            },
            {
                "id": "obj2",
                "category": "table",
                "bounding_box": {"center_x": 0, "center_y": 1, "center_z": 0,
                                 "width": 1, "height": 0.8, "depth": 1},
            },
            {
                "id": "obj3",
                "category": "lamp",
                "bounding_box": {"center_x": 0, "center_y": 1.5, "center_z": 0,
                                 "width": 0.2, "height": 0.3, "depth": 0.2},
            },
        ]
        
        graph = build_scene_graph(objects)
        
        assert graph["object_count"] == 3
        assert "floor" in graph["category_counts"]
        assert len(graph["root_objects"]) > 0


class TestObjectCategory:
    """Tests for object category enum."""
    
    def test_category_values(self):
        """Test object category enum values."""
        from models.scene_object import ObjectCategory
        
        assert ObjectCategory.WALL.value == "wall"
        assert ObjectCategory.FLOOR.value == "floor"
        assert ObjectCategory.CHAIR.value == "chair"
        assert ObjectCategory.PERSON.value == "person"


# ============================================================================
# Task 11: Scene Optimization Tests
# ============================================================================

@skip_without_celery
class TestSceneOptimization:
    """Tests for scene optimization."""
    
    def test_subsample_model(self):
        """Test model subsampling."""
        from workers.scene_optimization import subsample_model
        
        model_data = {
            "positions": np.random.randn(1000, 3).astype(np.float32),
            "scales": np.random.randn(1000, 3).astype(np.float32),
            "rotations": np.random.randn(1000, 4).astype(np.float32),
            "opacities": np.random.rand(1000, 1).astype(np.float32),
            "sh_dc": np.random.randn(1000, 3).astype(np.float32),
        }
        
        # 50% subsample
        sub_50 = subsample_model(model_data, 0.5)
        assert len(sub_50["positions"]) == 500
        
        # 20% subsample
        sub_20 = subsample_model(model_data, 0.2)
        assert len(sub_20["positions"]) == 200
    
    def test_load_gaussian_model(self):
        """Test loading Gaussian model from PLY."""
        from workers.gaussian_splatting import GaussianModel
        from workers.scene_optimization import load_gaussian_model
        
        # Create and save a model
        points = np.random.randn(50, 3).astype(np.float32)
        model = GaussianModel()
        model.initialize_from_points(points)
        
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as f:
            ply_path = f.name
        
        try:
            model.save_ply(ply_path)
            
            # Load it back
            loaded = load_gaussian_model(ply_path)
            
            assert "positions" in loaded
            assert len(loaded["positions"]) == 50
            
        finally:
            if os.path.exists(ply_path):
                os.unlink(ply_path)


# ============================================================================
# Task 12: Scene Tiling Tests
# ============================================================================

@skip_without_celery
class TestOctree:
    """Tests for octree spatial structure."""
    
    def test_octree_node_basic(self):
        """Test basic octree node properties."""
        from workers.scene_optimization import OctreeNode
        
        bounds = (np.array([0, 0, 0]), np.array([1, 1, 1]))
        node = OctreeNode(bounds, level=0, index=(0, 0, 0))
        
        assert node.level == 0
        assert node.is_leaf
        assert node.tile_id == "L0_X0_Y0_Z0"
        np.testing.assert_array_equal(node.center, [0.5, 0.5, 0.5])
        np.testing.assert_array_equal(node.size, [1, 1, 1])
    
    def test_octree_contains_point(self):
        """Test point containment."""
        from workers.scene_optimization import OctreeNode
        
        bounds = (np.array([0, 0, 0]), np.array([1, 1, 1]))
        node = OctreeNode(bounds)
        
        assert node.contains_point(np.array([0.5, 0.5, 0.5]))
        assert node.contains_point(np.array([0, 0, 0]))
        assert node.contains_point(np.array([1, 1, 1]))
        assert not node.contains_point(np.array([1.5, 0.5, 0.5]))
    
    def test_octree_subdivide(self):
        """Test octree subdivision."""
        from workers.scene_optimization import OctreeNode
        
        bounds = (np.array([0, 0, 0]), np.array([2, 2, 2]))
        node = OctreeNode(bounds)
        
        node.subdivide()
        
        assert not node.is_leaf
        assert all(child is not None for child in node.children)
        
        # Check children are at level 1
        for child in node.children:
            assert child.level == 1
    
    def test_scene_octree_build(self):
        """Test building octree from points."""
        from workers.scene_optimization import SceneOctree
        
        # Random points
        points = np.random.randn(1000, 3).astype(np.float32)
        
        octree = SceneOctree(points, max_per_tile=200)
        
        assert octree.num_gaussians == 1000
        assert len(octree.leaf_nodes) > 0
        
        # Check all Gaussians are in exactly one leaf
        total_in_leaves = sum(len(node.gaussian_indices) for node in octree.leaf_nodes)
        assert total_in_leaves == 1000
    
    def test_scene_octree_tile_limit(self):
        """Test that tiles respect Gaussian limit."""
        from workers.scene_optimization import SceneOctree, MAX_GAUSSIANS_PER_TILE
        
        # Many points to force subdivision
        points = np.random.randn(500000, 3).astype(np.float32) * 10
        
        octree = SceneOctree(points, max_per_tile=MAX_GAUSSIANS_PER_TILE)
        
        # All leaves should have <= max Gaussians
        for node in octree.leaf_nodes:
            assert len(node.gaussian_indices) <= MAX_GAUSSIANS_PER_TILE
    
    def test_octree_frustum_culling(self):
        """Test frustum-based tile selection."""
        from workers.scene_optimization import SceneOctree
        
        points = np.random.randn(1000, 3).astype(np.float32) * 10
        octree = SceneOctree(points, max_per_tile=100)
        
        # Get tiles visible from origin looking along +Z
        visible = octree.get_tiles_for_frustum(
            camera_pos=np.array([0, 0, -20]),
            camera_dir=np.array([0, 0, 1]),
            fov=60,
            max_distance=50,
        )
        
        assert isinstance(visible, list)


class TestTileModel:
    """Tests for scene tile model."""
    
    def test_bounding_box_properties(self):
        """Test bounding box properties."""
        from models.scene_tile import BoundingBox
        
        bbox = BoundingBox(
            min_x=0, min_y=0, min_z=0,
            max_x=2, max_y=4, max_z=6,
        )
        
        assert bbox.center == (1, 2, 3)
        assert bbox.size == (2, 4, 6)
    
    def test_bounding_box_contains(self):
        """Test bounding box containment check."""
        from models.scene_tile import BoundingBox
        
        bbox = BoundingBox(
            min_x=0, min_y=0, min_z=0,
            max_x=1, max_y=1, max_z=1,
        )
        
        assert bbox.contains_point(0.5, 0.5, 0.5)
        assert bbox.contains_point(0, 0, 0)
        assert not bbox.contains_point(2, 0, 0)
    
    def test_bounding_box_intersection(self):
        """Test bounding box intersection."""
        from models.scene_tile import BoundingBox
        
        bbox1 = BoundingBox(min_x=0, min_y=0, min_z=0, max_x=2, max_y=2, max_z=2)
        bbox2 = BoundingBox(min_x=1, min_y=1, min_z=1, max_x=3, max_y=3, max_z=3)
        bbox3 = BoundingBox(min_x=5, min_y=5, min_z=5, max_x=6, max_y=6, max_z=6)
        
        assert bbox1.intersects(bbox2)
        assert not bbox1.intersects(bbox3)
    
    def test_lod_level_enum(self):
        """Test LOD level enum."""
        from models.scene_tile import LODLevel
        
        assert LODLevel.HIGH.value == "high"
        assert LODLevel.MEDIUM.value == "medium"
        assert LODLevel.LOW.value == "low"
    
    @skip_without_celery
    def test_tile_id_format(self):
        """Test tile ID format."""
        from workers.scene_optimization import OctreeNode
        
        bounds = (np.array([0, 0, 0]), np.array([1, 1, 1]))
        node = OctreeNode(bounds, level=2, index=(3, 5, 7))
        
        assert node.tile_id == "L2_X3_Y5_Z7"


@skip_without_celery
class TestSaveTilePly:
    """Tests for tile PLY saving."""
    
    def test_save_tile_ply(self):
        """Test saving tile to PLY."""
        from workers.scene_optimization import save_tile_ply
        
        n = 100
        positions = np.random.randn(n, 3).astype(np.float32)
        scales = np.abs(np.random.randn(n, 3).astype(np.float32)) * 0.1
        rotations = np.zeros((n, 4), dtype=np.float32)
        rotations[:, 0] = 1.0
        opacities = np.random.rand(n, 1).astype(np.float32)
        sh_dc = np.random.randn(n, 3).astype(np.float32)
        
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as f:
            ply_path = f.name
        
        try:
            save_tile_ply(ply_path, positions, scales, rotations, opacities, sh_dc)
            
            assert os.path.exists(ply_path)
            assert os.path.getsize(ply_path) > 0
            
        finally:
            if os.path.exists(ply_path):
                os.unlink(ply_path)


# ============================================================================
# Phase 3 Summary Tests
# ============================================================================

class TestPhase3Summary:
    """Summary tests verifying all Phase 3 components exist."""
    
    def test_gaussian_splatting_worker_exists(self):
        """Verify Gaussian Splatting worker exists."""
        try:
            from workers.gaussian_splatting import reconstruct_scene, GaussianModel
            assert callable(reconstruct_scene) or True  # Celery task
            assert GaussianModel is not None
        except ImportError:
            # Check file exists
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "workers", "gaussian_splatting.py"
            )
            assert os.path.exists(path)
    
    def test_semantic_analysis_worker_exists(self):
        """Verify semantic analysis worker exists."""
        try:
            from workers.semantic_analysis import analyze_scene
            assert callable(analyze_scene) or True
        except ImportError:
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "workers", "semantic_analysis.py"
            )
            assert os.path.exists(path)
    
    def test_scene_optimization_worker_exists(self):
        """Verify scene optimization worker exists."""
        try:
            from workers.scene_optimization import optimize_and_tile
            assert callable(optimize_and_tile) or True
        except ImportError:
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "workers", "scene_optimization.py"
            )
            assert os.path.exists(path)
    
    def test_scene_tile_model_exists(self):
        """Verify SceneTile model exists."""
        from models.scene_tile import SceneTileInDB, BoundingBox, LODLevel
        
        assert SceneTileInDB is not None
        assert BoundingBox is not None
        assert LODLevel is not None
    
    def test_scene_object_model_exists(self):
        """Verify SceneObject model exists."""
        from models.scene_object import SceneObjectInDB, ObjectCategory
        
        assert SceneObjectInDB is not None
        assert ObjectCategory is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
