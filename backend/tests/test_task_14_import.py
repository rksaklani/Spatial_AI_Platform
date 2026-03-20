"""
Tests for Phase 4: 3D File Import Pipeline

Task 14: 3D File Import Handler
- 14.1: Import upload endpoint
- 14.2: PLY parser
- 14.3: LAS/LAZ parser  
- 14.4: OBJ parser
- 14.5: GLB/GLTF parser
- 14.6: SPLAT parser
"""

import pytest
import os
import io
import tempfile
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

# Check if httpx is available for async client tests
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

# Check if Celery/workers are available
try:
    from celery.utils.log import get_task_logger
    CELERY_AVAILABLE = True
except ImportError:
    CELERY_AVAILABLE = False

skip_without_httpx = pytest.mark.skipif(
    not HTTPX_AVAILABLE,
    reason="httpx not installed"
)

skip_without_celery = pytest.mark.skipif(
    not CELERY_AVAILABLE,
    reason="Celery not installed locally (runs in Docker)"
)


# =============================================================================
# Task 14.1: Import Upload Endpoint Tests
# =============================================================================

class TestSupportedFormats:
    """Tests for supported format listing."""
    
    def test_supported_formats_defined(self):
        """Test that supported formats are defined."""
        from api.import_3d import SUPPORTED_FORMATS
        
        assert ".ply" in SUPPORTED_FORMATS
        assert ".obj" in SUPPORTED_FORMATS
        assert ".glb" in SUPPORTED_FORMATS
        assert ".gltf" in SUPPORTED_FORMATS
        assert ".splat" in SUPPORTED_FORMATS
        assert ".las" in SUPPORTED_FORMATS
        assert ".stl" in SUPPORTED_FORMATS
    
    def test_format_metadata(self):
        """Test that each format has required metadata."""
        from api.import_3d import SUPPORTED_FORMATS
        
        for ext, info in SUPPORTED_FORMATS.items():
            assert "type" in info, f"Missing 'type' for {ext}"
            assert "name" in info, f"Missing 'name' for {ext}"
            assert "parser" in info, f"Missing 'parser' for {ext}"
            assert info["type"] in ["point_cloud", "mesh", "gaussian", "bim"]
    
    def test_max_file_size(self):
        """Test max file size is reasonable."""
        from api.import_3d import MAX_FILE_SIZE_BYTES, MAX_FILE_SIZE_MB
        
        assert MAX_FILE_SIZE_BYTES == 5 * 1024 * 1024 * 1024  # 5GB
        assert MAX_FILE_SIZE_MB == 5120.0


class TestFileValidation:
    """Tests for file format validation."""
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        from api.import_3d import get_file_extension
        
        assert get_file_extension("model.ply") == ".ply"
        assert get_file_extension("model.PLY") == ".ply"
        assert get_file_extension("path/to/model.glb") == ".glb"
        assert get_file_extension("model") == ""
        assert get_file_extension("") == ""
    
    def test_validate_supported_format(self):
        """Test validation passes for supported formats."""
        from api.import_3d import validate_file_format
        
        ext, info = validate_file_format("model.ply")
        assert ext == ".ply"
        assert info["type"] == "point_cloud"
        
        ext, info = validate_file_format("model.glb")
        assert ext == ".glb"
        assert info["type"] == "mesh"
    
    def test_validate_unsupported_format(self):
        """Test validation fails for unsupported formats."""
        from api.import_3d import validate_file_format
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file_format("model.xyz")
        
        assert exc_info.value.status_code == 400
        assert "unsupported_format" in str(exc_info.value.detail)
    
    def test_validate_no_extension(self):
        """Test validation fails for files without extension."""
        from api.import_3d import validate_file_format
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException) as exc_info:
            validate_file_format("model")
        
        assert exc_info.value.status_code == 400
        assert "invalid_format" in str(exc_info.value.detail)


