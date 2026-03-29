# Backend Setup Status & Quick Start Guide

## Current Status - ✅ FULLY WORKING

### ✅ What's Working
- Backend API (FastAPI) - **RUNNING on http://localhost:8000**
- Frontend UI (React + Vite) - **RUNNING on http://localhost:5173**
- Database (MongoDB Atlas) - Connected and initialized
- Authentication & Authorization - Working
- All dashboard pages with API integration
- Video upload functionality
- File storage (MinIO) - Configured
- Python Environment - Linux venv at `/tmp/spatial_venv`
- All Python dependencies installed (including PyTorch, OpenCV, Open3D)
- Node.js 20.20.0 and npm 10.8.2 installed
- Frontend dependencies installed

### ⚠️ What Needs Setup for Full 3D Reconstruction (Optional)
- CUDA Toolkit (for GPU acceleration)
- CMake (build tool)
- COLMAP (camera pose estimation)
- PyTorch with CUDA (currently CPU version - works but slower)
- Gaussian Splatting (3D reconstruction)

---

## ✅ Quick Start (CURRENT SETUP - WORKING NOW)

### Backend is Running
```bash
# Backend is already running at http://localhost:8000
# Process: /tmp/spatial_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend is Running
```bash
# Frontend is already running at http://localhost:5173
# Process: npm run dev -- --host 0.0.0.0 --port 5173
```

### Access Application
- **Frontend:** http://localhost:5173
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

### To Restart Services

**Backend:**
```bash
./start-backend.sh
# OR manually:
cd backend
/tmp/spatial_venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**Frontend:**
```bash
./start-frontend.sh
# OR manually:
cd frontend
npm run dev -- --host 0.0.0.0
```

---

## Important Notes

### Python Virtual Environment
- **Location:** `/tmp/spatial_venv` (Linux-compatible venv)
- **Why /tmp?** The project is on an exFAT drive which doesn't support symlinks required by Python venv
- **All dependencies installed:** FastAPI, PyTorch, OpenCV, Open3D, NumPy, Pillow, etc.

### Original Windows venv
- The `backend/venv` folder is from Windows and won't work on Linux
- Don't delete it - it might be needed if you switch back to Windows
- Use `/tmp/spatial_venv` on Linux instead

---

## Quick Start (Without 3D Pipeline)

You can use the platform NOW for basic features:

### 1. Start Backend (if not running)
```bash
./start-backend.sh
```

### 2. Start Frontend (if not running)
```bash
./start-frontend.sh
```

### 3. Access Application
- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 4. Test Backend Connection
Open `test-backend.html` in your browser to verify backend is running.

---

## What You Can Do NOW (Without 3D Pipeline)

1. **User Management**
   - Register/Login
   - Profile settings
   - Organization management

2. **File Upload**
   - Upload videos (stored in MinIO)
   - Upload photos
   - File management

3. **Dashboard**
   - View uploaded files
   - Manage scenes
   - Reports
   - Collaboration features

4. **UI Features**
   - All pages with attractive orange-blue theme
   - Responsive design
   - Glassmorphism effects
   - Dropdown menus
   - Navigation

---

## Setting Up 3D Pipeline (Optional)

If you want full 3D reconstruction (COLMAP + Gaussian Splatting):

### Option 1: Automated Installation (Recommended)
```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
.\scripts\install_3d_pipeline.ps1
```

This script will:
1. Check what's installed
2. Guide you through installing missing components
3. Install PyTorch with CUDA
4. Clone and build Gaussian Splatting
5. Verify everything works

**Time Required:** 2-3 hours

### Option 2: Check What's Missing First
```powershell
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
python scripts/check_3d_requirements.py
```

This will show you exactly what needs to be installed.

### Option 3: Manual Installation

Follow the detailed guide:
- **Full Guide:** `docs/3D_PIPELINE_INSTALLATION_WINDOWS.md`
- **Quick Steps:** `docs/QUICK_INSTALL_STEPS.md`

---

## Installation Order (If Installing Manually)

1. **Visual Studio 2022** (if not installed) - 30-60 min
   - Download from: https://visualstudio.microsoft.com/downloads/
   - Install "Desktop development with C++"

2. **CUDA Toolkit 11.8** - 15-20 min
   - Download from: https://developer.nvidia.com/cuda-11-8-0-download-archive
   - Add to PATH after installation

3. **CMake** - 5 min
   - Download from: https://cmake.org/download/
   - Or: `choco install cmake`

4. **COLMAP** - 10 min
   - Download from: https://github.com/colmap/colmap/releases
   - Or build from source with vcpkg

5. **PyTorch with CUDA** - 10 min
   ```powershell
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   ```

