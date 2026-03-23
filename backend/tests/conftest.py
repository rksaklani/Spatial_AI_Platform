"""
Pytest configuration and shared fixtures for all tests.
"""
import asyncio
import os
import pytest
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock, patch
from bson import ObjectId
from datetime import datetime

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


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture
async def test_db():
    """Get test database instance."""
    from utils.database import Database
    db = Database.get_db()
    yield db
    # Cleanup after tests
    # Note: In production tests, you might want to clean up test data


@pytest.fixture
async def test_organization(test_db):
    """Create a test organization."""
    org_id = str(ObjectId())
    org = {
        "_id": org_id,
        "name": "Test Organization",
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    await test_db.organizations.insert_one(org)
    yield org
    # Cleanup
    await test_db.organizations.delete_one({"_id": org_id})


@pytest.fixture
async def test_user(test_db, test_organization):
    """Create a test user."""
    user_id = str(ObjectId())
    user = {
        "_id": user_id,
        "organization_id": test_organization["_id"],
        "email": "testuser@example.com",
        "name": "Test User",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.I0Z0wDfYj6z",
        "is_active": True,
        "created_at": datetime.utcnow()
    }
    await test_db.users.insert_one(user)
    yield user
    # Cleanup
    await test_db.users.delete_one({"_id": user_id})


@pytest.fixture
def auth_headers(test_user):
    """Generate authentication headers for test user."""
    from utils.security import create_access_token
    
    # Create JWT token for test user
    token = create_access_token(
        data={"sub": test_user["_id"], "email": test_user["email"]}
    )
    
    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for API tests.
    This is the main client fixture that tests should use.
    """
    from main import app
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ============================================================================
# Mock Service Fixtures (for tests without infrastructure)
# ============================================================================

@pytest.fixture(autouse=True)
def mock_valkey_for_collaboration():
    """
    Mock Valkey client for collaboration tests.
    This runs automatically for all tests to avoid Valkey connection issues.
    """
    from unittest.mock import MagicMock
    
    class MockValkeyClient:
        """Mock Valkey client that simulates Redis operations."""
        
        def __init__(self):
            self.data = {}
            self.sets = {}
            self.expirations = {}
        
        def ping(self):
            return True
        
        def setex(self, key, ttl, value):
            self.data[key] = value
            self.expirations[key] = ttl
            return True
        
        def get(self, key):
            return self.data.get(key)
        
        def set(self, key, value):
            self.data[key] = value
            return True
        
        def delete(self, key):
            if key in self.data:
                del self.data[key]
            if key in self.expirations:
                del self.expirations[key]
            return 1
        
        def sadd(self, key, *values):
            if key not in self.sets:
                self.sets[key] = set()
            for value in values:
                self.sets[key].add(value)
            return len(values)
        
        def srem(self, key, *values):
            if key in self.sets:
                for value in values:
                    self.sets[key].discard(value)
            return len(values)
        
        def smembers(self, key):
            return list(self.sets.get(key, set()))
        
        def scard(self, key):
            return len(self.sets.get(key, set()))
        
        def expire(self, key, ttl):
            self.expirations[key] = ttl
            return True
        
        def exists(self, key):
            return 1 if key in self.data else 0
        
        def keys(self, pattern):
            import fnmatch
            return [k for k in self.data.keys() if fnmatch.fnmatch(k, pattern)]
    
    mock_client = MockValkeyClient()
    
    # Patch the Valkey client getter
    with patch('utils.valkey_client.get_valkey_client', return_value=mock_client):
        # Also patch any direct imports
        with patch('services.collaboration.get_valkey_client', return_value=mock_client):
            yield mock_client


# ============================================================================
# Photo Inspector Test Fixtures
# ============================================================================

@pytest.fixture
async def test_scene(db, test_organization, test_user):
    """Create a test scene for photo tests."""
    scene_id = str(ObjectId())
    scene_doc = {
        "_id": scene_id,
        "organization_id": test_organization["_id"],
        "owner_id": test_user["_id"],
        "name": "Test Scene",
        "description": "Test scene for photo inspector",
        "source_type": "video",
        "original_filename": "test_video.mp4",
        "file_size_bytes": 1024000,
        "mime_type": "video/mp4",
        "source_path": f"videos/{test_organization['_id']}/{scene_id}/original.mp4",
        "status": "ready",
        "is_public": False,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    await db.scenes.insert_one(scene_doc)
    yield scene_doc
    
    # Cleanup
    await db.scenes.delete_one({"_id": scene_id})


@pytest.fixture
async def other_org_user(db):
    """Create a user from a different organization."""
    org_id = str(ObjectId())
    user_id = str(ObjectId())
    
    # Create organization
    org_doc = {
        "_id": org_id,
        "name": "Other Organization",
        "created_at": datetime.utcnow(),
    }
    await db.organizations.insert_one(org_doc)
    
    # Create user
    user_doc = {
        "_id": user_id,
        "organization_id": org_id,
        "email": "other@example.com",
        "name": "Other User",
        "created_at": datetime.utcnow(),
    }
    await db.users.insert_one(user_doc)
    
    # Generate token (simplified)
    token = "other-user-token"
    
    yield {"_id": user_id, "organization_id": org_id, "token": token}
    
    # Cleanup
    await db.users.delete_one({"_id": user_id})
    await db.organizations.delete_one({"_id": org_id})
