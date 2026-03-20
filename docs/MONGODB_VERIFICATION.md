# MongoDB Deployment Verification Checklist

This document provides step-by-step instructions to verify that MongoDB has been properly deployed and configured.

## Prerequisites

- Docker and Docker Compose installed
- Docker Desktop running (if on Windows/Mac)
- Backend dependencies installed (`pip install -r requirements.txt`)

## Verification Steps

### Step 1: Start MongoDB Container

```bash
# Start MongoDB service
docker compose up -d mongodb

# Verify MongoDB is running
docker compose ps mongodb

# Check MongoDB logs
docker compose logs mongodb
```

**Expected Output:**
- Container status should be "Up" and "healthy"
- Logs should show "Waiting for connections" message

### Step 2: Verify MongoDB Connection

```bash
# Test connection using mongosh (MongoDB Shell)
docker exec -it spatial-ai-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin

# Inside mongosh, run:
show dbs
use spatial_ai_platform
show collections
exit
```

**Expected Output:**
- Should successfully connect to MongoDB
- Should see `spatial_ai_platform` database (after initialization)
- Should see collections after running initialization script

### Step 3: Run Database Initialization Script

```bash
cd backend

# Ensure virtual environment is activated
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Run initialization script
python scripts/init_mongodb.py
```

**Expected Output:**
```
{"event": "Starting MongoDB initialization...", "timestamp": "..."}
{"event": "Connected to MongoDB for initialization", "timestamp": "..."}
{"event": "Created collection: organizations", "timestamp": "..."}
{"event": "Created collection: users", "timestamp": "..."}
...
{"event": "Successfully created all indexes", "timestamp": "..."}
{"event": "MongoDB initialization completed successfully!", "timestamp": "..."}
```

### Step 4: Run Connection Test Script

```bash
cd backend

# Run test script
python scripts/test_mongodb.py
```

**Expected Output:**
```
{"event": "Testing MongoDB connection", "url": "mongodb://...", "timestamp": "..."}
{"event": "✓ Successfully connected to MongoDB", "timestamp": "..."}
{"event": "✓ Found 10 collections", "collections": [...], "timestamp": "..."}
{"event": "✓ Collection 'organizations' exists with X indexes", "timestamp": "..."}
...
{"event": "✓ Write test successful", "timestamp": "..."}
{"event": "✓ Read test successful", "timestamp": "..."}
{"event": "MongoDB connection test PASSED", "timestamp": "..."}
```

### Step 5: Verify Collections and Indexes

```bash
# Connect to MongoDB
docker exec -it spatial-ai-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin spatial_ai_platform

# Check collections
show collections

# Check indexes for each collection
db.organizations.getIndexes()
db.users.getIndexes()
db.scenes.getIndexes()
db.processing_jobs.getIndexes()
db.scene_tiles.getIndexes()
db.annotations.getIndexes()
db.guided_tours.getIndexes()
db.share_tokens.getIndexes()
db.scene_access_logs.getIndexes()
db.scene_objects.getIndexes()
```

**Expected Collections:**
1. organizations
2. users
3. scenes
4. processing_jobs
5. scene_tiles
6. annotations
7. guided_tours
8. share_tokens
9. scene_access_logs
10. scene_objects

**Expected Indexes (minimum):**
- Each collection should have at least 2-4 indexes
- All collections should have `_id` index (default)
- Check MONGODB_SETUP.md for complete index list

### Step 6: Start API Server and Test Health Endpoint

```bash
# Start all services
docker compose up -d

# Wait for services to be healthy (30 seconds)
timeout 30

# Test health endpoint
curl http://localhost:8000/health
```

**Expected Output:**
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### Step 7: Verify API Server Logs

```bash
# Check API server logs
docker compose logs api

# Look for these messages:
# - "Starting application..."
# - "Connecting to MongoDB"
# - "Successfully connected to MongoDB"
# - "Application startup completed"
```

## Verification Checklist

Use this checklist to confirm all requirements are met:

- [ ] MongoDB 7.0 container is running
- [ ] MongoDB is accessible on port 27017
- [ ] Database `spatial_ai_platform` exists
- [ ] All 10 collections are created:
  - [ ] organizations
  - [ ] users
  - [ ] scenes
  - [ ] processing_jobs
  - [ ] scene_tiles
  - [ ] annotations
  - [ ] guided_tours
  - [ ] share_tokens
  - [ ] scene_access_logs
  - [ ] scene_objects
- [ ] Indexes are created on required fields:
  - [ ] organization_id indexes
  - [ ] user_id indexes
  - [ ] scene_id indexes
  - [ ] status indexes
- [ ] Connection with authentication works
- [ ] API server can connect to MongoDB
- [ ] Health endpoint returns "connected" status
- [ ] Write and read operations work

## Troubleshooting

### Issue: Docker Desktop not running

**Error:** `The system cannot find the file specified`

**Solution:**
1. Start Docker Desktop application
2. Wait for Docker to fully start (check system tray icon)
3. Retry the docker commands

### Issue: MongoDB container fails to start

**Error:** Port 27017 already in use

**Solution:**
```bash
# Check what's using port 27017
netstat -ano | findstr :27017

# Stop local MongoDB if running
net stop MongoDB

# Or change port in docker-compose.yml
```

### Issue: Authentication failed

**Error:** `Authentication failed`

**Solution:**
1. Verify credentials in docker-compose.yml match .env file
2. Check the `authSource` parameter in connection URL
3. Ensure you're using the correct database name

### Issue: Collections not created

**Error:** Collections don't exist after initialization

**Solution:**
```bash
# Re-run initialization script
cd backend
python scripts/init_mongodb.py

# Or manually create collections
docker exec -it spatial-ai-mongodb mongosh -u admin -p admin123 --authenticationDatabase admin spatial_ai_platform
db.createCollection("organizations")
# ... repeat for other collections
```

### Issue: Indexes not created

**Error:** Queries are slow or indexes missing

**Solution:**
```bash
# Re-run initialization script to create indexes
cd backend
python scripts/init_mongodb.py

# Or manually create indexes using mongosh
# See MONGODB_SETUP.md for index definitions
```

## Success Criteria

Task 1.5 is complete when:

1. ✅ MongoDB 7.0 is deployed (container or Atlas)
2. ✅ Database `spatial_ai_platform` is created
3. ✅ All 10 collections are created
4. ✅ Indexes are created on organization_id, user_id, scene_id, status fields
5. ✅ Connection with authentication is configured
6. ✅ API server successfully connects to MongoDB
7. ✅ Health endpoint confirms database connection

## Next Steps

After successful verification:

1. Proceed to Task 1.6: Deploy and configure MinIO
2. Continue with remaining infrastructure tasks
3. Begin implementing authentication (Task 2.1)

## References

- [MONGODB_SETUP.md](./MONGODB_SETUP.md) - Detailed setup guide
- [docker-compose.yml](../docker-compose.yml) - Service configuration
- [utils/database.py](./utils/database.py) - Database connection code
- [scripts/init_mongodb.py](./scripts/init_mongodb.py) - Initialization script
- [scripts/test_mongodb.py](./scripts/test_mongodb.py) - Test script
