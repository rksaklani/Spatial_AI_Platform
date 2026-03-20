"""
Pytest configuration and shared fixtures for all tests.
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock, patch

# Set test environment variables before importing app modules
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("MONGODB_URL", "mongodb://localhost:27017")
os.environ.setdefault("DATABASE_NAME", "spatial_ai_platform_test")
os.environ.setdefault("VALKEY_HOST", "localhost")
os.environ.setdefault("VALKEY_PORT", "6379")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key-for-testing")

from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sync_client():
    """Synchronous test client for simple API tests (without lifespan)."""
    from fastapi import FastAPI
    from main import app
    
    # Create a test app without lifespan for unit tests
    test_app = FastAPI()
    
    # Copy routes from main app
    for route in app.routes:
        test_app.routes.append(route)
    
    # Copy middleware - handle different middleware formats
    for middleware in app.user_middleware:
        if hasattr(middleware, 'options'):
            test_app.add_middleware(middleware.cls, **middleware.options)
        elif hasattr(middleware, 'kwargs'):
            test_app.add_middleware(middleware.cls, **middleware.kwargs)
        else:
            test_app.add_middleware(middleware.cls)
    
    with TestClient(test_app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture
def simple_client():
    """Simple test client that doesn't require full app startup."""
    from fastapi import FastAPI
    from api.health import router as health_router
    
    test_app = FastAPI()
    test_app.include_router(health_router)
    
    @test_app.get("/")
    async def root():
        return {"message": "test", "status": "running", "version": "1.0.0"}
    
    with TestClient(test_app) as client:
        yield client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async test client for async endpoint tests."""
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def mock_db():
    """Mock database for unit tests."""
    mock = AsyncMock()
    mock.users = AsyncMock()
    mock.organizations = AsyncMock()
    mock.scenes = AsyncMock()
    mock.command = AsyncMock(return_value={"ok": 1})
    return mock


@pytest.fixture
def mock_valkey():
    """Mock Valkey client for unit tests."""
    mock = MagicMock()
    mock.ping.return_value = True
    mock.get.return_value = None
    mock.set.return_value = True
    mock.setex.return_value = True
    mock.delete.return_value = 1
    return mock


@pytest.fixture
def mock_minio():
    """Mock MinIO client for unit tests."""
    mock = MagicMock()
    mock.bucket_exists.return_value = True
    mock.is_connected.return_value = True
    return mock


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "TestPassword123!"
    }


@pytest.fixture
def sample_user_in_db():
    """Sample user document as stored in database."""
    import uuid
    from datetime import datetime
    return {
        "_id": str(uuid.uuid4()),
        "email": "test@example.com",
        "full_name": "Test User",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.I0Z0wDfYj6z",
        "is_active": True,
        "organization_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
