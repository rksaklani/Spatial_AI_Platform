"""
Test script for Valkey connection, configuration, and caching operations.

This script verifies:
1. Connection to Valkey server
2. Connection pooling functionality
3. Basic caching operations (get, set, delete)
4. TTL and expiration
5. JSON caching
6. Scene-specific caching (tiles, metadata)
7. Session management
8. Memory statistics and configuration
"""

import sys
import time
import json
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.valkey_client import get_valkey_client
from utils.config import settings


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_connection():
    """Test basic connection to Valkey."""
    print_section("Test 1: Connection")
    
    client = get_valkey_client()
    
    # Test ping
    result = client.ping()
    print(f"✓ Ping successful: {result}")
    
    # Get server info
    info = client.get_info()
    print(f"✓ Server version: {info.get('redis_version', 'unknown')}")
    print(f"✓ Connected clients: {info.get('connected_clients', 0)}")
    print(f"✓ Uptime (seconds): {info.get('uptime_in_seconds', 0)}")
    
    return True


def test_connection_pool():
    """Test connection pooling."""
    print_section("Test 2: Connection Pooling")
    
    client = get_valkey_client()
    
    print(f"✓ Pool configuration:")
    print(f"  - Host: {settings.valkey_host}")
    print(f"  - Port: {settings.valkey_port}")
    print(f"  - Database: {settings.valkey_db}")
    print(f"  - Max connections: {settings.valkey_max_connections}")
    print(f"  - Socket timeout: {settings.valkey_socket_timeout}s")
    print(f"  - Connect timeout: {settings.valkey_connect_timeout}s")
    
    # Test multiple operations using the pool
    for i in range(5):
        key = f"pool_test_{i}"
        client.set(key, f"value_{i}", ttl=10)
    
    print(f"✓ Successfully performed 5 operations using connection pool")
    
    # Cleanup
    for i in range(5):
        client.delete(f"pool_test_{i}")
    
    return True


def test_basic_operations():
    """Test basic key-value operations."""
    print_section("Test 3: Basic Operations")
    
    client = get_valkey_client()
    
    # Test SET
    key = "test_key"
    value = "test_value"
    result = client.set(key, value)
    print(f"✓ SET '{key}' = '{value}': {result}")
    
    # Test GET
    retrieved = client.get(key)
    print(f"✓ GET '{key}' = '{retrieved.decode('utf-8')}'")
    assert retrieved.decode('utf-8') == value, "Value mismatch!"
    
    # Test EXISTS
    exists = client.exists(key)
    print(f"✓ EXISTS '{key}': {exists}")
    assert exists == 1, "Key should exist!"
    
    # Test DELETE
    deleted = client.delete(key)
    print(f"✓ DELETE '{key}': {deleted} key(s) deleted")
    
    # Verify deletion
    exists = client.exists(key)
    print(f"✓ EXISTS '{key}' after delete: {exists}")
    assert exists == 0, "Key should not exist!"
    
    return True


def test_ttl_expiration():
    """Test TTL and expiration."""
    print_section("Test 4: TTL and Expiration")
    
    client = get_valkey_client()
    
    # Set key with TTL
    key = "ttl_test"
    value = "expires_soon"
    ttl = 5
    client.set(key, value, ttl=ttl)
    print(f"✓ SET '{key}' with TTL={ttl}s")
    
    # Check TTL
    remaining = client.ttl(key)
    print(f"✓ TTL '{key}': {remaining}s remaining")
    assert remaining > 0 and remaining <= ttl, "TTL should be positive and <= initial TTL"
    
    # Wait and check again
    time.sleep(2)
    remaining = client.ttl(key)
    print(f"✓ TTL '{key}' after 2s: {remaining}s remaining")
    
    # Test EXPIRE
    client.expire(key, 10)
    remaining = client.ttl(key)
    print(f"✓ TTL '{key}' after EXPIRE 10s: {remaining}s remaining")
    
    # Cleanup
    client.delete(key)
    
    return True


def test_json_caching():
    """Test JSON serialization and caching."""
    print_section("Test 5: JSON Caching")
    
    client = get_valkey_client()
    
    # Test JSON object
    key = "json_test"
    data = {
        "scene_id": "test-scene-123",
        "name": "Test Scene",
        "status": "completed",
        "metadata": {
            "gaussian_count": 1000000,
            "tile_count": 50
        }
    }
    
    result = client.set_json(key, data, ttl=60)
    print(f"✓ SET JSON '{key}': {result}")
    
    # Retrieve and verify
    retrieved = client.get_json(key)
    print(f"✓ GET JSON '{key}':")
    print(f"  {json.dumps(retrieved, indent=2)}")
    
    assert retrieved == data, "JSON data mismatch!"
    print(f"✓ JSON data matches original")
    
    # Cleanup
    client.delete(key)
    
    return True


def test_tile_caching():
    """Test scene tile caching."""
    print_section("Test 6: Tile Caching")
    
    client = get_valkey_client()
    
    scene_id = "test-scene-456"
    tile_id = "L0_X0_Y0_Z0_high"
    tile_data = b"fake_tile_binary_data_12345"
    
    # Cache tile
    result = client.cache_tile(scene_id, tile_id, tile_data, ttl=3600)
    print(f"✓ Cache tile '{tile_id}' for scene '{scene_id}': {result}")
    
    # Retrieve tile
    retrieved = client.get_tile(scene_id, tile_id)
    print(f"✓ Retrieved tile: {len(retrieved)} bytes")
    assert retrieved == tile_data, "Tile data mismatch!"
    
    # Check TTL
    key = f"tile:{scene_id}:{tile_id}"
    ttl = client.ttl(key)
    print(f"✓ Tile TTL: {ttl}s")
    
    # Cleanup
    client.delete(key)
    
    return True


