"""
Tests for Task 18.8: Streaming Engine

Tests cover:
- Frustum culling accuracy (Requirement 10.1)
- Distance-based prioritization (Requirement 10.2)
- LOD selection logic (Requirement 10.3)
- Bandwidth adaptation (Requirement 10.6)
- Caching performance (Requirement 10.5, 10.7)
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from typing import List

from api.tiles import (
    normalize_vector,
    point_in_frustum,
    bbox_in_frustum,
    select_lod_by_distance,
    calculate_tile_priority,
    TileRequest,
    CameraParams,
)
from models.scene_tile import SceneTileInDB, BoundingBox, LODLevel


def create_mock_cursor(tiles_data):
    """Create a properly mocked async cursor for MongoDB."""
    mock_cursor = AsyncMock()
    mock_cursor.to_list = AsyncMock(return_value=tiles_data)
    return mock_cursor


# ============================================================================
# Helper Functions
# ============================================================================

def create_test_tile(
    tile_id: str,
    scene_id: str,
    level: int,
    x: int,
    y: int,
    z: int,
    lod: str,
    bbox_min: tuple,
    bbox_max: tuple,
    gaussian_count: int = 50000,
) -> SceneTileInDB:
    """Create a test tile with specified parameters."""
    return SceneTileInDB(
        _id=tile_id,
        scene_id=scene_id,
        organization_id="test-org",
        level=level,
        x=x,
        y=y,
        z=z,
        lod=lod,
        bounding_box=BoundingBox(
            min_x=bbox_min[0],
            min_y=bbox_min[1],
            min_z=bbox_min[2],
            max_x=bbox_max[0],
            max_y=bbox_max[1],
            max_z=bbox_max[2],
        ),
        gaussian_count=gaussian_count,
        file_size_bytes=gaussian_count * 100,  # Approximate
        file_path=f"scenes/{scene_id}/tiles/{level}/{x}_{y}_{z}_{lod}.ply",
        created_at=datetime.utcnow(),
    )


# ============================================================================
# Test Frustum Culling (Requirement 10.1)
# ============================================================================

class TestFrustumCulling:
    """Test frustum culling accuracy."""
    
    def test_normalize_vector(self):
        """Test vector normalization."""
        v = np.array([3.0, 4.0, 0.0])
        normalized = normalize_vector(v)
        
        assert np.allclose(np.linalg.norm(normalized), 1.0)
        assert np.allclose(normalized, [0.6, 0.8, 0.0])
    
    def test_normalize_zero_vector(self):
        """Test normalization of zero vector."""
        v = np.array([0.0, 0.0, 0.0])
        normalized = normalize_vector(v)
        
        assert np.allclose(normalized, [0.0, 0.0, 0.0])
    
    def test_point_in_frustum_center(self):
        """Test point directly in front of camera is in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        point = np.array([0.0, 0.0, 10.0])
        
        result = point_in_frustum(point, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result == True
    
    def test_point_in_frustum_outside_fov(self):
        """Test point outside FOV is not in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        point = np.array([50.0, 0.0, 10.0])  # 90 degrees off, outside 60 degree FOV
        
        result = point_in_frustum(point, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result == False
    
    def test_point_in_frustum_too_close(self):
        """Test point closer than near plane is not in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        point = np.array([0.0, 0.0, 0.05])  # Closer than near=0.1
        
        result = point_in_frustum(point, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result is False
    
    def test_point_in_frustum_too_far(self):
        """Test point farther than far plane is not in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        point = np.array([0.0, 0.0, 150.0])  # Farther than far=100
        
        result = point_in_frustum(point, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result is False
    
    def test_point_in_frustum_at_edge(self):
        """Test point at edge of FOV is in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        # Point at 30 degrees (half of 60 degree FOV)
        distance = 10.0
        angle_rad = np.radians(29)  # Just inside
        point = np.array([distance * np.sin(angle_rad), 0.0, distance * np.cos(angle_rad)])
        
        result = point_in_frustum(point, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result == True
    
    def test_bbox_in_frustum_fully_visible(self):
        """Test bounding box fully in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        bbox = {
            "min_x": -1.0, "min_y": -1.0, "min_z": 9.0,
            "max_x": 1.0, "max_y": 1.0, "max_z": 11.0,
        }
        
        result = bbox_in_frustum(bbox, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result == True
    
    def test_bbox_in_frustum_behind_camera(self):
        """Test bounding box behind camera is not in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        bbox = {
            "min_x": -1.0, "min_y": -1.0, "min_z": -11.0,
            "max_x": 1.0, "max_y": 1.0, "max_z": -9.0,
        }
        
        result = bbox_in_frustum(bbox, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result == False
    
    def test_bbox_in_frustum_partially_visible(self):
        """Test bounding box partially in frustum is included."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        # Large bbox that extends outside FOV but center is visible
        bbox = {
            "min_x": -5.0, "min_y": -5.0, "min_z": 8.0,
            "max_x": 5.0, "max_y": 5.0, "max_z": 12.0,
        }
        
        result = bbox_in_frustum(bbox, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result == True
    
    def test_bbox_in_frustum_too_far(self):
        """Test bounding box beyond far plane is not in frustum."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        bbox = {
            "min_x": -1.0, "min_y": -1.0, "min_z": 150.0,
            "max_x": 1.0, "max_y": 1.0, "max_z": 160.0,
        }
        
        result = bbox_in_frustum(bbox, camera_pos, camera_dir, fov=60, near=0.1, far=100)
        
        assert result is False


# ============================================================================
# Test Distance-Based Prioritization (Requirement 10.2)
# ============================================================================

class TestDistancePrioritization:
    """Test distance-based tile prioritization."""
    
    def test_calculate_tile_priority_close_tile(self):
        """Test that closer tiles get higher priority."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        # Close tile
        tile = create_test_tile(
            "L0_X0_Y0_Z0_high", "scene1", 0, 0, 0, 0, "high",
            bbox_min=(0.0, 0.0, 5.0),
            bbox_max=(2.0, 2.0, 7.0),
        )
        
        priority = calculate_tile_priority(tile, camera_pos, camera_dir)
        
        # Close tile should have high priority (> 0.5)
        assert priority > 0.5
    
    def test_calculate_tile_priority_far_tile(self):
        """Test that farther tiles get lower priority."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        # Far tile
        tile = create_test_tile(
            "L0_X0_Y0_Z0_high", "scene1", 0, 0, 0, 0, "high",
            bbox_min=(0.0, 0.0, 90.0),
            bbox_max=(2.0, 2.0, 92.0),
        )
        
        priority = calculate_tile_priority(tile, camera_pos, camera_dir)
        
        # Far tile should have low priority (< 0.5)
        assert priority < 0.5
    
    def test_calculate_tile_priority_ordering(self):
        """Test that tiles are correctly ordered by distance."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        # Create tiles at different distances
        tile_close = create_test_tile(
            "L0_X0_Y0_Z0_high", "scene1", 0, 0, 0, 0, "high",
            bbox_min=(0.0, 0.0, 5.0),
            bbox_max=(2.0, 2.0, 7.0),
        )
        
        tile_medium = create_test_tile(
            "L0_X0_Y0_Z1_high", "scene1", 0, 0, 0, 1, "high",
            bbox_min=(0.0, 0.0, 15.0),
            bbox_max=(2.0, 2.0, 17.0),
        )
        
        tile_far = create_test_tile(
            "L0_X0_Y0_Z2_high", "scene1", 0, 0, 0, 2, "high",
            bbox_min=(0.0, 0.0, 50.0),
            bbox_max=(2.0, 2.0, 52.0),
        )
        
        priority_close = calculate_tile_priority(tile_close, camera_pos, camera_dir)
        priority_medium = calculate_tile_priority(tile_medium, camera_pos, camera_dir)
        priority_far = calculate_tile_priority(tile_far, camera_pos, camera_dir)
        
        # Verify ordering: close > medium > far
        assert priority_close > priority_medium > priority_far
    
    def test_calculate_tile_priority_direction_alignment(self):
        """Test that tiles aligned with camera direction get higher priority."""
        camera_pos = np.array([0.0, 0.0, 0.0])
        camera_dir = np.array([0.0, 0.0, 1.0])
        
        # Tile directly ahead
        tile_ahead = create_test_tile(
            "L0_X0_Y0_Z0_high", "scene1", 0, 0, 0, 0, "high",
            bbox_min=(0.0, 0.0, 10.0),
            bbox_max=(2.0, 2.0, 12.0),
        )
        
        # Tile to the side (same distance)
        tile_side = create_test_tile(
            "L0_X1_Y0_Z0_high", "scene1", 0, 1, 0, 0, "high",
            bbox_min=(10.0, 0.0, 1.0),
            bbox_max=(12.0, 2.0, 3.0),
        )
        
        priority_ahead = calculate_tile_priority(tile_ahead, camera_pos, camera_dir)
        priority_side = calculate_tile_priority(tile_side, camera_pos, camera_dir)
        
        # Tile ahead should have higher priority
        assert priority_ahead > priority_side


# ============================================================================
# Test LOD Selection Logic (Requirement 10.3)
# ============================================================================

class TestLODSelection:
    """Test LOD selection based on distance and bandwidth."""
    
    def test_select_lod_close_distance(self):
        """Test high LOD selected for close distances."""
        lod = select_lod_by_distance(distance=3.0)
        assert lod == "high"
    
    def test_select_lod_medium_distance(self):
        """Test medium LOD selected for medium distances."""
        lod = select_lod_by_distance(distance=10.0)
        assert lod == "medium"
    
    def test_select_lod_far_distance(self):
        """Test low LOD selected for far distances."""
        lod = select_lod_by_distance(distance=50.0)
        assert lod == "low"
    
    def test_select_lod_distance_thresholds(self):
        """Test LOD selection at threshold boundaries."""
        # Just below 5m threshold
        assert select_lod_by_distance(4.9) == "high"
        # Just above 5m threshold
        assert select_lod_by_distance(5.1) == "medium"
        
        # Just below 20m threshold
        assert select_lod_by_distance(19.9) == "medium"
        # Just above 20m threshold
        assert select_lod_by_distance(20.1) == "low"
    
    def test_select_lod_with_good_bandwidth(self):
        """Test LOD selection with good bandwidth (no downgrade)."""
        # Good bandwidth should not affect LOD selection
        lod = select_lod_by_distance(distance=3.0, bandwidth_mbps=10.0)
        assert lod == "high"
    
    def test_select_lod_with_low_bandwidth_close(self):
        """Test bandwidth downgrade for close tiles."""
        # Low bandwidth should downgrade even close tiles
        lod = select_lod_by_distance(distance=3.0, bandwidth_mbps=3.0)
        assert lod == "medium"
    
    def test_select_lod_with_low_bandwidth_far(self):
        """Test bandwidth downgrade for far tiles."""
        # Low bandwidth should use low LOD for far tiles
        lod = select_lod_by_distance(distance=15.0, bandwidth_mbps=3.0)
        assert lod == "low"


# ============================================================================
# Test Bandwidth Adaptation (Requirement 10.6)
# ============================================================================

class TestBandwidthAdaptation:
    """Test bandwidth-based quality adaptation."""
    
    def test_bandwidth_threshold_5mbps(self):
        """Test that 5 Mbps is the threshold for quality reduction."""
        # Just above threshold - no downgrade
        lod_above = select_lod_by_distance(distance=3.0, bandwidth_mbps=5.1)
        assert lod_above == "high"
        
        # Just below threshold - downgrade
        lod_below = select_lod_by_distance(distance=3.0, bandwidth_mbps=4.9)
        assert lod_below == "medium"
    
    def test_bandwidth_adaptation_maintains_framerate(self):
        """Test that low bandwidth reduces quality to maintain performance."""
        # With low bandwidth, all tiles should use lower LOD
        distances = [3.0, 10.0, 50.0]
        bandwidth = 2.0
        
        lods = [select_lod_by_distance(d, bandwidth) for d in distances]
        
        # All should be medium or low
        assert all(lod in ["medium", "low"] for lod in lods)
    
    def test_bandwidth_none_uses_distance_only(self):
        """Test that None bandwidth uses distance-based selection only."""
        lod = select_lod_by_distance(distance=3.0, bandwidth_mbps=None)
        assert lod == "high"


# ============================================================================
# Test Caching Performance (Requirements 10.5, 10.7)
# ============================================================================

class TestCachingPerformance:
    """Test tile caching with Valkey."""
    
    @pytest.mark.asyncio
    async def test_cache_hit_performance(self):
        """Test that cached tiles respond within 100ms (Requirement 10.7)."""
        import time
        from unittest.mock import patch, AsyncMock, MagicMock
        
        # Mock Valkey with cached data
        mock_valkey = MagicMock()
        mock_valkey.get_bytes.return_value = b"cached_tile_data"
        
        # Mock database
        mock_db = AsyncMock()
        mock_db.scenes.find_one.return_value = {
            "_id": "scene1",
            "organization_id": "org1",
        }
        mock_db.scene_tiles.find_one.return_value = {
            "_id": "tile1",
            "scene_id": "scene1",
            "organization_id": "org1",
            "level": 0,
            "x": 0,
            "y": 0,
            "z": 0,
            "lod": "high",
            "bounding_box": {
                "min_x": 0.0, "min_y": 0.0, "min_z": 0.0,
                "max_x": 10.0, "max_y": 10.0, "max_z": 10.0,
            },
            "gaussian_count": 50000,
            "file_size_bytes": 5000000,
            "file_path": "scenes/scene1/tiles/0/0_0_0_high.ply",
            "created_at": datetime.utcnow(),
        }
        
        with patch("utils.valkey_client.get_valkey_client", return_value=mock_valkey):
            from api.tiles import download_tile
            from models.user import UserInDB
            
            # Mock user
            mock_user = UserInDB(
                _id="user1",
                email="test@example.com",
                full_name="Test User",
                hashed_password="hashed",
                organization_id="org1",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            # Measure response time
            start_time = time.time()
            response = await download_tile("scene1", "tile1", mock_user, mock_db)
            elapsed_ms = (time.time() - start_time) * 1000
            
            # Should be well under 100ms for cache hit
            assert elapsed_ms < 100
            assert response.headers["X-Cache"] == "HIT"
    
    @pytest.mark.asyncio
    async def test_cache_ttl_one_hour(self):
        """Test that tiles are cached for 1 hour (Requirement 10.5)."""
        from unittest.mock import patch, AsyncMock, MagicMock
        
        mock_valkey = MagicMock()
        mock_valkey.get_bytes.return_value = None  # Cache miss
        mock_valkey.set_bytes = MagicMock()
        
        mock_minio = MagicMock()
        mock_minio.download_file = MagicMock()
        
        mock_db = AsyncMock()
        mock_db.scenes.find_one.return_value = {
            "_id": "scene1",
            "organization_id": "org1",
        }
        mock_db.scene_tiles.find_one.return_value = {
            "_id": "tile1",
            "scene_id": "scene1",
            "organization_id": "org1",
            "level": 0,
            "x": 0,
            "y": 0,
            "z": 0,
            "lod": "high",
            "bounding_box": {
                "min_x": 0.0, "min_y": 0.0, "min_z": 0.0,
                "max_x": 10.0, "max_y": 10.0, "max_z": 10.0,
            },
            "gaussian_count": 50000,
            "file_size_bytes": 5000000,
            "file_path": "scenes/scene1/tiles/0/0_0_0_high.ply",
            "created_at": datetime.utcnow(),
        }
        
        with patch("utils.valkey_client.get_valkey_client", return_value=mock_valkey), \
             patch("utils.minio_client.get_minio_client", return_value=mock_minio), \
             patch("builtins.open", create=True) as mock_open:
            
            # Mock file read
            mock_file = MagicMock()
            mock_file.read.return_value = b"tile_data"
            mock_file.__enter__.return_value = mock_file
            mock_open.return_value = mock_file
            
            from api.tiles import download_tile
            from models.user import UserInDB
            
            mock_user = UserInDB(
                _id="user1",
                email="test@example.com",
                full_name="Test User",
                hashed_password="hashed",
                organization_id="org1",
                is_active=True,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            
            await download_tile("scene1", "tile1", mock_user, mock_db)
            
            # Verify cache was set with 1 hour TTL (3600 seconds)
            mock_valkey.set_bytes.assert_called_once()
            call_args = mock_valkey.set_bytes.call_args
            assert call_args[1]["ttl"] == 3600


# ============================================================================
# Test Integration: Full Tile Request Flow
# ============================================================================

class TestTileRequestIntegration:
    """Test complete tile request flow."""
    
    @pytest.mark.asyncio
    async def test_get_scene_tiles_basic(self):
        """Test basic tile request with frustum culling and prioritization."""
        from unittest.mock import AsyncMock
        from api.tiles import get_scene_tiles
        from models.user import UserInDB
        
        # Mock database
        mock_db = AsyncMock()
        mock_db.scenes.find_one.return_value = {
            "_id": "scene1",
            "organization_id": "org1",
        }
        
        # Create test tiles
        tiles = [
            # Tile in front of camera (should be visible)
            {
                "_id": "L0_X0_Y0_Z0_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 0,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": 9.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": 11.0,
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": "scenes/scene1/tiles/0/0_0_0_high.ply",
                "created_at": datetime.utcnow(),
            },
            # Tile behind camera (should not be visible)
            {
                "_id": "L0_X0_Y0_Z1_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 1,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": -11.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": -9.0,
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": "scenes/scene1/tiles/0/0_0_1_high.ply",
                "created_at": datetime.utcnow(),
            },
        ]
        
        mock_cursor = create_mock_cursor(tiles)
        mock_db.scene_tiles.find = MagicMock(return_value=mock_cursor)
        
        # Mock user
        mock_user = UserInDB(
            _id="user1",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed",
            organization_id="org1",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Create request
        request = TileRequest(
            camera=CameraParams(
                position=[0.0, 0.0, 0.0],
                direction=[0.0, 0.0, 1.0],
                fov=60,
                near=0.1,
                far=100,
            ),
            bandwidth_mbps=10.0,
            max_tiles=50,
        )
        
        # Execute
        response = await get_scene_tiles("scene1", request, mock_user, mock_db)
        
        # Verify only visible tile is returned
        assert len(response.tiles) == 1
        assert response.tiles[0].tile_id == "L0_X0_Y0_Z0_high"
        assert response.total_tiles == 2
    
    @pytest.mark.asyncio
    async def test_get_scene_tiles_with_low_bandwidth(self):
        """Test tile request with low bandwidth adaptation."""
        from unittest.mock import AsyncMock
        from api.tiles import get_scene_tiles
        from models.user import UserInDB
        
        mock_db = AsyncMock()
        mock_db.scenes.find_one.return_value = {
            "_id": "scene1",
            "organization_id": "org1",
        }
        
        # Create tiles with different LODs
        tiles = [
            {
                "_id": "L0_X0_Y0_Z0_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 0,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": 9.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": 11.0,
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": "scenes/scene1/tiles/0/0_0_0_high.ply",
                "created_at": datetime.utcnow(),
            },
            {
                "_id": "L0_X0_Y0_Z0_low",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 0,
                "lod": "low",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": 9.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": 11.0,
                },
                "gaussian_count": 10000,
                "file_size_bytes": 1000000,
                "file_path": "scenes/scene1/tiles/0/0_0_0_low.ply",
                "created_at": datetime.utcnow(),
            },
        ]
        
        mock_cursor = create_mock_cursor(tiles)
        mock_db.scene_tiles.find = MagicMock(return_value=mock_cursor)
        
        mock_user = UserInDB(
            _id="user1",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed",
            organization_id="org1",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        # Request with low bandwidth
        request = TileRequest(
            camera=CameraParams(
                position=[0.0, 0.0, 0.0],
                direction=[0.0, 0.0, 1.0],
                fov=60,
                near=0.1,
                far=100,
            ),
            bandwidth_mbps=3.0,  # Low bandwidth
            max_tiles=50,
        )
        
        response = await get_scene_tiles("scene1", request, mock_user, mock_db)
        
        # Should return low LOD tile due to bandwidth
        assert len(response.tiles) == 1
        assert response.tiles[0].lod == "low"
        assert response.bandwidth_adjusted is True
        assert response.selected_lod == "low"
    
    @pytest.mark.asyncio
    async def test_get_scene_tiles_priority_ordering(self):
        """Test that tiles are returned in priority order."""
        from unittest.mock import AsyncMock
        from api.tiles import get_scene_tiles
        from models.user import UserInDB
        
        mock_db = AsyncMock()
        mock_db.scenes.find_one.return_value = {
            "_id": "scene1",
            "organization_id": "org1",
        }
        
        # Create tiles at different distances
        tiles = [
            # Far tile
            {
                "_id": "L0_X0_Y0_Z0_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 0,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": 49.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": 51.0,
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": "scenes/scene1/tiles/0/0_0_0_high.ply",
                "created_at": datetime.utcnow(),
            },
            # Close tile
            {
                "_id": "L0_X0_Y0_Z1_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 1,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": 4.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": 6.0,
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": "scenes/scene1/tiles/0/0_0_1_high.ply",
                "created_at": datetime.utcnow(),
            },
            # Medium distance tile
            {
                "_id": "L0_X0_Y0_Z2_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": 2,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": 19.0,
                    "max_x": 1.0, "max_y": 1.0, "max_z": 21.0,
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": "scenes/scene1/tiles/0/0_0_2_high.ply",
                "created_at": datetime.utcnow(),
            },
        ]
        
        mock_cursor = create_mock_cursor(tiles)
        mock_db.scene_tiles.find = MagicMock(return_value=mock_cursor)
        
        mock_user = UserInDB(
            _id="user1",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed",
            organization_id="org1",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        request = TileRequest(
            camera=CameraParams(
                position=[0.0, 0.0, 0.0],
                direction=[0.0, 0.0, 1.0],
                fov=60,
                near=0.1,
                far=100,
            ),
            bandwidth_mbps=10.0,
            max_tiles=50,
        )
        
        response = await get_scene_tiles("scene1", request, mock_user, mock_db)
        
        # Should return all 3 tiles in priority order (close to far)
        assert len(response.tiles) == 3
        
        # Verify ordering by checking distances
        distances = [tile.distance for tile in response.tiles]
        assert distances == sorted(distances)  # Should be in ascending order
        
        # First tile should be the closest
        assert response.tiles[0].tile_id == "L0_X0_Y0_Z1_high"
    
    @pytest.mark.asyncio
    async def test_get_scene_tiles_max_tiles_limit(self):
        """Test that max_tiles parameter limits results."""
        from unittest.mock import AsyncMock
        from api.tiles import get_scene_tiles
        from models.user import UserInDB
        
        mock_db = AsyncMock()
        mock_db.scenes.find_one.return_value = {
            "_id": "scene1",
            "organization_id": "org1",
        }
        
        # Create many tiles
        tiles = []
        for i in range(10):
            tiles.append({
                "_id": f"L0_X0_Y0_Z{i}_high",
                "scene_id": "scene1",
                "organization_id": "org1",
                "level": 0,
                "x": 0,
                "y": 0,
                "z": i,
                "lod": "high",
                "bounding_box": {
                    "min_x": -1.0, "min_y": -1.0, "min_z": float(i * 10),
                    "max_x": 1.0, "max_y": 1.0, "max_z": float(i * 10 + 2),
                },
                "gaussian_count": 50000,
                "file_size_bytes": 5000000,
                "file_path": f"scenes/scene1/tiles/0/0_0_{i}_high.ply",
                "created_at": datetime.utcnow(),
            })
        
        mock_cursor = AsyncMock()
        mock_cursor.to_list.return_value = tiles
        mock_db.scene_tiles.find.return_value = mock_cursor
        
        mock_user = UserInDB(
            _id="user1",
            email="test@example.com",
            full_name="Test User",
            hashed_password="hashed",
            organization_id="org1",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        request = TileRequest(
            camera=CameraParams(
                position=[0.0, 0.0, 0.0],
                direction=[0.0, 0.0, 1.0],
                fov=60,
                near=0.1,
                far=100,
            ),
            bandwidth_mbps=10.0,
            max_tiles=5,  # Limit to 5 tiles
        )
        
        response = await get_scene_tiles("scene1", request, mock_user, mock_db)
        
        # Should return only 5 tiles (the highest priority ones)
        assert len(response.tiles) <= 5
        assert response.total_tiles == 10
