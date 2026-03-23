# Frontend-Backend API Integration

## Overview
The frontend is now fully connected to the FastAPI backend using RTK Query for state management and API calls.

## Configuration

### Environment Variables
Create `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Connected APIs

### 1. Authentication API (`/api/v1/auth`)

#### Login
- **Endpoint**: `POST /auth/login`
- **Frontend Hook**: `useLoginMutation()`
- **Request**: OAuth2 form data with `username` (email) and `password`
- **Response**: Access token, refresh token, token type
- **Flow**:
  1. User enters email/password
  2. Frontend sends OAuth2 form data
  3. Backend returns tokens
  4. Frontend fetches user info with access token
  5. Stores tokens in Redux + localStorage
  6. Redirects to `/app/dashboard`

#### Register
- **Endpoint**: `POST /auth/register`
- **Frontend Hook**: `useRegisterMutation()`
- **Request**: `{ email, password, full_name }`
- **Response**: User object
- **Flow**:
  1. User fills registration form
  2. Frontend sends registration data
  3. Backend creates user and sends welcome email
  4. Frontend redirects to login page

#### Logout
- **Endpoint**: `POST /auth/logout`
- **Frontend Hook**: `useLogoutMutation()`
- **Request**: None (uses Authorization header)
- **Response**: Success message
- **Flow**:
  1. User clicks logout
  2. Frontend sends logout request
  3. Backend blacklists the token
  4. Frontend clears Redux state and localStorage
  5. Redirects to home page

#### Get Current User
- **Endpoint**: `GET /auth/me`
- **Frontend Hook**: `useGetCurrentUserQuery()`
- **Request**: None (uses Authorization header)
- **Response**: User object with profile data

#### Refresh Token
- **Endpoint**: `POST /auth/refresh`
- **Frontend Hook**: `useRefreshTokenMutation()`
- **Request**: `{ refresh_token }`
- **Response**: New access token and refresh token

### 2. Scenes API (`/api/v1/scenes`)

#### List Scenes
- **Endpoint**: `GET /scenes`
- **Frontend Hook**: `useGetScenesQuery()`
- **Request**: Query params for pagination/filtering
- **Response**: Array of scene objects

#### Upload Scene
- **Endpoint**: `POST /scenes/upload`
- **Frontend Hook**: `useUploadVideoMutation()`
- **Request**: FormData with video file
- **Response**: Scene object

#### Get Scene
- **Endpoint**: `GET /scenes/{scene_id}`
- **Frontend Hook**: `useGetSceneQuery(sceneId)`
- **Request**: Scene ID in URL
- **Response**: Scene object with details

#### Delete Scene
- **Endpoint**: `DELETE /scenes/{scene_id}`
- **Frontend Hook**: `useDeleteSceneMutation()`
- **Request**: Scene ID in URL
- **Response**: Success message

### 3. Organizations API (`/api/v1/organizations`)

#### List Organizations
- **Endpoint**: `GET /organizations`
- **Frontend Hook**: `useGetOrganizationsQuery()`
- **Response**: Array of organizations user belongs to

#### Switch Organization
- **Endpoint**: `POST /organizations/{org_id}/switch`
- **Frontend Hook**: `useSwitchOrganizationMutation()`
- **Request**: Organization ID in URL
- **Response**: Updated user context

## Authentication Flow

### Token Management
1. **Access Token**: Stored in Redux state (`auth.token`)
2. **Refresh Token**: Stored in localStorage (`refreshToken`)
3. **Auto-refresh**: Implemented in base query interceptor
4. **Token Expiry**: Handled automatically with 401 response

### Request Interceptor
All API requests automatically include:
```typescript
headers: {
  'Authorization': `Bearer ${accessToken}`
}
```

### Error Handling
- **401 Unauthorized**: Auto-logout and redirect to login
- **403 Forbidden**: Show access denied message
- **404 Not Found**: Show not found message
- **500 Server Error**: Show error toast with retry option

## Usage Examples

### Login
```typescript
import { useLoginMutation } from '../store/api/authApi';

const [login, { isLoading, error }] = useLoginMutation();

const handleLogin = async () => {
  try {
    const result = await login({ email, password }).unwrap();
    // Success - user is logged in
  } catch (error) {
    // Handle error
  }
};
```

### Fetch Scenes
```typescript
import { useGetScenesQuery } from '../store/api/sceneApi';

const { data: scenes, isLoading, error } = useGetScenesQuery();
```

### Upload Video
```typescript
import { useUploadVideoMutation } from '../store/api/sceneApi';

const [uploadVideo] = useUploadVideoMutation();

const handleUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('organization_id', orgId);
  
  await uploadVideo(formData).unwrap();
};
```

## Backend Requirements

### CORS Configuration
The backend must allow requests from the frontend origin:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Running the Backend
```bash
cd backend
python -m uvicorn main:app --reload --port 8000
```

## Testing the Integration

### 1. Start Backend
```bash
cd backend
python -m uvicorn main:app --reload
```

### 2. Start Frontend
```bash
cd frontend
npm run dev
```

### 3. Test Flow
1. Visit `http://localhost:5173`
2. Click "LOG IN"
3. Click "Continue with Demo Mode" (for testing without backend)
4. Or enter real credentials if backend is running
5. Should redirect to dashboard at `/app/dashboard`

## Demo Mode

For testing the UI without a running backend, use the "Continue with Demo Mode" button on the login page. This bypasses authentication and uses mock data.

To disable demo mode in production, remove the demo login handler from `LoginForm.tsx`.

## Next Steps

1. ✅ Authentication API connected
2. ✅ Login/Register flow working
3. ✅ Token management implemented
4. ⏳ Scenes API integration (partially done)
5. ⏳ Organizations API integration
6. ⏳ Annotations API integration
7. ⏳ Collaboration WebSocket integration
8. ⏳ Photos API integration

## Troubleshooting

### CORS Errors
If you see CORS errors in the browser console:
1. Check backend CORS configuration
2. Ensure frontend origin is allowed
3. Verify credentials are enabled

### 401 Errors
If you get 401 errors:
1. Check token is being sent in headers
2. Verify token hasn't expired
3. Check backend JWT configuration matches

### Network Errors
If requests fail:
1. Verify backend is running on port 8000
2. Check `VITE_API_BASE_URL` in `.env`
3. Ensure no firewall blocking requests
