# API Security Status

## CORS Configuration

**Status:** ✅ Configured to allow all origins

**Configuration:**
- Location: `backend/.env`
- Setting: `CORS_ORIGINS='["*"]'`
- Applied in: `backend/main.py` via `CORSMiddleware`

This allows the frontend to be accessed from any IP address or domain.

## Authentication Status

All API endpoints are protected with JWT token authentication except for:

### Public Endpoints (No Authentication Required)
1. **Health Check:** `GET /health` - System health status
2. **Root:** `GET /` - API information
3. **Metrics:** `GET /metrics` - Prometheus metrics
4. **Authentication Endpoints:**
   - `POST /api/v1/auth/register` - User registration
   - `POST /api/v1/auth/login` - User login
   - `POST /api/v1/auth/refresh` - Token refresh
   - `POST /api/v1/auth/logout` - User logout

### Protected Endpoints (Require Authentication Token)

All other endpoints require a valid JWT token in the `Authorization` header:

**Format:** `Authorization: Bearer <token>`

#### Scenes API (`/api/v1/scenes`)
- ✅ `POST /scenes/upload` - Upload video
- ✅ `GET /scenes` - List scenes
- ✅ `GET /scenes/{scene_id}` - Get scene details
- ✅ `PATCH /scenes/{scene_id}` - Update scene
- ✅ `DELETE /scenes/{scene_id}` - Delete scene
- ✅ `GET /scenes/{scene_id}/jobs` - Get processing jobs
- ✅ `POST /scenes/{scene_id}/reprocess` - Reprocess scene
- ✅ `GET /scenes/{scene_id}/camera-config` - Get camera config
- ✅ `PUT /scenes/{scene_id}/camera-config` - Update camera config

#### Tiles API (`/api/v1/scenes/{scene_id}/tiles`)
- ✅ `POST /scenes/{scene_id}/tiles` - Get scene tiles (with frustum culling)
- ✅ `GET /scenes/{scene_id}/tiles/{tile_id}` - Download specific tile

#### 3D Import API (`/api/v1/scenes/import`)
- ✅ `GET /scenes/import/formats` - Get supported formats
- ✅ `POST /scenes/import/upload` - Upload 3D file
- ✅ `GET /scenes/import/status/{job_id}` - Get import status

#### Organizations API (`/api/v1/organizations`)
- ✅ All organization endpoints require authentication

#### Sharing API (`/api/v1/sharing`)
- ✅ All sharing endpoints require authentication

#### Annotations API (`/api/v1/annotations`)
- ✅ All annotation endpoints require authentication

#### Collaboration API (`/api/v1/collaboration`)
- ✅ All collaboration endpoints require authentication

#### Photos API (`/api/v1/photos`)
- ✅ All photo endpoints require authentication

#### Geospatial API
- ✅ All geospatial endpoints require authentication

#### Reports API (`/api/v1/reports`)
- ✅ All report endpoints require authentication

## Authentication Implementation

**Dependency:** `get_current_user` from `backend/api/deps.py`

**Features:**
- JWT token validation
- Token blacklist checking (via Valkey/Redis)
- User existence verification
- Active user status check
- Organization membership validation

**Token Payload:**
```python
{
    "sub": "user_id",           # User ID
    "jti": "token_id",          # JWT ID (for blacklisting)
    "exp": timestamp,           # Expiration time
    "type": "access"            # Token type
}
```

## Frontend Token Management

**Location:** `frontend/src/store/api/baseApi.ts`

**Features:**
- Automatic token injection in request headers
- Automatic token refresh on 401 errors
- Token storage in Redux state
- Logout on refresh failure

## Security Best Practices

✅ All sensitive endpoints protected with authentication
✅ JWT tokens with expiration
✅ Token blacklisting for logout
✅ HTTPS recommended for production
✅ CORS configured (currently allows all origins)
✅ Password hashing with bcrypt
✅ Refresh token rotation

## Production Recommendations

For production deployment:

1. **CORS:** Restrict to specific domains
   ```python
   CORS_ORIGINS='["https://yourdomain.com", "https://app.yourdomain.com"]'
   ```

2. **HTTPS:** Enable SSL/TLS
3. **JWT Secret:** Use strong, random secret key
4. **Token Expiration:** Keep access tokens short-lived (15-30 minutes)
5. **Rate Limiting:** Add rate limiting middleware
6. **API Keys:** Consider API keys for service-to-service communication

## Testing Authentication

### Get Token
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=password"
```

### Use Token
```bash
curl -X GET http://localhost:8000/api/v1/scenes \
  -H "Authorization: Bearer <your_token_here>"
```

---

**Last Updated:** 2026-04-02
**Status:** ✅ All endpoints properly secured
