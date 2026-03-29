"""Tests for Task 24: Real-time collaboration."""
import pytest
import asyncio
import json
import time
from unittest.mock import Mock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from bson import ObjectId

from main import app
from utils.database import Database
from services.collaboration import collaboration_service
from models.user import UserInDB
from models.organization import OrganizationInDB
from models.scene import SceneInDB


# Mock Valkey client for tests
class MockValkeyClient:
    """Mock Valkey client for testing."""
    
    def __init__(self):
        self.data = {}
        self.sets = {}
    
    def setex(self, key, ttl, value):
        self.data[key] = value
        return True
    
    def get(self, key):
        return self.data.get(key)
    
    def delete(self, key):
        if key in self.data:
            del self.data[key]
        return True
    
    def sadd(self, key, value):
        if key not in self.sets:
            self.sets[key] = set()
        self.sets[key].add(value)
        return True
    
    def srem(self, key, value):
        if key in self.sets:
            self.sets[key].discard(value)
        return True
    
    def smembers(self, key):
        return list(self.sets.get(key, set()))
    
    def scard(self, key):
        return len(self.sets.get(key, set()))
    
    def expire(self, key, ttl):
        return True


@pytest.fixture(autouse=True)
def mock_valkey():
    """Mock Valkey client for all tests."""
    mock_client = MockValkeyClient()
    with patch.object(collaboration_service, 'valkey', mock_client):
        yield mock_client


@pytest.fixture
async def test_organization():
    """Create a test organization."""
    db = Database.get_db()
    org = OrganizationInDB(
        name="Test Collaboration Org",
        created_at=time.time(),
        updated_at=time.time()
    )
    result = await db.organizations.insert_one(org.dict(by_alias=True))
    org_id = result.inserted_id
    
    yield str(org_id)
    
    # Cleanup
    await db.organizations.delete_one({"_id": org_id})


@pytest.fixture
async def test_users(test_organization):
    """Create test users."""
    db = Database.get_db()
    users = []
    
    for i in range(3):
        user = UserInDB(
            organization_id=ObjectId(test_organization),
            email=f"collab_user{i}@test.com",
            name=f"Collab User {i}",
            hashed_password="dummy_hash",
            is_active=True,
            created_at=time.time()
        )
        result = await db.users.insert_one(user.dict(by_alias=True))
        users.append(str(result.inserted_id))
    
    yield users
    
    # Cleanup
    for user_id in users:
        await db.users.delete_one({"_id": ObjectId(user_id)})


@pytest.fixture
async def test_scene(test_organization):
    """Create a test scene."""
    db = Database.get_db()
    scene = SceneInDB(
        organization_id=ObjectId(test_organization),
        user_id=ObjectId(),
        name="Test Collaboration Scene",
        source_type="video",
        source_format="mp4",
        status="completed",
        created_at=time.time(),
        updated_at=time.time()
    )
    result = await db.scenes.insert_one(scene.dict(by_alias=True))
    scene_id = result.inserted_id
    
    yield str(scene_id)
    
    # Cleanup
    await db.scenes.delete_one({"_id": scene_id})


