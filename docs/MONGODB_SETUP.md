# MongoDB Setup Guide

This guide explains how to deploy and configure MongoDB for the Ultimate Spatial AI Platform.

## Overview

The platform uses MongoDB 7.0 as the primary database for storing:
- Organizations and users
- Scene metadata and processing jobs
- Scene tiles and annotations
- Guided tours and share tokens
- Access logs and scene objects

## Deployment Options

### Option 1: Docker Compose (Recommended for Development)

MongoDB is already configured in `docker-compose.yml`. To start MongoDB:

```bash
# Start MongoDB only
docker-compose up -d mongodb

# Start all services including MongoDB
docker-compose up -d
```

**MongoDB Configuration:**
- Port: 27017
- Root Username: admin
- Root Password: admin123
- Database: spatial_ai_platform
- Connection URL: `mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin`

### Option 2: MongoDB Atlas (Recommended for Production)

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster (M10 or higher recommended for production)
3. Create a database user with read/write permissions
4. Whitelist your application's IP addresses
5. Get the connection string from Atlas dashboard
6. Update the `MONGODB_URL` environment variable:

```bash
export MONGODB_URL="mongodb+srv://username:password@cluster.mongodb.net/spatial_ai_platform?retryWrites=true&w=majority"
```

### Option 3: Self-Hosted MongoDB

1. Install MongoDB 7.0:
   ```bash
   # Ubuntu/Debian
   wget -qO - https://www.mongodb.org/static/pgp/server-7.0.asc | sudo apt-key add -
   echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu jammy/mongodb-org/7.0 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-7.0.list
   sudo apt-get update
   sudo apt-get install -y mongodb-org
   
   # Start MongoDB
   sudo systemctl start mongod
   sudo systemctl enable mongod
   ```

2. Create admin user:
   ```bash
   mongosh
   use admin
   db.createUser({
     user: "admin",
     pwd: "your-secure-password",
     roles: ["root"]
   })
   ```

3. Enable authentication in `/etc/mongod.conf`:
   ```yaml
   security:
     authorization: enabled
   ```

4. Restart MongoDB:
   ```bash
   sudo systemctl restart mongod
   ```

## Database Initialization

The database is automatically initialized when the FastAPI application starts. It will:
1. Create the database if it doesn't exist
2. Create all required collections
3. Create indexes for optimal query performance

### Manual Initialization

If you need to manually initialize the database:

```bash
cd backend
python scripts/init_mongodb.py
```

## Database Schema

### Collections

1. **organizations** - Organization/tenant data
2. **users** - User accounts and authentication
3. **scenes** - Scene metadata and status
4. **processing_jobs** - Background job tracking
5. **scene_tiles** - Spatial tile metadata
6. **annotations** - User annotations and measurements
7. **guided_tours** - Saved camera paths with narration
8. **share_tokens** - Scene sharing tokens
9. **scene_access_logs** - Audit trail for scene access
10. **scene_objects** - Semantic scene analysis results

### Indexes

The following indexes are automatically created for optimal performance:

**organizations:**
- name (ascending)
- created_at (descending)

**users:**
- email (unique, ascending)
- organization_id (ascending)
- created_at (descending)

**scenes:**
- organization_id (ascending)
- user_id (ascending)
- status (ascending)
- scene_id (unique, ascending)
- created_at (descending)
- organization_id + status (compound)

**processing_jobs:**
- scene_id (ascending)
- status (ascending)
- scene_id + status (compound)
- created_at (descending)

**scene_tiles:**
- scene_id (ascending)
- tile_id (ascending)
- scene_id + tile_id (unique, compound)
- scene_id + level (compound)

**annotations:**
- scene_id (ascending)
- user_id (ascending)
- scene_id + created_at (compound, descending)
- annotation_type (ascending)

**guided_tours:**
- scene_id (ascending)
- user_id (ascending)
- created_at (descending)

**share_tokens:**
- token (unique, ascending)
- scene_id (ascending)
- expires_at (ascending)
- created_at (descending)

**scene_access_logs:**
- scene_id (ascending)
- user_id (ascending)
- accessed_at (descending)
- scene_id + accessed_at (compound, descending)

**scene_objects:**
- scene_id (ascending)
- object_id (ascending)
- scene_id + object_id (unique, compound)
- label (ascending)

## Connection Configuration

### Environment Variables

Configure MongoDB connection using environment variables:

```bash
# MongoDB connection URL
MONGODB_URL=mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin

# Database name
DATABASE_NAME=spatial_ai_platform
```

### Connection Pooling

The application uses Motor (async MongoDB driver) with connection pooling:
- Max connections: 100
- Min connections: 10
- Server selection timeout: 5 seconds

## Monitoring and Maintenance

### Health Check

Check MongoDB connection status:
```bash
curl http://localhost:8000/health
```

### Database Statistics

Connect to MongoDB and check statistics:
```bash
mongosh "mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin"

# Show collections
show collections

# Show collection statistics
db.scenes.stats()

# Count documents
db.scenes.countDocuments()

# Check indexes
db.scenes.getIndexes()
```

### Backup

**Docker Compose:**
```bash
docker exec spatial-ai-mongodb mongodump --uri="mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin" --out=/data/backup
```

**Self-Hosted:**
```bash
mongodump --uri="mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin" --out=/backup/mongodb
```

### Restore

**Docker Compose:**
```bash
docker exec spatial-ai-mongodb mongorestore --uri="mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin" /data/backup/spatial_ai_platform
```

**Self-Hosted:**
```bash
mongorestore --uri="mongodb://admin:admin123@localhost:27017/spatial_ai_platform?authSource=admin" /backup/mongodb/spatial_ai_platform
```

## Security Best Practices

1. **Change default passwords** - Never use default credentials in production
2. **Use strong passwords** - Minimum 16 characters with mixed case, numbers, and symbols
3. **Enable TLS/SSL** - Use encrypted connections in production
4. **Restrict network access** - Use firewall rules to limit MongoDB access
5. **Regular backups** - Implement automated backup strategy
6. **Monitor access logs** - Review scene_access_logs regularly
7. **Update regularly** - Keep MongoDB updated with security patches

## Troubleshooting

### Connection Refused

If you get "connection refused" errors:
1. Check if MongoDB is running: `docker ps` or `sudo systemctl status mongod`
2. Verify the connection URL in environment variables
3. Check firewall rules and network connectivity

### Authentication Failed

If you get authentication errors:
1. Verify username and password
2. Check the `authSource` parameter in connection URL
3. Ensure the user has proper permissions

### Slow Queries

If queries are slow:
1. Check if indexes are created: `db.collection.getIndexes()`
2. Use explain to analyze queries: `db.collection.find().explain()`
3. Monitor with MongoDB profiler: `db.setProfilingLevel(1, { slowms: 100 })`

## References

- [MongoDB Documentation](https://docs.mongodb.com/)
- [Motor Documentation](https://motor.readthedocs.io/)
- [PyMongo Documentation](https://pymongo.readthedocs.io/)
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
