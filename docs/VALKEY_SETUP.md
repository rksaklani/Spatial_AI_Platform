# Valkey Setup and Configuration

This document describes the Valkey (Redis-compatible) caching and session management setup for the Spatial AI Platform.

## Overview

Valkey is used for:
- Tile caching (1 hour TTL)
- Scene metadata caching (5 minutes TTL)
- Session management for real-time collaboration
- Celery job queue and result backend

## Configuration

### Docker Compose

Valkey is deployed as a Docker container with the following configuration:

```yaml
redis:
  image: valkey/valkey:7.2
  container_name: spatial-ai-redis
  ports:
    - "6379:6379"
  volumes:
    - redis_data:/data
    - ./backend/config/valkey.conf:/usr/local/etc/valkey/valkey.conf
  command: valkey-server /usr/local/etc/valkey/valkey.conf
  environment:
    - VALKEY_MAXMEMORY=2gb
    - VALKEY_MAXMEMORY_POLICY=allkeys-lru
  deploy:
    resources:
      limits:
        memory: 2.5G
      reservations:
        memory: 512M
```

### Persistence

Valkey is configured with dual persistence:

**RDB (Snapshots):**
- Save after 900s if ≥1 key changed
- Save after 300s if ≥10 keys changed
- Save after 60s if ≥10,000 keys changed

**AOF (Append-Only File):**
- Enabled with `everysec` fsync policy
- Automatic rewrite at 100% growth and 64MB minimum size

### Memory Management

- **Max Memory:** 2GB
- **Eviction Policy:** allkeys-lru (Least Recently Used)
- **Container Limit:** 2.5GB (allows overhead)

### Connection Pooling

The Python client uses connection pooling:

```python
VALKEY_HOST = "localhost"
VALKEY_PORT = 6379
VALKEY_DB = 0
VALKEY_MAX_CONNECTIONS = 50
VALKEY_SOCKET_TIMEOUT = 5
VALKEY_CONNECT_TIMEOUT = 5
```

## Usage

### Python Client

```python
from utils.valkey_client import get_valkey_client

client = get_valkey_client()

# Basic operations
client.set("key", "value", ttl=60)
value = client.get("key")
client.delete("key")

# JSON caching
client.set_json("metadata", {"scene_id": "123"}, ttl=300)
data = client.get_json("metadata")

# Tile caching
client.cache_tile("scene-123", "L0_X0_Y0_Z0_high", tile_data, ttl=3600)
tile = client.get_tile("scene-123", "L0_X0_Y0_Z0_high")

# Scene metadata
client.cache_scene_metadata("scene-123", metadata, ttl=300)
metadata = client.get_scene_metadata("scene-123")

# Session management
client.create_session("scene-123", "user-456", session_data, ttl=3600)
session = client.get_session("scene-123", "user-456")
active_users = client.get_active_sessions("scene-123")
```

## Testing

Run the test suite to verify Valkey configuration:

```bash
# Start Valkey container
docker-compose up -d redis

# Run tests
cd backend
python scripts/test_valkey.py
```

The test suite verifies:
1. Connection and ping
2. Connection pooling
3. Basic operations (get, set, delete, exists)
4. TTL and expiration
5. JSON caching
6. Tile caching
7. Scene metadata caching
8. Session management
9. Memory statistics
10. Persistence configuration

## Monitoring

### Memory Statistics

```python
client = get_valkey_client()
stats = client.get_memory_stats()

print(f"Used: {stats['used_memory_human']}")
print(f"Peak: {stats['used_memory_peak_human']}")
print(f"Max: {stats['maxmemory_human']}")
print(f"Policy: {stats['maxmemory_policy']}")
```

### Server Information

```python
info = client.get_info()
print(f"Version: {info['redis_version']}")
print(f"Clients: {info['connected_clients']}")
print(f"Uptime: {info['uptime_in_seconds']}s")
```

## Key Patterns

The platform uses the following key naming conventions:

- **Tiles:** `tile:{scene_id}:{tile_id}`
- **Scene Metadata:** `scene:metadata:{scene_id}`
- **Sessions:** `session:{scene_id}:{user_id}`
- **Celery Tasks:** `celery:task:{task_id}`

## Performance

### Expected Performance

- **Cached tile retrieval:** <100ms
- **Session lookup:** <10ms
- **Metadata caching:** <5ms

### Optimization

- Connection pooling reduces overhead
- LRU eviction prevents memory exhaustion
- Dual persistence ensures data durability
- Health checks ensure availability

## Troubleshooting

### Connection Issues

```bash
# Check if Valkey is running
docker ps | grep spatial-ai-redis

# Check logs
docker logs spatial-ai-redis

# Test connection
docker exec spatial-ai-redis valkey-cli ping
```

### Memory Issues

```bash
# Check memory usage
docker exec spatial-ai-redis valkey-cli INFO memory

# Flush database (caution!)
docker exec spatial-ai-redis valkey-cli FLUSHDB
```

### Persistence Issues

```bash
# Check persistence status
docker exec spatial-ai-redis valkey-cli INFO persistence

# Force save
docker exec spatial-ai-redis valkey-cli BGSAVE
```

## Production Considerations

### Security

- Enable password authentication in production
- Use TLS for encrypted connections
- Restrict network access with firewall rules

### Scaling

- Consider Redis Cluster for horizontal scaling
- Use Redis Sentinel for high availability
- Monitor memory usage and adjust limits

### Backup

- RDB snapshots are stored in `/data/dump.rdb`
- AOF file is stored in `/data/appendonly.aof`
- Back up these files regularly

## References

- [Valkey Documentation](https://valkey.io/docs/)
- [Redis Protocol Compatibility](https://redis.io/docs/reference/protocol-spec/)
- [Connection Pooling Best Practices](https://redis.io/docs/manual/patterns/connection-pool/)