class TestCollaborationService:
    """Test collaboration service functionality."""
    
    @pytest.mark.asyncio
    async def test_join_scene(self, test_scene, test_users):
        """Test user joining a scene."""
        scene_id = test_scene
        user_id = test_users[0]
        user_name = "Test User"
        
        # Mock websocket
        class MockWebSocket:
            pass
        
        websocket = MockWebSocket()
        
        # Join scene
        session = await collaboration_service.join_scene(
            scene_id=scene_id,
            user_id=user_id,
            user_name=user_name,
            websocket=websocket
        )
        
        assert session.user_id == user_id
        assert session.user_name == user_name
        assert session.scene_id == scene_id
        assert session.joined_at > 0
        assert session.last_heartbeat > 0
        
        # Verify session in Valkey
        session_key = collaboration_service._get_session_key(scene_id, user_id)
        session_data = collaboration_service.valkey.get(session_key)
        assert session_data is not None
        
        # Verify user in scene users set
        scene_users_key = collaboration_service._get_scene_users_key(scene_id)
        user_count = collaboration_service.valkey.scard(scene_users_key)
        assert user_count == 1
        
        # Cleanup
        await collaboration_service.leave_scene(scene_id, user_id, websocket)
    
    @pytest.mark.asyncio
    async def test_leave_scene(self, test_scene, test_users):
        """Test user leaving a scene."""
        scene_id = test_scene
        user_id = test_users[0]
        user_name = "Test User"
        
        class MockWebSocket:
            pass
        
        websocket = MockWebSocket()
        
        # Join and then leave
        await collaboration_service.join_scene(
            scene_id=scene_id,
            user_id=user_id,
            user_name=user_name,
            websocket=websocket
        )
        
        await collaboration_service.leave_scene(scene_id, user_id, websocket)
        
        # Verify session removed from Valkey
        session_key = collaboration_service._get_session_key(scene_id, user_id)
        session_data = collaboration_service.valkey.get(session_key)
        assert session_data is None
        
        # Verify user removed from scene users set
        scene_users_key = collaboration_service._get_scene_users_key(scene_id)
        user_count = collaboration_service.valkey.scard(scene_users_key)
        assert user_count == 0
    
    @pytest.mark.asyncio
    async def test_update_heartbeat(self, test_scene, test_users):
        """Test updating user heartbeat."""
        scene_id = test_scene
        user_id = test_users[0]
        user_name = "Test User"
        
        class MockWebSocket:
            pass
        
        websocket = MockWebSocket()
        
        # Join scene
        session = await collaboration_service.join_scene(
            scene_id=scene_id,
            user_id=user_id,
            user_name=user_name,
            websocket=websocket
        )
        
        initial_heartbeat = session.last_heartbeat
        
        # Wait a bit
        await asyncio.sleep(0.1)
        
        # Update heartbeat
        await collaboration_service.update_heartbeat(scene_id, user_id)
        
        # Verify heartbeat updated
        session_key = collaboration_service._get_session_key(scene_id, user_id)
        session_data = collaboration_service.valkey.get(session_key)
        session_dict = json.loads(session_data)
        
        assert session_dict['last_heartbeat'] > initial_heartbeat
        
        # Cleanup
        await collaboration_service.leave_scene(scene_id, user_id, websocket)
    
    @pytest.mark.asyncio
    async def test_update_cursor_position(self, test_scene, test_users):
        """Test updating user cursor position."""
        scene_id = test_scene
        user_id = test_users[0]
        user_name = "Test User"
        
        class MockWebSocket:
            pass
        
        websocket = MockWebSocket()
        
        # Join scene
        await collaboration_service.join_scene(
            scene_id=scene_id,
            user_id=user_id,
            user_name=user_name,
            websocket=websocket
        )
        
        # Update cursor position
        position = (1.5, 2.5, 3.5)
        await collaboration_service.update_cursor_position(scene_id, user_id, position)
        
        # Verify position updated
        session_key = collaboration_service._get_session_key(scene_id, user_id)
        session_data = collaboration_service.valkey.get(session_key)
        session_dict = json.loads(session_data)
        
        assert session_dict['cursor_position'] == list(position)
        
        # Cleanup
        await collaboration_service.leave_scene(scene_id, user_id, websocket)
    
    @pytest.mark.asyncio
    async def test_get_active_users(self, test_scene, test_users):
        """Test getting active users in a scene."""
        scene_id = test_scene
        
        class MockWebSocket:
            pass
        
        websockets = [MockWebSocket() for _ in range(3)]
        
        # Join multiple users
        for i, user_id in enumerate(test_users):
            await collaboration_service.join_scene(
                scene_id=scene_id,
                user_id=user_id,
                user_name=f"User {i}",
                websocket=websockets[i]
            )
        
        # Get active users
        active_users = await collaboration_service.get_active_users(scene_id)
        
        assert len(active_users) == 3
        user_ids = [user['user_id'] for user in active_users]
        for user_id in test_users:
            assert user_id in user_ids
        
        # Cleanup
        for i, user_id in enumerate(test_users):
            await collaboration_service.leave_scene(scene_id, user_id, websockets[i])
    
    @pytest.mark.asyncio
    async def test_get_user_count(self, test_scene, test_users):
        """Test getting user count in a scene."""
        scene_id = test_scene
        
        class MockWebSocket:
            pass
        
        websockets = [MockWebSocket() for _ in range(3)]
        
        # Initially no users
        count = await collaboration_service.get_user_count(scene_id)
        assert count == 0
        
        # Join users one by one
        for i, user_id in enumerate(test_users):
            await collaboration_service.join_scene(
                scene_id=scene_id,
                user_id=user_id,
                user_name=f"User {i}",
                websocket=websockets[i]
            )
            count = await collaboration_service.get_user_count(scene_id)
            assert count == i + 1
        
        # Cleanup
        for i, user_id in enumerate(test_users):
            await collaboration_service.leave_scene(scene_id, user_id, websockets[i])
    
    @pytest.mark.asyncio
    async def test_concurrent_user_limit(self, test_scene):
        """Test 50 concurrent user limit per scene."""
        scene_id = test_scene
        
        class MockWebSocket:
            pass
        
        # Join 50 users
        websockets = []
        for i in range(50):
            ws = MockWebSocket()
            websockets.append(ws)
            await collaboration_service.join_scene(
                scene_id=scene_id,
                user_id=f"user_{i}",
                user_name=f"User {i}",
                websocket=ws
            )
        
        # Verify count
        count = await collaboration_service.get_user_count(scene_id)
        assert count == 50
        
        # Cleanup
        for i in range(50):
            await collaboration_service.leave_scene(scene_id, f"user_{i}", websockets[i])