def test_scene_metadata_caching():
    """Test scene metadata caching."""
    print_section("Test 7: Scene Metadata Caching")
    
    client = get_valkey_client()
    
    scene_id = "test-scene-789"
    metadata = {
        "sceneId": scene_id,
        "name": "Test Scene",
        "status": "completed",
        "bounds": {
            "min": [0, 0, 0],
            "max": [10, 10, 10]
        },
        "tileCount": 25,
        "gaussianCount": 5000000
    }
    
    # Cache metadata
    result = client.cache_scene_metadata(scene_id, metadata, ttl=300)
    print(f"✓ Cache scene metadata for '{scene_id}': {result}")
    
    # Retrieve metadata
    retrieved = client.get_scene_metadata(scene_id)
    print(f"✓ Retrieved metadata:")
    print(f"  {json.dumps(retrieved, indent=2)}")
    assert retrieved == metadata, "Metadata mismatch!"
    
    # Cleanup
    key = f"scene:metadata:{scene_id}"
    client.delete(key)
    
    return True


def test_session_management():
    """Test session management."""
    print_section("Test 8: Session Management")
    
    client = get_valkey_client()
    
    scene_id = "test-scene-session"
    user_id = "user-123"
    session_data = {
        "userId": user_id,
        "userName": "Test User",
        "joinedAt": time.time(),
        "lastHeartbeat": time.time()
    }
    
    # Create session
    result = client.create_session(scene_id, user_id, session_data, ttl=3600)
    print(f"✓ Create session for user '{user_id}' in scene '{scene_id}': {result}")
    
    # Get session
    retrieved = client.get_session(scene_id, user_id)
    print(f"✓ Retrieved session:")
    print(f"  {json.dumps(retrieved, indent=2)}")
    assert retrieved["userId"] == user_id, "Session data mismatch!"
    
    # Create multiple sessions
    for i in range(3):
        uid = f"user-{i}"
        data = {"userId": uid, "userName": f"User {i}"}
        client.create_session(scene_id, uid, data, ttl=3600)
    
    # Get active sessions
    active = client.get_active_sessions(scene_id)
    print(f"✓ Active sessions in scene '{scene_id}': {len(active)} users")
    print(f"  Users: {active}")
    
    # Delete session
    result = client.delete_session(scene_id, user_id)
    print(f"✓ Delete session for user '{user_id}': {result}")
    
    # Cleanup
    for i in range(3):
        client.delete_session(scene_id, f"user-{i}")
    
    return True


def test_memory_stats():
    """Test memory statistics and configuration."""
    print_section("Test 9: Memory Statistics")
    
    client = get_valkey_client()
    
    stats = client.get_memory_stats()
    print(f"✓ Memory statistics:")
    print(f"  - Used memory: {stats.get('used_memory_human', 'unknown')}")
    print(f"  - Peak memory: {stats.get('used_memory_peak_human', 'unknown')}")
    print(f"  - Max memory: {stats.get('maxmemory_human', 'unknown')}")
    print(f"  - Eviction policy: {stats.get('maxmemory_policy', 'unknown')}")
    
    # Verify configuration
    info = client.get_info()
    print(f"\n✓ Persistence configuration:")
    print(f"  - RDB enabled: {info.get('rdb_last_save_time', 0) > 0}")
    print(f"  - AOF enabled: {info.get('aof_enabled', 0) == 1}")
    
    return True


def test_persistence():
    """Test persistence configuration."""
    print_section("Test 10: Persistence Configuration")
    
    client = get_valkey_client()
    
    info = client.get_info('persistence')
    
    print(f"✓ RDB (Snapshot) Persistence:")
    print(f"  - Last save time: {info.get('rdb_last_save_time', 0)}")
    print(f"  - Changes since last save: {info.get('rdb_changes_since_last_save', 0)}")
    print(f"  - Last save status: {info.get('rdb_last_bgsave_status', 'unknown')}")
    
    print(f"\n✓ AOF (Append-Only File) Persistence:")
    print(f"  - AOF enabled: {info.get('aof_enabled', 0) == 1}")
    print(f"  - AOF rewrite in progress: {info.get('aof_rewrite_in_progress', 0) == 1}")
    print(f"  - AOF last write status: {info.get('aof_last_write_status', 'unknown')}")
    
    return True


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("  VALKEY CONNECTION AND CACHING TEST SUITE")
    print("="*60)
    
    tests = [
        ("Connection", test_connection),
        ("Connection Pooling", test_connection_pool),
        ("Basic Operations", test_basic_operations),
        ("TTL and Expiration", test_ttl_expiration),
        ("JSON Caching", test_json_caching),
        ("Tile Caching", test_tile_caching),
        ("Scene Metadata Caching", test_scene_metadata_caching),
        ("Session Management", test_session_management),
        ("Memory Statistics", test_memory_stats),
        ("Persistence Configuration", test_persistence),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            test_func()
            passed += 1
            print(f"\n✓ {name} test PASSED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} test FAILED: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print_section("Test Summary")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓ All tests passed successfully!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
