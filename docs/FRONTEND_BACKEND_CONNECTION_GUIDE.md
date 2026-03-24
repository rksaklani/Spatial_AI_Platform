# Frontend-Backend Connection Guide

## Current Configuration

### ✅ Frontend Configuration
- **Location**: `frontend/.env`
- **API Base URL**: `http://localhost:8000/api/v1`
- **WebSocket URL**: `ws://localhost:8000`

### ✅ Backend Configuration
- **Location**: `backend/.env`
- **API Host**: `0.0.0.0`
- **API Port**: `8000`
- **CORS Origins**: `["http://localhost:3000", "http://localhost:5173"]`

### ✅ Connection Status
The frontend and backend are **already configured** to work together!

## How to Start Both Services

### Option 1: Using Docker Compose (Recommended)
```bash
# Start all services (backend, frontend, MongoDB, MinIO, Redis)
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

### Option 2: Manual Start

#### 1. Start Backend
```bash
# Navigate to backend directory
cd backend

# Activate virtual environment (if using venv)
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Start the backend server
python main.py
```

Backend will be available at: `http://localhost:8000`

#### 2. Start Frontend
```bash
# Navigate to frontend directory (in a new terminal)
cd frontend

# Install dependencies (first time only)
npm install

# Start the development server
npm run dev
```

Frontend will be available at: `http://localhost:5173`

## Testing the Connection

### 1. Check Backend Health
Open your browser and visit:
```
http://localhost:8000/health
```

You should see:
```json
{
  "status": "healthy",
  "timestamp": "2026-03-24T...",
  "services": {
    "mongodb": "connected",
    "minio": "connected",
    "valkey": "connected"
  }
}
```

### 2. Check Frontend Connection
1. Open `http://localhost:5173` in your browser
2. Try to register a new account or login
3. Check the browser console (F12) for any errors
4. Check the Network tab to see API requests

### 3. Test API Endpoints
You can test the backend API directly:

```bash
# Test root endpoint
curl http://localhost:8000/

# Test health endpoint
curl http://localhost:8000/health

# Test registration
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "testpassword123",
    "full_name": "Test User",
    "organization_name": "Test Org"
  }'
```

## API Integration Points

### Authentication
- **Register**: `POST /api/v1/auth/register`
- **Login**: `POST /api/v1/auth/login`
- **Refresh Token**: `POST /api/v1/auth/refresh`
- **Get Current User**: `GET /api/v1/auth/me`

### Scenes
- **List Scenes**: `GET /api/v1/scenes`
- **Upload Video**: `POST /api/v1/scenes/upload`
- **Get Scene**: `GET /api/v1/scenes/{id}`
- **Update Scene**: `PATCH /api/v1/scenes/{id}`
- **Delete Scene**: `DELETE /api/v1/scenes/{id}`

### Tiles (3D Streaming)
- **Request Tiles**: `POST /api/v1/scenes/{id}/tiles`
- **Download Tile**: `GET /api/v1/tiles/{tile_id}`

### Annotations
- **List Annotations**: `GET /api/v1/scenes/{id}/annotations`
- **Create Annotation**: `POST /api/v1/scenes/{id}/annotations`
- **Update Annotation**: `PATCH /api/v1/annotations/{id}`
- **Delete Annotation**: `DELETE /api/v1/annotations/{id}`

### Collaboration (WebSocket)
- **Connect**: `WS /api/v1/scenes/{id}/collaborate`
- Events: `user:joined`, `user:left`, `cursor:move`, `annotation:created`

## Frontend API Services

The frontend uses RTK Query for API integration. All API endpoints are defined in:

- `frontend/src/store/api/baseApi.ts` - Base configuration
- `frontend/src/store/api/authApi.ts` - Authentication endpoints
- `frontend/src/store/api/sceneApi.ts` - Scene management
- `frontend/src/store/api/annotationApi.ts` - Annotations
- `frontend/src/store/api/tourApi.ts` - Guided tours
- `frontend/src/store/api/photoApi.ts` - Photos
- `frontend/src/store/api/sharingApi.ts` - Scene sharing
- `frontend/src/store/api/reportApi.ts` - Report generation

## WebSocket Connection

The frontend connects to the backend WebSocket for real-time collaboration:

```typescript
// Service: frontend/src/services/websocket.service.ts
const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
websocketService.connect(sceneId, token);
```

## Troubleshooting

### Issue: Frontend can't connect to backend

**Solution 1**: Check if backend is running
```bash
curl http://localhost:8000/health
```

**Solution 2**: Check CORS configuration in `backend/.env`
```
CORS_ORIGINS='["http://localhost:3000", "http://localhost:5173"]'
```

**Solution 3**: Check frontend API URL in `frontend/.env`
```
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

### Issue: 401 Unauthorized errors

**Solution**: The user is not logged in or token has expired
- Try logging in again
- Check if token is stored in Redux state
- Check browser console for token refresh errors

### Issue: CORS errors in browser console

**Solution**: Restart the backend server after changing CORS configuration
```bash
# Stop backend (Ctrl+C)
# Start backend again
python main.py
```

### Issue: WebSocket connection fails

**Solution 1**: Check WebSocket URL in `frontend/.env`
```
VITE_WS_URL=ws://localhost:8000
```

**Solution 2**: Ensure backend WebSocket endpoint is working
```bash
# Check backend logs for WebSocket connection attempts
```

## Environment Variables

### Frontend (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000
```

### Backend (`backend/.env`)
```env
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS='["http://localhost:3000", "http://localhost:5173"]'
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=spatial_ai_platform
MINIO_ENDPOINT=localhost:9000
VALKEY_HOST=localhost
VALKEY_PORT=6379
JWT_SECRET_KEY=your-secret-key-change-in-production
```

## Production Deployment

For production, update the environment variables:

### Frontend
```env
VITE_API_BASE_URL=https://api.yourdomain.com/api/v1
VITE_WS_URL=wss://api.yourdomain.com
```

### Backend
```env
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS='["https://yourdomain.com"]'
MONGODB_URL=mongodb+srv://user:pass@cluster.mongodb.net/
# ... other production settings
```

## Next Steps

1. ✅ Start the backend server
2. ✅ Start the frontend development server
3. ✅ Open `http://localhost:5173` in your browser
4. ✅ Register a new account
5. ✅ Upload a video or 3D file
6. ✅ View the 3D scene
7. ✅ Test real-time collaboration features

The frontend and backend are now connected and ready to use!
