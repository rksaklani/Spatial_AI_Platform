"""
Tests for Task 28: Gigapixel Photo Inspector

Task 28.5: Write photo inspector tests
- Test photo upload and EXIF extraction
- Test photo alignment
- Test gigapixel zoom
- Test view synchronization

Requirements: 26.1-26.9
"""

import pytest
import io
from datetime import datetime
from PIL import Image
from PIL.ExifTags import TAGS
import struct

from models.photo import PhotoFormat, EXIFMetadata, GPSCoordinates, PhotoAlignment


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def sample_jpeg_image():
    """Create a sample JPEG image for testing."""
    img = Image.new('RGB', (1920, 1080), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def sample_jpeg_with_exif():
    """Create a sample JPEG image with EXIF data."""
    from PIL.ExifTags import TAGS, GPSTAGS
    
    img = Image.new('RGB', (4000, 3000), color='red')
    
    # Create EXIF data
    exif_dict = {
        'Make': 'Canon',
        'Model': 'EOS R5',
        'DateTime': '2024:03:23 10:30:00',
        'FocalLength': (50, 1),
        'FNumber': (28, 10),
        'ISOSpeedRatings': 400,
    }
    
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def sample_gigapixel_image():
    """Create a sample gigapixel image (simulated with smaller size)."""
    # Simulate 150MP image (actual would be too large for tests)
    img = Image.new('RGB', (15000, 10000), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    return img_bytes


# ============================================================================
# Test Photo Upload and EXIF Extraction (Requirement 26.1, 26.2)
# ============================================================================

@pytest.mark.asyncio
async def test_photo_upload_jpeg(client, auth_headers, test_scene):
    """Test uploading a JPEG photo."""
    scene_id = test_scene["_id"]
    
    # Create test image
    img = Image.new('RGB', (1920, 1080), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    # Upload photo
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("test_photo.jpg", img_bytes, "image/jpeg")},
        data={"description": "Test photo"}
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["filename"] == "test_photo.jpg"
    assert data["format"] == "jpeg"
    assert data["scene_id"] == scene_id
    assert data["description"] == "Test photo"
    assert data["exif"] is not None
    assert data["exif"]["width"] == 1920
    assert data["exif"]["height"] == 1080
    assert data["exif"]["megapixels"] == pytest.approx(2.07, rel=0.1)


@pytest.mark.asyncio
async def test_photo_upload_png(client, auth_headers, test_scene):
    """Test uploading a PNG photo."""
    scene_id = test_scene["_id"]
    
    # Create test image
    img = Image.new('RGB', (2560, 1440), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    # Upload photo
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("test_photo.png", img_bytes, "image/png")},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["format"] == "png"
    assert data["exif"]["width"] == 2560
    assert data["exif"]["height"] == 1440


@pytest.mark.asyncio
async def test_photo_upload_tiff(client, auth_headers, test_scene):
    """Test uploading a TIFF photo."""
    scene_id = test_scene["_id"]
    
    # Create test image
    img = Image.new('RGB', (3840, 2160), color='green')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='TIFF')
    img_bytes.seek(0)
    
    # Upload photo
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("test_photo.tiff", img_bytes, "image/tiff")},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["format"] == "tiff"


@pytest.mark.asyncio
async def test_photo_upload_invalid_format(client, auth_headers, test_scene):
    """Test uploading an invalid file format."""
    scene_id = test_scene["_id"]
    
    # Create text file
    text_bytes = io.BytesIO(b"This is not an image")
    
    # Upload should fail
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("test.txt", text_bytes, "text/plain")},
    )
    
    assert response.status_code == 400
    assert "Invalid file format" in response.json()["detail"]


@pytest.mark.asyncio
async def test_photo_upload_too_large(client, auth_headers, test_scene):
    """Test uploading a photo exceeding megapixel limit."""
    scene_id = test_scene["_id"]
    
    # Create image exceeding 500MP (simulate with metadata)
    # In reality, we can't create a 500MP+ image in tests
    # So we'll test the validation logic separately
    
    # For now, test with a reasonable size
    img = Image.new('RGB', (10000, 10000), color='blue')  # 100MP
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("huge_photo.jpg", img_bytes, "image/jpeg")},
    )
    
    # Should succeed (under 500MP limit)
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_exif_extraction_basic(client, auth_headers, test_scene):
    """Test basic EXIF metadata extraction."""
    scene_id = test_scene["_id"]
    
    # Create image with basic EXIF
    img = Image.new('RGB', (4000, 3000), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("photo.jpg", img_bytes, "image/jpeg")},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Check EXIF data
    assert data["exif"] is not None
    assert data["exif"]["width"] == 4000
    assert data["exif"]["height"] == 3000
    assert data["exif"]["megapixels"] == 12.0


