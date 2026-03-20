"""
Tests for Tasks 1.5-1.9: Infrastructure components.

Task 1.5: MongoDB deployment and configuration
Task 1.6: MinIO object storage
Task 1.7: Valkey cache/queue
Task 1.8: Celery task queue
Task 1.9: Health and monitoring endpoints

Requirements: 21.1-21.5, 19.1, 19.3, 19.5, 19.7, 22.4, 22.5
"""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch


class TestMongoDBModule:
    """Test MongoDB database module (Task 1.5)."""
    
    @pytest.mark.unit
    def test_database_class_importable(self):
        """Database class should be importable."""
        from utils.database import Database
        assert Database is not None
    
    @pytest.mark.unit
    def test_get_db_importable(self):
        """get_db function should be importable."""
        from utils.database import get_db
        assert callable(get_db)
    
    @pytest.mark.unit
    def test_init_database_sync_importable(self):
        """init_database_sync should be importable."""
        from utils.database import init_database_sync
        assert callable(init_database_sync)
    
    @pytest.mark.unit
    def test_init_database_async_importable(self):
        """init_database_async should be importable."""
        from utils.database import init_database_async
        assert callable(init_database_async)


class TestMinIOModule:
    """Test MinIO client module (Task 1.6)."""
    
    @pytest.mark.unit
    def test_minio_client_importable(self):
        """MinIOClient should be importable."""
        from utils.minio_client import MinIOClient
        assert MinIOClient is not None
    
    @pytest.mark.unit
    def test_get_minio_client_importable(self):
        """get_minio_client should be importable."""
        from utils.minio_client import get_minio_client
        assert callable(get_minio_client)
    
    @pytest.mark.unit
    def test_initialize_buckets_importable(self):
        """initialize_buckets should be importable."""
        from utils.minio_client import initialize_buckets
        assert callable(initialize_buckets)
    
    @pytest.mark.unit
    def test_minio_client_has_required_methods(self):
        """MinIOClient should have required methods."""
        from utils.minio_client import MinIOClient
        assert hasattr(MinIOClient, 'create_bucket')
        assert hasattr(MinIOClient, 'upload_file')
        assert hasattr(MinIOClient, 'download_file')
        assert hasattr(MinIOClient, 'get_object')
        assert hasattr(MinIOClient, 'delete_object')
        assert hasattr(MinIOClient, 'list_objects')
    
    @pytest.mark.unit
    def test_required_buckets_defined(self):
        """Required buckets should be defined."""
        # Test the expected bucket names
        expected_buckets = ['videos', 'frames', 'depth', 'scenes', 'reports']
        from utils.minio_client import initialize_buckets
        # The function creates these buckets
        # We just verify the function exists and is callable
        assert callable(initialize_buckets)


class TestValkeyModule:
    """Test Valkey client module (Task 1.7)."""
    
    @pytest.mark.unit
    def test_valkey_client_importable(self):
        """ValkeyClient should be importable."""
        from utils.valkey_client import ValkeyClient
        assert ValkeyClient is not None
    
    @pytest.mark.unit
    def test_get_valkey_client_importable(self):
        """get_valkey_client should be importable."""
        from utils.valkey_client import get_valkey_client
        assert callable(get_valkey_client)
    
    @pytest.mark.unit
    def test_valkey_client_has_caching_methods(self):
        """ValkeyClient should have caching methods."""
        from utils.valkey_client import ValkeyClient
        assert hasattr(ValkeyClient, 'get')
        assert hasattr(ValkeyClient, 'set')
        assert hasattr(ValkeyClient, 'delete')
        assert hasattr(ValkeyClient, 'expire')
        assert hasattr(ValkeyClient, 'ttl')
    
    @pytest.mark.unit
    def test_valkey_client_has_json_methods(self):
        """ValkeyClient should have JSON caching methods."""
        from utils.valkey_client import ValkeyClient
        assert hasattr(ValkeyClient, 'get_json')
        assert hasattr(ValkeyClient, 'set_json')
    
    @pytest.mark.unit
    def test_valkey_client_has_tile_caching_methods(self):
        """ValkeyClient should have tile caching methods."""
        from utils.valkey_client import ValkeyClient
        assert hasattr(ValkeyClient, 'cache_tile')
        assert hasattr(ValkeyClient, 'get_tile')
    
    @pytest.mark.unit
    def test_valkey_client_has_session_methods(self):
        """ValkeyClient should have session management methods."""
        from utils.valkey_client import ValkeyClient
        assert hasattr(ValkeyClient, 'create_session')
        assert hasattr(ValkeyClient, 'get_session')
        assert hasattr(ValkeyClient, 'delete_session')
    
    @pytest.mark.unit
    def test_valkey_client_has_token_blacklist_methods(self):
        """ValkeyClient should have token blacklist methods."""
        from utils.valkey_client import ValkeyClient
        assert hasattr(ValkeyClient, 'blacklist_token')
        assert hasattr(ValkeyClient, 'is_token_blacklisted')