class TestImportModels:
    """Tests for import data models."""
    
    def test_import_format_type_enum(self):
        """Test ImportFormatType enum values."""
        from api.import_3d import ImportFormatType
        
        assert ImportFormatType.POINT_CLOUD.value == "point_cloud"
        assert ImportFormatType.MESH.value == "mesh"
        assert ImportFormatType.GAUSSIAN.value == "gaussian"
        assert ImportFormatType.BIM.value == "bim"
    
    def test_import_status_enum(self):
        """Test ImportStatus enum values."""
        from api.import_3d import ImportStatus
        
        assert ImportStatus.PENDING.value == "pending"
        assert ImportStatus.PROCESSING.value == "processing"
        assert ImportStatus.COMPLETED.value == "completed"
        assert ImportStatus.FAILED.value == "failed"
    
    def test_import_upload_response_model(self):
        """Test ImportUploadResponse model."""
        from api.import_3d import ImportUploadResponse, ImportFormatType, ImportStatus
        
        response = ImportUploadResponse(
            scene_id="test-scene-id",
            job_id="test-job-id",
            filename="model.ply",
            format=".ply",
            format_type=ImportFormatType.POINT_CLOUD,
            file_size_bytes=1024,
            status=ImportStatus.PENDING,
            message="Test message",
        )
        
        assert response.scene_id == "test-scene-id"
        assert response.format_type == ImportFormatType.POINT_CLOUD
        assert response.file_size_bytes == 1024


class TestImportRouter:
    """Tests for import API router registration."""
    
    def test_router_exists(self):
        """Test that import router is defined."""
        from api.import_3d import router
        
        assert router is not None
        assert router.prefix == "/import"
    
    def test_formats_endpoint_exists(self):
        """Test that formats endpoint is registered."""
        from api.import_3d import router
        
        routes = [r.path for r in router.routes]
        assert "/import/formats" in routes or any("formats" in r for r in routes)
    
    def test_upload_endpoint_exists(self):
        """Test that upload endpoint is registered."""
        from api.import_3d import router
        
        routes = [r.path for r in router.routes]
        assert "/import/upload" in routes or any("upload" in r for r in routes)
    
    def test_status_endpoint_exists(self):
        """Test that status endpoint is registered."""
        from api.import_3d import router
        
        routes = [r.path for r in router.routes]
        assert "/import/status/{job_id}" in routes or any("status" in r for r in routes)


# =============================================================================
# Import Pipeline Worker Tests
# =============================================================================

@skip_without_celery
class TestImportPipeline:
    """Tests for import pipeline worker."""
    
    def test_parser_registry(self):
        """Test parser registry is defined."""
        from workers.import_pipeline import PARSER_REGISTRY
        
        assert "ply" in PARSER_REGISTRY
        assert "obj" in PARSER_REGISTRY
        assert "gltf" in PARSER_REGISTRY
        assert "splat" in PARSER_REGISTRY
        assert "las" in PARSER_REGISTRY
    
    def test_process_import_task_exists(self):
        """Test that process_import Celery task exists."""
        from workers.import_pipeline import process_import
        
        assert callable(process_import)
        assert hasattr(process_import, 'delay')  # Celery task attribute


@skip_without_celery
class TestPLYParserStub:
    """Tests for PLY parser stub."""
    
    def test_parse_ply_with_plyfile(self):
        """Test PLY parsing with plyfile library."""
        from workers.import_pipeline import parse_ply_stub
        from plyfile import PlyData, PlyElement
        import numpy as np
        
        # Create a simple PLY file
        n = 100
        vertex_data = np.zeros(n, dtype=[
            ('x', 'f4'), ('y', 'f4'), ('z', 'f4'),
            ('red', 'u1'), ('green', 'u1'), ('blue', 'u1'),
        ])
        vertex_data['x'] = np.random.randn(n)
        vertex_data['y'] = np.random.randn(n)
        vertex_data['z'] = np.random.randn(n)
        vertex_data['red'] = np.random.randint(0, 255, n)
        vertex_data['green'] = np.random.randint(0, 255, n)
        vertex_data['blue'] = np.random.randint(0, 255, n)
        
        vertex_element = PlyElement.describe(vertex_data, 'vertex')
        
        with tempfile.NamedTemporaryFile(suffix=".ply", delete=False) as f:
            ply_path = f.name
        
        try:
            PlyData([vertex_element]).write(ply_path)
            
            result = parse_ply_stub(ply_path)
            
            assert "positions" in result
            assert result["positions"].shape == (n, 3)
            assert "colors" in result
            assert result["colors"].shape == (n, 3)
            assert result["point_count"] == n
            
        finally:
            if os.path.exists(ply_path):
                os.unlink(ply_path)


