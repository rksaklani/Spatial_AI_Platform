# Linux Setup Guide - Quick Reference

## ✅ Setup Complete!

Both backend and frontend are running and fully functional.

---

## Access URLs

- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## Running Services

### Backend (Terminal ID: 11)
```
Command: /tmp/spatial_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
Directory: backend/
Status: ✅ RUNNING
```

### Frontend (Terminal ID: 12)
```
Command: npm run dev -- --host 0.0.0.0 --port 5173
Directory: frontend/
Status: ✅ RUNNING
```

---

## Quick Commands

### Start Services (if stopped)
```bash
# Backend
./start-backend.sh

# Frontend
./start-frontend.sh
```

### Check Status
```bash
# Backend health
curl http://localhost:8000/health

# Frontend
curl -I http://localhost:5173/
```

### View Logs
```bash
# Backend logs
tail -f backend/logs/*.log

# Or check the terminal where uvicorn is running
```

---

## Important Paths

### Python Virtual Environment
```
Location: /tmp/spatial_venv
Reason: Project on exFAT drive (no symlink support)
Python: 3.10.12
Packages: All requirements.txt installed
```

### Project Structure
```
/media/rk/Rohit_SSD/Rk_Saklani/3d_rendering/
├── backend/          # FastAPI backend
├── frontend/         # React frontend
├── start-backend.sh  # Backend launcher
└── start-frontend.sh # Frontend launcher
```

---

## Environment Details

### System
- OS: Linux (Ubuntu 22.04)
- Python: 3.10.12
- Node.js: 20.20.0
- npm: 10.8.2

### Backend Stack
- FastAPI 0.135.2
- Uvicorn 0.42.0
- PyTorch 2.11.0
- MongoDB (Atlas)
- MinIO (configured)

### Frontend Stack
- React 18.3.1
- Vite 8.0.1
- Three.js 0.170.0
- Tailwind CSS 3.4.17

---

## What Works

✅ User authentication and authorization
✅ File upload and management
✅ Database operations (MongoDB Atlas)
✅ All API endpoints
✅ Full UI with all pages
✅ Real-time features (WebSocket ready)
✅ 3D viewer components

---

## What's Optional

⚠️ 3D Reconstruction Pipeline (not required for basic use)
- CUDA Toolkit
- COLMAP
- Gaussian Splatting

These are only needed if you want to convert videos into 3D scenes.

---

## Troubleshooting

### Port Already in Use
```bash
# Find process using port 8000 (backend)
sudo netstat -tulpn | grep 8000
sudo kill -9 <PID>

# Find process using port 5173 (frontend)
sudo netstat -tulpn | grep 5173
sudo kill -9 <PID>
```

### Backend Issues
```bash
# Check if venv is working
/tmp/spatial_venv/bin/python --version

# Test imports
/tmp/spatial_venv/bin/python -c "import fastapi; print('OK')"

# Check MongoDB connection
curl http://localhost:8000/health/detailed
```

### Frontend Issues
```bash
# Reinstall dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install

# Clear cache
npm cache clean --force
```

---

## Next Steps

1. **Open the application:** http://localhost:5173
2. **Register a user** or login if you have an account
3. **Explore the features:**
   - Upload files
   - Create scenes
   - Manage organizations
   - View reports

4. **Read the docs:**
   - `SETUP_COMPLETE.md` - Full setup details
   - `BACKEND_SETUP_STATUS.md` - Backend configuration
   - http://localhost:8000/docs - API documentation

---

## Support

If you encounter issues:
1. Check the logs in the terminal
2. Verify services are running: `curl http://localhost:8000/health`
3. Check the troubleshooting section above
4. Review `SETUP_COMPLETE.md` for detailed information

---

**Status:** ✅ Fully operational and ready to use!
