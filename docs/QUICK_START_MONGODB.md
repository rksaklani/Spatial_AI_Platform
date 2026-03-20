# Quick Start: MongoDB Setup

This is a quick reference for deploying and verifying MongoDB. For detailed information, see [MONGODB_SETUP.md](./MONGODB_SETUP.md).

## 🚀 Quick Setup (3 Steps)

### 1. Start MongoDB

```bash
# Make sure Docker Desktop is running first!

# Start MongoDB container
docker compose up -d mongodb

# Verify it's running
docker compose ps mongodb
```

### 2. Initialize Database

```bash
cd backend

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Run initialization
python scripts/init_mongodb.py
```

### 3. Verify Setup

```bash
# Run test script
python scripts/test_mongodb.py

# Should see: "MongoDB connection test PASSED"
```

## ✅ Verification

Test the health endpoint:

```bash
# Start all services
docker compose up -d

# Test health
curl http://localhost:8000/health

# Expected: {"status": "healthy", "database": "connected"}
```

## 📋 What Was Created

### Database
- **Name:** spatial_ai_platform
- **Port:** 27017
- **Auth:** admin / admin123

### Collections (10 total)
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

### Indexes
- organization_id (multiple collections)
- user_id (multiple collections)
- scene_id (multiple collections)
- status (scenes, processing_jobs)
- Plus 30+ additional indexes for performance

## 🔧 Files Created

```
backend/
├── utils/
│   └── database.py              # MongoDB connection manager
├── scripts/
│   ├── init_mongodb.py          # Database initialization
│   └── test_mongodb.py          # Connection test
├── MONGODB_SETUP.md             # Detailed setup guide
├── MONGODB_VERIFICATION.md      # Verification checklist
└── QUICK_START_MONGODB.md       # This file
```

## 🐛 Troubleshooting

**Docker not running?**
```bash
# Start Docker Desktop and wait for it to fully start
# Then retry: docker compose up -d mongodb
```

**Port 27017 in use?**
```bash
# Check what's using it
netstat -ano | findstr :27017

# Stop local MongoDB if running
net stop MongoDB
```

**Connection failed?**
```bash
# Check MongoDB logs
docker compose logs mongodb

# Verify credentials in .env match docker-compose.yml
```

## 📚 More Information

- [MONGODB_SETUP.md](./MONGODB_SETUP.md) - Complete setup guide
- [MONGODB_VERIFICATION.md](./MONGODB_VERIFICATION.md) - Detailed verification steps
- [MongoDB Documentation](https://docs.mongodb.com/)

## ✨ Task 1.5 Complete!

Once all verification steps pass, Task 1.5 is complete and you can proceed to Task 1.6 (MinIO setup).