class TestWebSocketEndpoint:
    """Test WebSocket collaboration endpoint."""
    
    def test_websocket_connection(self, test_scene):
        """Test WebSocket connection establishment."""
        client = TestClient(app)
        scene_id = test_scene
        
        with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as websocket:
            # Send join message
            websocket.send_json({
                "type": "join",
                "user_id": "test_user_1",
                "user_name": "Test User 1"
            })
            
            # Receive active users list
            data = websocket.receive_json()
            assert data["type"] == "active_users"
            assert isinstance(data["users"], list)
    
    def test_websocket_user_presence(self, test_scene):
        """Test user presence broadcasting."""
        client = TestClient(app)
        scene_id = test_scene
        
        # Connect first user
        with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws1:
            ws1.send_json({
                "type": "join",
                "user_id": "user_1",
                "user_name": "User 1"
            })
            
            # Receive active users
            data = ws1.receive_json()
            assert data["type"] == "active_users"
            
            # Connect second user
            with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws2:
                ws2.send_json({
                    "type": "join",
                    "user_id": "user_2",
                    "user_name": "User 2"
                })
                
                # First user should receive user_joined event
                data = ws1.receive_json()
                assert data["type"] == "user_joined"
                assert data["user_id"] == "user_2"
                assert data["user_name"] == "User 2"
    
    def test_websocket_cursor_update(self, test_scene):
        """Test cursor position broadcasting."""
        client = TestClient(app)
        scene_id = test_scene
        
        with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws1:
            ws1.send_json({
                "type": "join",
                "user_id": "user_1",
                "user_name": "User 1"
            })
            ws1.receive_json()  # active_users
            
            with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws2:
                ws2.send_json({
                    "type": "join",
                    "user_id": "user_2",
                    "user_name": "User 2"
                })
                ws1.receive_json()  # user_joined
                ws2.receive_json()  # active_users
                
                # User 1 sends cursor update
                ws1.send_json({
                    "type": "cursor_move",
                    "position": [1.0, 2.0, 3.0]
                })
                
                # User 2 should receive cursor update
                data = ws2.receive_json()
                assert data["type"] == "cursor_update"
                assert data["user_id"] == "user_1"
                assert data["position"] == [1.0, 2.0, 3.0]
    
    def test_websocket_annotation_sync(self, test_scene):
        """Test annotation synchronization."""
        client = TestClient(app)
        scene_id = test_scene
        
        with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws1:
            ws1.send_json({
                "type": "join",
                "user_id": "user_1",
                "user_name": "User 1"
            })
            ws1.receive_json()  # active_users
            
            with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws2:
                ws2.send_json({
                    "type": "join",
                    "user_id": "user_2",
                    "user_name": "User 2"
                })
                ws1.receive_json()  # user_joined
                ws2.receive_json()  # active_users
                
                # User 1 creates annotation
                annotation = {
                    "id": "test_annotation_1",
                    "type": "comment",
                    "position": [1.0, 2.0, 3.0],
                    "content": "Test annotation"
                }
                ws1.send_json({
                    "type": "annotation_create",
                    "annotation": annotation
                })
                
                # User 2 should receive annotation_created
                data = ws2.receive_json()
                assert data["type"] == "annotation_created"
                assert data["annotation"]["id"] == "test_annotation_1"
                
                # User 1 updates annotation
                ws1.send_json({
                    "type": "annotation_update",
                    "annotation_id": "test_annotation_1",
                    "changes": {"content": "Updated content"}
                })
                
                # User 2 should receive annotation_updated
                data = ws2.receive_json()
                assert data["type"] == "annotation_updated"
                assert data["annotation_id"] == "test_annotation_1"
                assert data["changes"]["content"] == "Updated content"
                
                # User 1 deletes annotation
                ws1.send_json({
                    "type": "annotation_delete",
                    "annotation_id": "test_annotation_1"
                })
                
                # User 2 should receive annotation_deleted
                data = ws2.receive_json()
                assert data["type"] == "annotation_deleted"
                assert data["annotation_id"] == "test_annotation_1"
    
    def test_websocket_heartbeat(self, test_scene):
        """Test heartbeat mechanism."""
        client = TestClient(app)
        scene_id = test_scene
        
        with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as websocket:
            websocket.send_json({
                "type": "join",
                "user_id": "test_user",
                "user_name": "Test User"
            })
            websocket.receive_json()  # active_users
            
            # Send heartbeat
            websocket.send_json({"type": "heartbeat"})
            
            # Should not receive any response for heartbeat
            # (heartbeat is silent, just updates timestamp)
    
    def test_websocket_disconnection(self, test_scene):
        """Test graceful disconnection handling."""
        client = TestClient(app)
        scene_id = test_scene
        
        with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws1:
            ws1.send_json({
                "type": "join",
                "user_id": "user_1",
                "user_name": "User 1"
            })
            ws1.receive_json()  # active_users
            
            with client.websocket_connect(f"/api/v1/scenes/{scene_id}/collaborate") as ws2:
                ws2.send_json({
                    "type": "join",
                    "user_id": "user_2",
                    "user_name": "User 2"
                })
                ws1.receive_json()  # user_joined
                ws2.receive_json()  # active_users
                
                # Close ws2
                ws2.close()
                
                # ws1 should receive user_left event
                data = ws1.receive_json()
                assert data["type"] == "user_left"
                assert data["user_id"] == "user_2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
