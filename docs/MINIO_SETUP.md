# MinIO Object Storage Setup

This document describes the MinIO object storage configuration for the Spatial AI Platform.

## Overview

MinIO provides S3-compatible object storage for the platform. It stores:
- **videos**: Uploaded video files
- **frames**: Extracted video frames
- **depth**: Generated depth maps
- **scenes**: Reconstructed 3D scenes and tiles
- **reports**: Generated PDF reports

## Configuration

### Environment Variables

MinIO is configured via environment variables in `docker-compose.yml`:

```bash
MINIO_ENDPOINT=minio:9000          # MinIO server endpoint
MINIO_ACCESS_KEY=minioadmin        # Access key (change in production)
MINIO_SECRET_KEY=minioadmin123     # Secret key (change in production)
MINIO_SECURE=false                 # Use HTTPS (set to true in production)
```

### Docker Compose Service

MinIO runs as a Docker container with:
- **API Port**: 9000 (S3-compatible API)
- **Console Port**: 9001 (Web UI)
- **Storage**: Persistent volume at `/data`
- **Health Check**: HTTP endpoint monitoring

## Deployment

### 1. Start MinIO Container

```bash
# Start MinIO service
docker-compose up -d minio

# Check MinIO status
docker-compose ps minio

# View MinIO logs
docker-compose logs -f minio
```

### 2. Initialize Buckets

Run the initialization script to create required buckets:

```bash
# From the backend directory
cd backend

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Run initialization script
python scripts/init_minio.py
```

The script will:
1. Connect to MinIO
2. Create all required buckets
3. Test upload/download operations
4. Verify bucket accessibility

### 3. Verify Configuration

Run the verification script to check MinIO status:

```bash
python scripts/test_minio.py
```

## Bucket Structure

### videos
Stores uploaded video files organized by organization and scene:
```
videos/
└── {organizationId}/
    └── {sceneId}/
        └── original.{ext}
```

### frames
Stores extracted video frames:
```
frames/
└── {sceneId}/
    ├── frame_0000.jpg
    ├── frame_0001.jpg
    └── ...
```

### depth
Stores depth maps:
```
depth/
└── {sceneId}/
    ├── depth_0000.png
    ├── depth_0001.png
    └── ...
```

### scenes
Stores reconstructed 3D scenes:
```
scenes/
└── {sceneId}/
    ├── sparse/
    │   ├── cameras.bin
    │   ├── images.bin
    │   └── points3D.bin
    ├── gaussian/
    │   └── scene.ply
    └── tiles/
        ├── 0/
        ├── 1/
        └── metadata.json
```

### reports
Stores generated PDF reports:
```
reports/
└── {sceneId}/
    └── report_{timestamp}.pdf
```

## Access via Web Console

MinIO provides a web console for manual management:

1. Open browser to: http://localhost:9001
2. Login with credentials:
   - Username: `minioadmin`
   - Password: `minioadmin123`
3. Browse buckets, upload/download files, manage policies

## Python Client Usage

### Basic Operations

```python
from utils.minio_client import get_minio_client

# Get client instance
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
    file_path="/path/to/download/video.mp4"
)

# List objects
objects = client.list_objects(
    bucket_name="videos",
    prefix="org123/"
)
for obj in objects:
    print(f"{obj.object_name} - {obj.size} bytes")

# Delete an object
client.delete_object(
    bucket_name="videos",
    object_name="org123/scene456/video.mp4"
)
```

### Upload from Memory

```python
from io import BytesIO

# Upload data from memory
data = BytesIO(b"file content")
client.upload_data(
    bucket_name="reports",
    object_name="scene123/report.pdf",
    data=data,
    length=len(data.getvalue()),
    content_type="application/pdf"
)
```

### Stream Download

```python
# Get object as stream
response = client.get_object(
    bucket_name="videos",
    object_name="org123/scene456/video.mp4"
)

# Read data
with open("/path/to/save.mp4", "wb") as f:
    for chunk in response.stream(32*1024):
        f.write(chunk)

response.close()
response.release_conn()
```

## Security Considerations

### Production Deployment

For production environments:

1. **Change Default Credentials**
   ```bash
   MINIO_ROOT_USER=your-secure-username
   MINIO_ROOT_PASSWORD=your-secure-password-min-8-chars
   ```

2. **Enable HTTPS**
   ```bash
   MINIO_SECURE=true
   ```
   Configure TLS certificates in MinIO

3. **Set Bucket Policies**
   - Restrict public access
   - Use IAM policies for fine-grained control
   - Enable versioning for critical buckets

4. **Network Security**
   - Use internal network for service communication
   - Expose only necessary ports
   - Configure firewall rules

5. **Access Logging**
   - Enable audit logging
   - Monitor access patterns
   - Set up alerts for suspicious activity

## Troubleshooting

### Connection Issues

```bash
# Check if MinIO is running
docker-compose ps minio

# Check MinIO logs
docker-compose logs minio

# Test connectivity
curl http://localhost:9000/minio/health/live
```

### Bucket Creation Fails

```bash
# Check MinIO credentials
echo $MINIO_ACCESS_KEY
echo $MINIO_SECRET_KEY

# Verify network connectivity
docker-compose exec api ping minio

# Check MinIO storage space
docker-compose exec minio df -h /data
```

### Upload/Download Errors

```python
# Enable debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Check bucket exists
client = get_minio_client()
exists = client.bucket_exists("videos")
print(f"Bucket exists: {exists}")

# List buckets
from minio import Minio
minio_client = Minio(
    "localhost:9000",
    access_key="minioadmin",
    secret_key="minioadmin123",
    secure=False
)
buckets = minio_client.list_buckets()
for bucket in buckets:
    print(bucket.name)
```

## Performance Optimization

### Upload Performance

- Use multipart uploads for large files (>5MB)
- Enable parallel uploads for multiple files
- Compress data before upload when appropriate

### Download Performance

- Use byte-range requests for partial downloads
- Implement client-side caching
- Use CDN for frequently accessed objects

### Storage Optimization

- Set lifecycle policies to archive old data
- Enable compression for text-based files
- Use appropriate storage classes

## Monitoring

### Health Checks

```bash
# Check MinIO health
curl http://localhost:9000/minio/health/live

# Check readiness
curl http://localhost:9000/minio/health/ready
```

### Metrics

MinIO exposes Prometheus metrics at:
```
http://localhost:9000/minio/v2/metrics/cluster
```

Key metrics to monitor:
- `minio_bucket_usage_total_bytes` - Storage usage per bucket
- `minio_s3_requests_total` - Request count
- `minio_s3_errors_total` - Error count
- `minio_network_sent_bytes_total` - Network egress

## Backup and Recovery

### Backup Strategy

```bash
# Backup MinIO data
docker-compose exec minio mc mirror /data /backup

# Or use volume backup
docker run --rm -v spatial-ai-platform_minio_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar czf /backup/minio-backup.tar.gz /data
```

### Restore

```bash
# Restore from backup
docker run --rm -v spatial-ai-platform_minio_data:/data \
  -v $(pwd)/backup:/backup \
  alpine tar xzf /backup/minio-backup.tar.gz -C /
```

## References

- [MinIO Documentation](https://min.io/docs/minio/linux/index.html)
- [MinIO Python SDK](https://min.io/docs/minio/linux/developers/python/minio-py.html)
- [S3 API Compatibility](https://min.io/docs/minio/linux/operations/concepts/s3-compatibility.html)