6. **Gaussian Splatting** - 30-45 min
   ```powershell
   cd E:\Rk_Saklani\3d_rendering\backend
   git clone https://github.com/graphdeco-inria/gaussian-splatting.git --recursive
   cd gaussian-splatting
   pip install -e .
   ```

---

## How the 3D Pipeline Works

### Without 3D Pipeline (Current State)
```
User → Upload Video → Store in MinIO → Show in Dashboard
```

### With 3D Pipeline (After Setup)
```
User → Upload Video → Backend Processing:
  1. Extract frames (FFmpeg)
  2. Filter frames (blur/motion detection)
  3. Estimate camera poses (COLMAP)
  4. Generate depth maps (MiDaS)
  5. 3D reconstruction (Gaussian Splatting)
  6. Optimize and tile
  → Interactive 3D viewer in browser
```

---

## Testing Backend Connection

### Method 1: Use Test HTML File
1. Open `test-backend.html` in your browser
2. Click "Test Again" button
3. Should show "✅ Backend is running!"

### Method 2: Use curl
```powershell
curl http://localhost:8000/api/v1/health
```

Should return:
```json
{
  "status": "healthy",
  "database": "connected",
  "storage": "connected"
}
```

### Method 3: Browser
Open: http://localhost:8000/docs

You should see the FastAPI Swagger documentation.

---

## Creating Your First Scene

### Step 1: Start Services
```powershell
# Terminal 1: Backend
cd E:\Rk_Saklani\3d_rendering\backend
.\venv\Scripts\activate
uvicorn main:app --reload

# Terminal 2: Frontend
cd E:\Rk_Saklani\3d_rendering\frontend
npm run dev
```

### Step 2: Login
1. Go to http://localhost:5173
2. Click "Login"
3. Use your credentials or register

### Step 3: Create Scene
1. Click "3D Scenes" in sidebar
2. Click "Upload Video" button
3. Select a video file
4. Click "Upload"

**Note:** Without 3D pipeline, the video will be stored but not processed into 3D. You'll see it in the scenes list with status "uploaded".

### Step 4: Upload Photos
1. Click "Photos" in sidebar
2. Select a scene from dropdown
3. Click "Choose File"
4. Select an image
5. Click "Upload"

---

## Troubleshooting

### Backend Won't Start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill process if needed
taskkill /PID <process_id> /F

# Try different port
uvicorn main:app --reload --port 8001
```

### Frontend Won't Start
```powershell
# Clear node modules and reinstall
rm -r node_modules
npm install

# Try different port
npm run dev -- --port 5174
```

### Database Connection Error
Check `backend/.env`:
```
MONGODB_URL=mongodb+srv://rksaklani90_db_user:rksaklani90_db_user@cluster0.lelxuus.mongodb.net/
DATABASE_NAME=spatial_ai_platform
```

### MinIO Connection Error
Make sure MinIO is running:
```powershell
# If using Docker
docker ps | findstr minio

# If not running
docker-compose up -d minio
```

---

## Environment Configuration

### Backend (.env)
```env
# MongoDB
MONGODB_URL=mongodb+srv://rksaklani90_db_user:rksaklani90_db_user@cluster0.lelxuus.mongodb.net/
DATABASE_NAME=spatial_ai_platform

# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256

# API
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS='["http://localhost:3000", "http://localhost:5173"]'
```

### Frontend (.env)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

---

## Next Steps

### Immediate (No 3D Pipeline Required)
1. ✅ Start backend and frontend
2. ✅ Test login/registration
3. ✅ Upload a video (will be stored)
4. ✅ Upload photos
5. ✅ Explore all UI pages

### Later (When Ready for 3D)
1. Run `python scripts/check_3d_requirements.py`
2. Install missing components
3. Test with short video (30 seconds)
4. View 3D reconstruction in browser

---

## Documentation

- 📖 **This file:** Quick start and status
- 📋 **START_HERE.md:** 3D pipeline installation overview
- 📊 **COMPLETE_PIPELINE_GUIDE.md:** How everything works
- 🔧 **check_3d_requirements.py:** Check what's installed
- 🤖 **install_3d_pipeline.ps1:** Automated installation

---

## Summary

**Current State:**
- ✅ Backend API is ready
- ✅ Frontend UI is complete and beautiful
- ✅ Database is connected
- ✅ File upload works
- ⚠️ 3D reconstruction needs additional setup

**You Can Use NOW:**
- All UI features
- File management
- User authentication
- Dashboard pages

**For Full 3D Reconstruction:**
- Run installation script
- Or follow manual installation guide
- Estimated time: 2-3 hours

---

**Questions?**
- Check `docs/` folder for detailed guides
- Run `python scripts/check_3d_requirements.py` to see status
- Open `test-backend.html` to test backend connection
