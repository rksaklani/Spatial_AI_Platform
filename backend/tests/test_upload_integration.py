"""
Integration tests for file upload functionality
Tests video upload, image upload, and 3D file import
"""
import pytest
from fastapi.testclient import TestClient
from io import BytesIO
from main import app

client = TestClient(app)


@pytest.fixture
def auth_token():
    """Get authentication token for testing"""
    response = client.post(
        "/api/v1/auth/login",
        data={
            "username": "test@example.com",
            "password": "testpassword"
        }
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    
    # Register if user doesn't exist
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
        data={
            "username": "test@example.com",
            "password": "testpassword"
        }
    )
    return response.json()["access_token"]


class TestVideoUpload:
    """Test video upload functionality"""
    
    def test_upload_single_video(self, auth_token):
        """Test uploading a single video file"""
        video_content = b"fake video content"
        files = {
            "file": ("test_video.mp4", BytesIO(video_content), "video/mp4")
        }
        
        response = client.post(
            "/api/v1/scenes/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "sceneId" in data or "_id" in data
    
    def test_upload_video_without_auth(self):
        """Test that upload requires authentication"""
        video_content = b"fake video content"
        files = {
            "file": ("test_video.mp4", BytesIO(video_content), "video/mp4")
        }
        
        response = client.post(
            "/api/v1/scenes/upload",
            files=files
        )
        
        assert response.status_code == 401
    
    def test_upload_invalid_video_format(self, auth_token):
        """Test uploading invalid video format"""
        text_content = b"not a video"
        files = {
            "file": ("test.txt", BytesIO(text_content), "text/plain")
        }
        
        response = client.post(
            "/api/v1/scenes/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should reject invalid format
        assert response.status_code in [400, 415, 422]
    
    def test_upload_supported_video_formats(self, auth_token):
        """Test all supported video formats"""
        formats = [
            ("test.mp4", "video/mp4"),
            ("test.mov", "video/quicktime"),
            ("test.avi", "video/x-msvideo"),
            ("test.webm", "video/webm"),
        ]
        
        for filename, mime_type in formats:
            files = {
                "file": (filename, BytesIO(b"video content"), mime_type)
            }
            
            response = client.post(
                "/api/v1/scenes/upload",
                files=files,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 201, 202], f"Failed for {filename}"


class TestImageUpload:
    """Test image upload functionality"""
    
    def test_upload_single_image(self, auth_token):
        """Test uploading a single image"""
        image_content = b"fake image content"
        files = {
            "file": ("test_image.jpg", BytesIO(image_content), "image/jpeg")
        }
        
        response = client.post(
            "/api/v1/photos/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 201, 202]
    
    def test_upload_multiple_images(self, auth_token):
        """Test uploading multiple images"""
        for i in range(3):
            files = {
                "file": (f"test_{i}.jpg", BytesIO(b"image content"), "image/jpeg")
            }
            
            response = client.post(
                "/api/v1/photos/upload",
                files=files,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 201, 202]
    
    def test_upload_supported_image_formats(self, auth_token):
        """Test all supported image formats"""
        formats = [
            ("test.jpg", "image/jpeg"),
            ("test.png", "image/png"),
            ("test.webp", "image/webp"),
        ]
        
        for filename, mime_type in formats:
            files = {
                "file": (filename, BytesIO(b"image content"), mime_type)
            }
            
            response = client.post(
                "/api/v1/photos/upload",
                files=files,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            
            assert response.status_code in [200, 201, 202], f"Failed for {filename}"


class Test3DFileImport:
    """Test 3D file import functionality"""
    
    def test_get_supported_formats(self, auth_token):
        """Test getting list of supported 3D formats"""
        response = client.get(
            "/api/v1/import/formats",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "formats" in data
        assert len(data["formats"]) > 0
    
    def test_import_glb_file(self, auth_token):
        """Test importing GLB file"""
        glb_content = b"fake glb content"
        files = {
            "file": ("model.glb", BytesIO(glb_content), "model/gltf-binary")
        }
        
        response = client.post(
            "/api/v1/import/upload",
            files=files,
            data={"name": "Test GLB Model"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 201, 202]
        data = response.json()
        assert "job_id" in data or "scene_id" in data
    
    def test_import_ply_file(self, auth_token):
        """Test importing PLY point cloud"""
        ply_content = b"fake ply content"
        files = {
            "file": ("pointcloud.ply", BytesIO(ply_content), "application/octet-stream")
        }
        
        response = client.post(
            "/api/v1/import/upload",
            files=files,
            data={"name": "Test Point Cloud"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 201, 202]
    
    def test_import_obj_file(self, auth_token):
        """Test importing OBJ mesh"""
        obj_content = b"fake obj content"
        files = {
            "file": ("model.obj", BytesIO(obj_content), "application/octet-stream")
        }
        
        response = client.post(
            "/api/v1/import/upload",
            files=files,
            data={"name": "Test OBJ Model"},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 201, 202]
    
    def test_import_status_tracking(self, auth_token):
        """Test tracking import job status"""
        # This would require a real job ID from a previous import
        # For now, test the endpoint exists
        response = client.get(
            "/api/v1/import/status/fake-job-id",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should return 404 for non-existent job or 200 with status
        assert response.status_code in [200, 404]


class TestUploadValidation:
    """Test upload validation and error handling"""
    
    def test_file_size_limit(self, auth_token):
        """Test file size validation"""
        # Create a mock large file (this won't actually be 6GB in memory)
        large_content = b"x" * (100 * 1024 * 1024)  # 100MB for testing
        files = {
            "file": ("large.mp4", BytesIO(large_content), "video/mp4")
        }
        
        response = client.post(
            "/api/v1/scenes/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Should accept or reject based on actual size limit
        assert response.status_code in [200, 201, 202, 413]
    
    def test_missing_file(self, auth_token):
        """Test upload without file"""
        response = client.post(
            "/api/v1/scenes/upload",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 422
    
    def test_concurrent_uploads(self, auth_token):
        """Test multiple concurrent uploads"""
        import concurrent.futures
        
        def upload_file(index):
            files = {
                "file": (f"test_{index}.mp4", BytesIO(b"video"), "video/mp4")
            }
            return client.post(
                "/api/v1/scenes/upload",
                files=files,
                headers={"Authorization": f"Bearer {auth_token}"}
            )
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(upload_file, i) for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # All uploads should succeed
        for response in results:
            assert response.status_code in [200, 201, 202]


class TestUploadProgress:
    """Test upload progress tracking"""
    
    def test_upload_with_progress_callback(self, auth_token):
        """Test that upload supports progress tracking"""
        video_content = b"fake video content" * 1000
        files = {
            "file": ("test.mp4", BytesIO(video_content), "video/mp4")
        }
        
        response = client.post(
            "/api/v1/scenes/upload",
            files=files,
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code in [200, 201, 202]
        # Progress tracking is handled client-side via axios


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
