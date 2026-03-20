"""
Tests for Task 1.1: Python environment and dependencies.

Verifies that all required packages are installed and importable.
Requirements: 22.1, 22.2, 22.7
"""
import pytest


class TestCorePackages:
    """Test core framework packages are installed."""
    
    @pytest.mark.unit
    def test_fastapi_installed(self):
        """FastAPI should be importable."""
        import fastapi
        assert fastapi.__version__
    
    @pytest.mark.unit
    def test_uvicorn_installed(self):
        """Uvicorn should be importable."""
        import uvicorn
        assert uvicorn
    
    @pytest.mark.unit
    def test_pydantic_installed(self):
        """Pydantic should be importable."""
        import pydantic
        assert pydantic.__version__
    
    @pytest.mark.unit
    def test_python_multipart_installed(self):
        """python-multipart should be importable."""
        import multipart
        assert multipart
    
    @pytest.mark.unit
    def test_python_dotenv_installed(self):
        """python-dotenv should be importable."""
        import dotenv
        assert dotenv


class TestDatabasePackages:
    """Test database packages are installed."""
    
    @pytest.mark.unit
    def test_pymongo_installed(self):
        """PyMongo should be importable."""
        import pymongo
        assert pymongo.__version__
    
    @pytest.mark.unit
    def test_motor_installed(self):
        """Motor (async MongoDB) should be importable."""
        import motor
        assert motor
    
    @pytest.mark.unit
    def test_valkey_installed(self):
        """Valkey should be importable."""
        import valkey
        assert valkey
    
    @pytest.mark.unit
    def test_minio_installed(self):
        """MinIO should be importable."""
        import minio
        assert minio


class TestProcessingPackages:
    """Test processing packages are installed."""
    
    @pytest.mark.unit
    def test_celery_installed(self):
        """Celery should be importable."""
        import celery
        assert celery.__version__
    
    @pytest.mark.unit
    def test_ffmpeg_python_installed(self):
        """ffmpeg-python should be importable."""
        import ffmpeg
        assert ffmpeg


class TestAuthPackages:
    """Test authentication packages are installed."""
    
    @pytest.mark.unit
    def test_python_jose_installed(self):
        """python-jose should be importable."""
        import jose
        assert jose
    
    @pytest.mark.unit
    def test_passlib_installed(self):
        """passlib should be importable."""
        import passlib
        assert passlib
    
    @pytest.mark.unit
    def test_bcrypt_installed(self):
        """bcrypt should be importable."""
        import bcrypt
        assert bcrypt


class TestAIMLPackages:
    """Test AI/ML packages are installed."""
    
    @pytest.mark.unit
    def test_torch_installed(self):
        """PyTorch should be importable."""
        import torch
        assert torch.__version__
    
    @pytest.mark.unit
    def test_torchvision_installed(self):
        """TorchVision should be importable."""
        import torchvision
        assert torchvision.__version__
    
    @pytest.mark.unit
    def test_transformers_installed(self):
        """Transformers should be importable."""
        import transformers
        assert transformers.__version__
    
    @pytest.mark.unit
    def test_opencv_installed(self):
        """OpenCV should be importable."""
        import cv2
        assert cv2.__version__
    
    @pytest.mark.unit
    def test_numpy_installed(self):
        """NumPy should be importable."""
        import numpy
        assert numpy.__version__
    
    @pytest.mark.unit
    def test_pillow_installed(self):
        """Pillow should be importable."""
        from PIL import Image
        assert Image


class Test3DPackages:
    """Test 3D processing packages are installed."""
    
    @pytest.mark.unit
    def test_open3d_installed(self):
        """Open3D should be importable."""
        import open3d
        assert open3d.__version__
    
    @pytest.mark.unit
    def test_trimesh_installed(self):
        """Trimesh should be importable."""
        import trimesh
        assert trimesh
    
    @pytest.mark.unit
    def test_plyfile_installed(self):
        """Plyfile should be importable."""
        import plyfile
        assert plyfile
    
    @pytest.mark.unit
    def test_laspy_installed(self):
        """Laspy should be importable."""
        import laspy
        assert laspy


class TestMonitoringPackages:
    """Test monitoring packages are installed."""
    
    @pytest.mark.unit
    def test_structlog_installed(self):
        """Structlog should be importable."""
        import structlog
        assert structlog
    
    @pytest.mark.unit
    def test_prometheus_client_installed(self):
        """Prometheus client should be importable."""
        import prometheus_client
        assert prometheus_client


class TestReportingPackages:
    """Test reporting packages are installed."""
    
    @pytest.mark.unit
    def test_reportlab_installed(self):
        """ReportLab should be importable."""
        import reportlab
        assert reportlab
    
    @pytest.mark.unit
    def test_jinja2_installed(self):
        """Jinja2 should be importable."""
        import jinja2
        assert jinja2


class TestDevPackages:
    """Test development packages are installed."""
    
    @pytest.mark.unit
    def test_pytest_installed(self):
        """Pytest should be importable."""
        import pytest
        assert pytest
    
    @pytest.mark.unit
    def test_pytest_asyncio_installed(self):
        """pytest-asyncio should be importable."""
        import pytest_asyncio
        assert pytest_asyncio
    
    @pytest.mark.unit
    def test_black_installed(self):
        """Black should be importable."""
        import black
        assert black
    
    @pytest.mark.unit
    def test_isort_installed(self):
        """isort should be importable."""
        import isort
        assert isort
    
    @pytest.mark.unit
    def test_mypy_installed(self):
        """mypy should be importable."""
        import mypy
        assert mypy