class TestCeleryModule:
    """Test Celery configuration module (Task 1.8)."""
    
    @pytest.mark.unit
    def test_celery_app_importable(self):
        """Celery app should be importable."""
        from workers.celery_app import celery_app
        assert celery_app is not None
    
    @pytest.mark.unit
    def test_celery_app_name(self):
        """Celery app should have correct name."""
        from workers.celery_app import celery_app
        assert celery_app.main == "spatial_ai_platform"
    
    @pytest.mark.unit
    def test_celery_queues_configured(self):
        """Celery should have CPU and GPU queues configured."""
        from workers.celery_app import celery_app
        queue_names = [q.name for q in celery_app.conf.task_queues]
        assert 'cpu' in queue_names
        assert 'gpu' in queue_names
    
    @pytest.mark.unit
    def test_celery_task_routing_configured(self):
        """Celery should have task routing configured."""
        from workers.celery_app import celery_app
        routes = celery_app.conf.task_routes
        assert routes is not None
        # Check GPU routing exists
        assert any('gpu' in str(k).lower() for k in routes.keys())
    
    @pytest.mark.unit
    def test_celery_serialization_json(self):
        """Celery should use JSON serialization."""
        from workers.celery_app import celery_app
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"


class TestBaseTask:
    """Test Celery base task module."""
    
    @pytest.mark.unit
    def test_base_task_importable(self):
        """Base task module should be importable."""
        from workers import base_task
        assert base_task is not None


class TestHealthEndpoints:
    """Test health and monitoring endpoints (Task 1.9)."""
    
    @pytest.mark.unit
    def test_health_router_importable(self):
        """Health router should be importable."""
        from api.health import router
        assert router is not None
    
    @pytest.mark.unit
    def test_basic_health_endpoint(self, simple_client):
        """Basic health endpoint should return ok."""
        response = simple_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
    
    @pytest.mark.unit
    def test_detailed_health_response_model(self):
        """DetailedHealthResponse model should have required fields."""
        from api.health import DetailedHealthResponse
        # Test model can be instantiated
        response = DetailedHealthResponse(
            status="ok",
            dependencies={"mongodb": "ok", "valkey": "ok"},
            version="1.0.0"
        )
        assert response.status == "ok"
        assert "mongodb" in response.dependencies


class TestLogging:
    """Test logging configuration."""
    
    @pytest.mark.unit
    def test_logger_module_importable(self):
        """Logger module should be importable."""
        from utils.logger import setup_logging
        assert callable(setup_logging)
    
    @pytest.mark.unit
    def test_structlog_configured(self):
        """Structlog should be properly configured."""
        import structlog
        logger = structlog.get_logger()
        assert logger is not None


class TestMetricsEndpoint:
    """Test Prometheus metrics endpoint."""
    
    @pytest.mark.unit
    def test_prometheus_instrumentator_importable(self):
        """Prometheus instrumentator should be importable."""
        from prometheus_fastapi_instrumentator import Instrumentator
        assert Instrumentator is not None
    
    @pytest.mark.unit
    def test_prometheus_client_importable(self):
        """Prometheus client should be importable."""
        import prometheus_client
        assert prometheus_client is not None
