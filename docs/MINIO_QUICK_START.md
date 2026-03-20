# MinIO Quick Start Guide

Quick reference for deploying and configuring MinIO object storage.

## Prerequisites

- Docker and Docker Compose installed
- Backend Python environment set up (see Task 1.1)

## Quick Setup (3 Steps)

### Step 1: Start MinIO Container

```bash
# Start MinIO service
docker-compose up -d minio

# Verify MinIO is running
docker-compose ps minio
```

Expected output:
```
NAME                  STATUS              PORTS
spatial-ai-minio      Up (healthy)        0.0.0.0:9000->9000/tcp, 0.0.0.0:9001->9001/tcp
```

### Step 2: Initialize Buckets

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run initialization script
python scripts/init_minio.py
```

Expected output:
```
✓ MinIO initialization complete - All tests passed
Buckets: ['videos', 'frames', 'depth', 'scenes', 'reports']
```

### Step 3: Verify Configuration

```bash
# Run verification script
python scripts/test_minio.py
```

Expected output:
```
✓ All buckets verified successfully
Total: 5, Successful: 5, Failed: 0
```

## Access MinIO Console

Open your browser to: http://localhost:9001

Login credentials:
- **Username**: `minioadmin`
- **Password**: `minioadmin123`

## Bucket Overview

| Bucket | Purpose | Example Path |
|--------|---------|--------------|
| `videos` | Uploaded videos | `{orgId}/{sceneId}/original.mp4` |
| `frames` | Extracted frames | `{sceneId}/frame_0000.jpg` |
| `depth` | Depth maps | `{sceneId}/depth_0000.png` |
| `scenes` | 3D scenes & tiles | `{sceneId}/tiles/0/0_0_0_high.ply` |
| `reports` | PDF reports | `{sceneId}/report_{timestamp}.pdf` |

## Python Usage Example

```python
from utils.minio_client import get_minio_client

# Get client
client = get_minio_client()

# Upload a file
client.upload_file(
    bucket_name="videos",
    object_name="org123/scene456/video.mp4",
    file_path="/path/to/video.mp4",
    content_type="video/mp4"
)

# Download a file
client.download_file(
    bucket_name="videos",
    object_name="org123/scene456/video.mp4",
    file_path="/path/to/save/video.mp4"
)
```

## Troubleshooting

### MinIO won't start

```bash
# Check Docker is running
docker ps

# Check MinIO logs
docker-compose logs minio

# Restart MinIO
docker-compose restart minio
```

### Can't connect from Python

```bash
# Check environment variables
echo $MINIO_ENDPOINT
echo $MINIO_ACCESS_KEY

# Test connectivity
curl http://localhost:9000/minio/health/live
```

### Bucket creation fails

```bash
# Check MinIO is healthy
docker-compose ps minio

# Check storage space
docker-compose exec minio df -h /data

# Recreate MinIO container
docker-compose down minio
docker-compose up -d minio
```

## Configuration Files

- **Docker Compose**: `docker-compose.yml` - MinIO service definition
- **Python Client**: `backend/utils/minio_client.py` - MinIO client wrapper
- **Init Script**: `backend/scripts/init_minio.py` - Bucket initialization
- **Test Script**: `backend/scripts/test_minio.py` - Verification tests

## Environment Variables

```bash
# MinIO Server (in docker-compose.yml)
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=minioadmin123

# Application (in docker-compose.yml services)
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin123
MINIO_SECURE=false
```

## Next Steps

After MinIO is configured:
1. ✓ Task 1.6 complete - MinIO deployed and configured
2. → Task 1.7 - Deploy and configure Valkey (Redis)
3. → Task 1.8 - Set up Celery task queue

## Full Documentation

For detailed information, see [MINIO_SETUP.md](MINIO_SETUP.md)