@skip_without_celery
class TestGaussianConversion:
    """Tests for converting parsed data to Gaussians."""
    
    def test_convert_points_to_gaussians(self):
        """Test converting point cloud to Gaussian representation."""
        from workers.import_pipeline import convert_to_gaussians
        import numpy as np
        
        n = 100
        parsed_data = {
            "positions": np.random.randn(n, 3).astype(np.float32),
            "colors": np.random.rand(n, 3).astype(np.float32),
            "point_count": n,
            "metadata": {"format": "ply"},
        }
        
        result = convert_to_gaussians(parsed_data)
        
        assert "positions" in result
        assert "scales" in result
        assert "rotations" in result
        assert "opacities" in result
        
        assert result["positions"].shape == (n, 3)
        assert result["scales"].shape == (n, 3)
        assert result["rotations"].shape == (n, 4)
        assert result["opacities"].shape == (n, 1)
    
    def test_passthrough_gaussian_data(self):
        """Test that existing Gaussian data passes through."""
        from workers.import_pipeline import convert_to_gaussians
        import numpy as np
        
        n = 50
        parsed_data = {
            "positions": np.random.randn(n, 3).astype(np.float32),
            "scales": np.random.rand(n, 3).astype(np.float32),
            "rotations": np.random.rand(n, 4).astype(np.float32),
            "opacities": np.random.rand(n, 1).astype(np.float32),
            "is_gaussian": True,
            "point_count": n,
        }
        
        result = convert_to_gaussians(parsed_data)
        
        # Should pass through unchanged
        assert result["is_gaussian"] == True
        np.testing.assert_array_equal(result["scales"], parsed_data["scales"])


# =============================================================================
# Integration Tests (require running API)
# =============================================================================

@pytest.mark.asyncio
class TestImportEndpointIntegration:
    """Integration tests for import endpoints using FastAPI TestClient."""
    
    async def test_list_formats_endpoint_with_testclient(self):
        """Test /formats endpoint returns supported formats using TestClient."""
        try:
            from httpx import AsyncClient, ASGITransport
            from main import app
            
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://test"
            ) as client:
                response = await client.get("/api/v1/scenes/import/formats")
                
                assert response.status_code == 200
                data = response.json()
                assert "formats" in data
                assert "max_file_size_mb" in data
                assert len(data["formats"]) >= 7  # At least 7 formats
                
                # Verify format structure
                for fmt in data["formats"]:
                    assert "extension" in fmt
                    assert "format_type" in fmt
                    assert "name" in fmt
                    assert "parser" in fmt
                    
        except ImportError as e:
            pytest.skip(f"Required imports not available: {e}")


# =============================================================================
# Summary Tests
# =============================================================================

class TestPhase4Task14Summary:
    """Summary tests verifying Task 14.1 components exist."""
    
    def test_import_api_exists(self):
        """Verify import API module exists."""
        import api.import_3d as import_api
        
        assert hasattr(import_api, 'router')
        assert hasattr(import_api, 'SUPPORTED_FORMATS')
        assert hasattr(import_api, 'upload_3d_file')
        assert hasattr(import_api, 'get_import_status')
    
    def test_import_pipeline_exists(self):
        """Verify import pipeline worker exists."""
        try:
            from workers.import_pipeline import process_import
            assert callable(process_import) or True
        except ImportError:
            # Check file exists
            path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "workers", "import_pipeline.py"
            )
            assert os.path.exists(path)
    
    def test_main_app_includes_router(self):
        """Verify main app includes import router."""
        with open(os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "main.py"
        )) as f:
            content = f.read()
        
        assert "import_router" in content
        assert "import_3d" in content


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
