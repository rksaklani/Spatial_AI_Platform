"""
Tests for Task 1.2: FastAPI backend project structure.

Verifies that FastAPI app is properly initialized with correct structure.
Requirements: 22.1
"""
import pytest
import os


class TestProjectStructure:
    """Test project directory structure exists."""
    
    @pytest.mark.unit
    def test_api_directory_exists(self):
        """API directory should exist."""
        assert os.path.isdir("api")
    
    @pytest.mark.unit
    def test_services_directory_exists(self):
        """Services directory should exist."""
        assert os.path.isdir("services")
    
    @pytest.mark.unit
    def test_models_directory_exists(self):
        """Models directory should exist."""
        assert os.path.isdir("models")
    
    @pytest.mark.unit
    def test_utils_directory_exists(self):
        """Utils directory should exist."""
        assert os.path.isdir("utils")
    
    @pytest.mark.unit
    def test_workers_directory_exists(self):
        """Workers directory should exist."""
        assert os.path.isdir("workers")
    
    @pytest.mark.unit
    def test_main_py_exists(self):
        """main.py should exist."""
        assert os.path.isfile("main.py")


class TestFastAPIApp:
    """Test FastAPI app initialization."""
    
    @pytest.mark.unit
    def test_app_importable(self):
        """FastAPI app should be importable."""
        from main import app
        assert app is not None
    
    @pytest.mark.unit
    def test_app_title(self):
        """App should have correct title."""
        from main import app
        assert app.title == "Ultimate Spatial AI Platform"
    
    @pytest.mark.unit
    def test_app_version(self):
        """App should have version 1.0.0."""
        from main import app
        assert app.version == "1.0.0"
    
    @pytest.mark.unit
    def test_cors_middleware_configured(self):
        """CORS middleware should be configured."""
        from main import app
        middlewares = [m.cls.__name__ for m in app.user_middleware]
        assert "CORSMiddleware" in middlewares


class TestConfigModule:
    """Test configuration module."""
    
    @pytest.mark.unit
    def test_settings_importable(self):
        """Settings should be importable."""
        from utils.config import settings
        assert settings is not None
    
    @pytest.mark.unit
    def test_settings_has_mongodb_url(self):
        """Settings should have mongodb_url."""
        from utils.config import settings
        assert hasattr(settings, "mongodb_url")
    
    @pytest.mark.unit
    def test_settings_has_jwt_secret(self):
        """Settings should have jwt_secret_key."""
        from utils.config import settings
        assert hasattr(settings, "jwt_secret_key")
    
    @pytest.mark.unit
    def test_settings_has_api_port(self):
        """Settings should have api_port."""
        from utils.config import settings
        assert hasattr(settings, "api_port")
        assert isinstance(settings.api_port, int)


class TestRootEndpoint:
    """Test root endpoint."""
    
    @pytest.mark.unit
    def test_root_endpoint(self, sync_client):
        """Root endpoint should return status."""
        response = sync_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["version"] == "1.0.0"