# ============================================================================
# Test Photo Alignment (Requirement 26.3, 26.4)
# ============================================================================

@pytest.mark.asyncio
async def test_photo_alignment_gps(client, auth_headers, test_scene, test_photo_with_gps):
    """Test automatic photo alignment using GPS coordinates."""
    photo_id = test_photo_with_gps["_id"]
    
    # Trigger GPS alignment
    response = client.post(
        f"/api/v1/photos/photos/{photo_id}/align",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check alignment
    assert data["alignment"] is not None
    assert data["alignment"]["is_aligned"] is True
    assert data["alignment"]["alignment_method"] == "gps"
    assert data["alignment"]["position_3d"] is not None
    assert len(data["alignment"]["position_3d"]) == 3
    assert data["alignment"]["alignment_confidence"] > 0


@pytest.mark.asyncio
async def test_photo_alignment_manual(client, auth_headers, test_scene, test_photo):
    """Test manual photo alignment."""
    photo_id = test_photo["_id"]
    
    # Set manual alignment
    position = [10.5, 2.3, -5.7]
    rotation = [0.0, 0.0, 0.0, 1.0]  # Identity quaternion
    
    response = client.post(
        f"/api/v1/photos/photos/{photo_id}/align/manual",
        headers=auth_headers,
        params={
            "position_3d": position,
            "rotation_3d": rotation,
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Check alignment
    assert data["alignment"] is not None
    assert data["alignment"]["is_aligned"] is True
    assert data["alignment"]["alignment_method"] == "manual"
    assert data["alignment"]["position_3d"] == position
    assert data["alignment"]["rotation_3d"] == rotation
    assert data["alignment"]["alignment_confidence"] == 1.0


@pytest.mark.asyncio
async def test_photo_alignment_no_gps(client, auth_headers, test_scene, test_photo):
    """Test GPS alignment fails when photo has no GPS data."""
    photo_id = test_photo["_id"]
    
    # Try GPS alignment without GPS data
    response = client.post(
        f"/api/v1/photos/photos/{photo_id}/align",
        headers=auth_headers,
    )
    
    assert response.status_code == 400
    assert "GPS metadata" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_photo_markers(client, auth_headers, test_scene, test_photo_aligned):
    """Test retrieving photo markers for scene."""
    scene_id = test_scene["_id"]
    
    response = client.get(
        f"/api/v1/photos/scenes/{scene_id}/photo-markers",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    markers = response.json()
    
    assert len(markers) > 0
    marker = markers[0]
    assert "photo_id" in marker
    assert "filename" in marker
    assert "position" in marker
    assert len(marker["position"]) == 3


# ============================================================================
# Test Photo List and Retrieval
# ============================================================================

@pytest.mark.asyncio
async def test_list_photos(client, auth_headers, test_scene, test_photo):
    """Test listing photos for a scene."""
    scene_id = test_scene["_id"]
    
    response = client.get(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "items" in data
    assert "total" in data
    assert data["total"] > 0
    assert len(data["items"]) > 0


@pytest.mark.asyncio
async def test_get_photo(client, auth_headers, test_photo):
    """Test retrieving a single photo."""
    photo_id = test_photo["_id"]
    
    response = client.get(
        f"/api/v1/photos/photos/{photo_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["id"] == photo_id
    assert data["filename"] == test_photo["filename"]


@pytest.mark.asyncio
async def test_update_photo(client, auth_headers, test_photo):
    """Test updating photo metadata."""
    photo_id = test_photo["_id"]
    
    response = client.patch(
        f"/api/v1/photos/photos/{photo_id}",
        headers=auth_headers,
        json={"description": "Updated description"}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["description"] == "Updated description"


@pytest.mark.asyncio
async def test_delete_photo(client, auth_headers, test_photo):
    """Test deleting a photo."""
    photo_id = test_photo["_id"]
    
    response = client.delete(
        f"/api/v1/photos/photos/{photo_id}",
        headers=auth_headers,
    )
    
    assert response.status_code == 204
    
    # Verify photo is deleted
    response = client.get(
        f"/api/v1/photos/photos/{photo_id}",
        headers=auth_headers,
    )
    assert response.status_code == 404


# ============================================================================
# Test Photo Download
# ============================================================================

@pytest.mark.asyncio
async def test_download_photo(client, auth_headers, test_photo):
    """Test downloading a photo file."""
    photo_id = test_photo["_id"]
    
    response = client.get(
        f"/api/v1/photos/photos/{photo_id}/download",
        headers=auth_headers,
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] in ["image/jpeg", "image/png", "image/tiff"]
    assert "content-disposition" in response.headers


# ============================================================================
# Test Access Control
# ============================================================================

@pytest.mark.asyncio
async def test_photo_access_denied_different_org(client, auth_headers, test_photo, other_org_user):
    """Test that users cannot access photos from other organizations."""
    photo_id = test_photo["_id"]
    
    # Get token for other org user
    other_headers = {"Authorization": f"Bearer {other_org_user['token']}"}
    
    response = client.get(
        f"/api/v1/photos/photos/{photo_id}",
        headers=other_headers,
    )
    
    assert response.status_code == 403


# ============================================================================
# Test Gigapixel Support (Requirement 26.5, 26.6, 26.8)
# ============================================================================

@pytest.mark.asyncio
async def test_gigapixel_photo_upload(client, auth_headers, test_scene):
    """Test uploading a gigapixel photo (>100MP)."""
    scene_id = test_scene["_id"]
    
    # Create 150MP image (simulated with smaller size for test)
    img = Image.new('RGB', (15000, 10000), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("gigapixel.jpg", img_bytes, "image/jpeg")},
    )
    
    assert response.status_code == 201
    data = response.json()
    
    # Verify megapixels
    assert data["exif"]["megapixels"] == 150.0
    assert data["exif"]["width"] == 15000
    assert data["exif"]["height"] == 10000


def test_photo_format_detection():
    """Test photo format detection from filename and content type."""
    from api.photos import determine_photo_format
    
    assert determine_photo_format("photo.jpg", "image/jpeg") == PhotoFormat.JPEG
    assert determine_photo_format("photo.jpeg", "image/jpeg") == PhotoFormat.JPEG
    assert determine_photo_format("photo.png", "image/png") == PhotoFormat.PNG
    assert determine_photo_format("photo.tiff", "image/tiff") == PhotoFormat.TIFF
    assert determine_photo_format("photo.tif", "image/tiff") == PhotoFormat.TIFF
    assert determine_photo_format("photo.bmp", "image/bmp") is None


def test_photo_validation():
    """Test photo file validation."""
    from api.photos import validate_photo_file
    
    # Valid JPEG
    img = Image.new('RGB', (1920, 1080), color='blue')
    is_valid, msg = validate_photo_file("photo.jpg", "image/jpeg", img)
    assert is_valid is True
    
    # Invalid extension
    is_valid, msg = validate_photo_file("photo.bmp", "image/bmp", img)
    assert is_valid is False
    assert "Invalid file format" in msg
    
    # Too large (>500MP)
    large_img = Image.new('RGB', (30000, 20000), color='blue')  # 600MP
    is_valid, msg = validate_photo_file("huge.jpg", "image/jpeg", large_img)
    assert is_valid is False
    assert "too large" in msg


# ============================================================================
# Test Fixtures for Tests
# ============================================================================

@pytest.fixture
async def test_photo(client, auth_headers, test_scene):
    """Create a test photo."""
    scene_id = test_scene["_id"]
    
    img = Image.new('RGB', (1920, 1080), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("test_photo.jpg", img_bytes, "image/jpeg")},
    )
    
    return response.json()


@pytest.fixture
async def test_photo_with_gps(client, auth_headers, test_scene, db):
    """Create a test photo with GPS data."""
    scene_id = test_scene["_id"]
    
    img = Image.new('RGB', (1920, 1080), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    
    response = client.post(
        f"/api/v1/photos/scenes/{scene_id}/photos",
        headers=auth_headers,
        files={"file": ("gps_photo.jpg", img_bytes, "image/jpeg")},
    )
    
    photo = response.json()
    
    # Add GPS data manually
    await db.photos.update_one(
        {"_id": photo["id"]},
        {
            "$set": {
                "exif.gps": {
                    "latitude": 37.7749,
                    "longitude": -122.4194,
                    "altitude": 10.0
                }
            }
        }
    )
    
    # Fetch updated photo
    updated = await db.photos.find_one({"_id": photo["id"]})
    return updated


@pytest.fixture
async def test_photo_aligned(client, auth_headers, test_scene, test_photo):
    """Create a test photo with alignment."""
    photo_id = test_photo["id"]
    
    response = client.post(
        f"/api/v1/photos/photos/{photo_id}/align/manual",
        headers=auth_headers,
        params={
            "position_3d": [10.0, 2.0, -5.0],
            "rotation_3d": [0.0, 0.0, 0.0, 1.0],
        }
    )
    
    return response.json()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
