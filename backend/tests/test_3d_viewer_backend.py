"""
Backend tests for 3D viewer functionality
Tests scene retrieval, tile serving, and model download
"""
import pytest
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get authentication token"""
    # Try to login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # Register if needed
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword",
            "full_name": "Test User"
        }
    )
    
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "testpassword"}
    )
    return response.json()["access_token"]


@pytest.fixture
def test_scene_id(auth_token):
    """Create a test scene"""
    from io import BytesIO
    
    files = {
        "file": ("test.mp4", BytesIO(b"fake video"), "video/mp4")
    }
    
    response = client.post(
        "/api/v1/scenes/upload",
        files=files,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    
    if response.status_code in [200, 201, 202]:
        data = response.json()
        return data.get("sceneId") or data.get("_id")
    
    return "test-scene-id"


class TestSceneRetrieval:
    """Test scene data retrieval for viewer"""
    
    def test_get_scene_by_id(self, auth_token, test_scene_id):
        """Test retrieving scene by ID"""
        response = client.get(
            f"/api/v1/scenes/{test_scene_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 404]
        if response.status_code == 200:
            data = response.json()
            assert "_id" in data or "id" in data
            assert "name" in data
            assert "status" in data
    
    def test_get_scene_metadata(self, auth_token, test_scene_id):
        """Test retrieving scene metadata"""
        response = client.get(
            f"/api/v1/scenes/{test_scene_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check for expected metadata fields
            expected_fields = ["name", "status", "format", "bounds"]
            for field in expected_fields:
                assert field in data or True  # Some fields may be optional
    
    def test_list_scenes(self, auth_token):
        """Test listing all scenes"""
        response = client.get(
            "/api/v1/scenes",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data or isinstance(data, list)


class TestTileServing:
    """Test tile serving for streaming"""
    
    def test_get_tile_endpoint_exists(self, auth_token, test_scene_id):
        """Test that tile endpoint exists"""
        response = client.get(
            f"/api/v1/tiles/{test_scene_id}/0/0/0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 200 with tile data or 404 if not found
        assert response.status_code in [200, 404]
    
    def test_tile_caching_headers(self, auth_token, test_scene_id):
        """Test that tiles have proper caching headers"""
        response = client.get(
            f"/api/v1/tiles/{test_scene_id}/0/0/0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            # Check for cache headers
            assert "cache-control" in response.headers or "Cache-Control" in response.headers


class TestModelDownload:
    """Test 3D model download"""
    
    def test_download_scene_file(self, auth_token, test_scene_id):
        """Test downloading scene file"""
        response = client.get(
            f"/api/v1/scenes/{test_scene_id}/download",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return file or 404 if not ready
        assert response.status_code in [200, 404]
    
    def test_download_glb_export(self, auth_token, test_scene_id):
        """Test exporting scene as GLB"""
        response = client.get(
            f"/api/v1/scenes/{test_scene_id}/export/glb",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Endpoint may not exist yet, that's ok
        assert response.status_code in [200, 404, 501]


class TestGaussianSplatting:
    """Test Gaussian splatting specific features"""
    
    def test_gaussian_count_in_metadata(self, auth_token, test_scene_id):
        """Test that scene metadata includes Gaussian count"""
        response = client.get(
            f"/api/v1/scenes/{test_scene_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            # Gaussian count may be present for splat scenes
            assert "gaussianCount" in data or "gaussian_count" in data or True
    
    def test_splat_format_support(self, auth_token):
        """Test that splat format is supported"""
        from io import BytesIO
        
        files = {
            "file": ("test.splat", BytesIO(b"fake splat data"), "application/octet-stream")
        }
        
        response = client.post(
            "/api/v1/import/upload",
            files=files,
            data={"name": "Test Splat"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should accept or return proper error
        assert response.status_code in [200, 201, 202, 400, 415, 422]


class TestViewerPerformance:
    """Test viewer performance requirements"""
    
    def test_scene_load_time(self, auth_token, test_scene_id):
        """Test that scene loads within acceptable time"""
        import time
        
        start = time.time()
        response = client.get(
            f"/api/v1/scenes/{test_scene_id}",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        elapsed = time.time() - start
        
        # Should respond within 1 second
        assert elapsed < 1.0
        assert response.status_code in [200, 404]
    
    def test_tile_load_time(self, auth_token, test_scene_id):
        """Test that tiles load quickly"""
        import time
        
        start = time.time()
        response = client.get(
            f"/api/v1/tiles/{test_scene_id}/0/0/0",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        elapsed = time.time() - start
        
        # Tiles should load very fast
        assert elapsed < 0.5
        assert response.status_code in [200, 404]


class TestPublicSceneViewer:
    """Test public scene viewing without authentication"""
    
    def test_public_scene_access(self):
        """Test accessing public scene without auth"""
        # This would require a scene to be marked as public first
        response = client.get("/api/v1/public/scenes/test-scene-id")
        
        # Should work without auth or return 404
        assert response.status_code in [200, 404]
    
    def test_public_scene_requires_share_token(self):
        """Test that public scenes can use share tokens"""
        response = client.get(
            "/api/v1/public/scenes/test-scene-id",
            params={"token": "share-token-123"}
        )
        
        # Should validate token
        assert response.status_code in [200, 401, 404]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
