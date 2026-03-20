# RTK Query Integration Guide

## Overview

This project uses **RTK Query** for efficient data fetching and caching. RTK Query is Redux Toolkit's powerful data fetching and caching tool that simplifies API interactions.

## Architecture

### Base API Configuration

Located in `src/store/api/baseApi.ts`, this file configures:
- Base URL for all API requests
- Automatic authentication token injection
- Token refresh logic
- 401 error handling (auto-logout)
- Cache tag types for invalidation

```typescript
import { baseApi } from './store/api/baseApi';

// All API endpoints extend from baseApi
export const myApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Define endpoints here
  }),
});
```

### API Endpoints

#### Scene API (`src/store/api/sceneApi.ts`)
Handles all scene-related operations:
- `useGetSceneByIdQuery` - Fetch single scene
- `useGetScenesQuery` - Fetch all scenes
- `useGetSceneTilesQuery` - Fetch scene tiles for streaming
- `useUploadVideoMutation` - Upload video file
- `useImportFileMutation` - Import 3D file
- `useUpdateSceneMutation` - Update scene metadata
- `useDeleteSceneMutation` - Delete scene

#### Auth API (`src/store/api/authApi.ts`)
Handles authentication:
- `useLoginMutation` - User login
- `useRegisterMutation` - User registration
- `useLogoutMutation` - User logout
- `useGetCurrentUserQuery` - Get current user info
- `useRefreshTokenMutation` - Refresh JWT token

#### Annotation API (`src/store/api/annotationApi.ts`)
Handles scene annotations:
- `useGetAnnotationsQuery` - Fetch annotations for a scene
- `useCreateAnnotationMutation` - Create new annotation
- `useUpdateAnnotationMutation` - Update annotation
- `useDeleteAnnotationMutation` - Delete annotation

## Usage Examples

### Fetching Data (Query)

```typescript
import { useGetSceneByIdQuery } from '../store/api/sceneApi';

function SceneViewer({ sceneId }: { sceneId: string }) {
  const { data, isLoading, error, refetch } = useGetSceneByIdQuery(sceneId);

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error loading scene</div>;
  if (!data) return <div>No scene found</div>;

  return (
    <div>
      <h1>{data.name}</h1>
      <button onClick={refetch}>Refresh</button>
    </div>
  );
}
```

### Mutating Data (Mutation)

```typescript
import { useUploadVideoMutation } from '../store/api/sceneApi';
import { useDispatch } from 'react-redux';
import { addNotification } from '../store/slices/uiSlice';

function VideoUploader() {
  const dispatch = useDispatch();
  const [uploadVideo, { isLoading }] = useUploadVideoMutation();

  const handleUpload = async (file: File) => {
    try {
      const result = await uploadVideo({
        file,
        organizationId: 'org-123',
      }).unwrap();

      dispatch(addNotification({
        type: 'success',
        message: 'Video uploaded successfully!',
      }));

      console.log('Uploaded scene:', result);
    } catch (error) {
      dispatch(addNotification({
        type: 'error',
        message: 'Upload failed',
      }));
    }
  };

  return (
    <button onClick={() => handleUpload(file)} disabled={isLoading}>
      {isLoading ? 'Uploading...' : 'Upload Video'}
    </button>
  );
}
```

### Authentication Example

```typescript
import { useLoginMutation } from '../store/api/authApi';
import { useDispatch } from 'react-redux';
import { loginSuccess } from '../store/slices/authSlice';

function LoginForm() {
  const dispatch = useDispatch();
  const [login, { isLoading }] = useLoginMutation();

  const handleLogin = async (email: string, password: string) => {
    try {
      const result = await login({ email, password }).unwrap();
      
      // Update auth state
      dispatch(loginSuccess(result));
      
      // Navigate to dashboard
      navigate('/dashboard');
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleLogin(email, password);
    }}>
      {/* Form fields */}
    </form>
  );
}
```

## Key Features

### Automatic Caching

RTK Query automatically caches responses and reuses them:

```typescript
// First call - fetches from server
const { data: scene1 } = useGetSceneByIdQuery('scene-123');

// Second call with same ID - uses cache
const { data: scene2 } = useGetSceneByIdQuery('scene-123');
```

### Cache Invalidation

Mutations automatically invalidate related queries:

```typescript
// When you delete a scene, the scene list is automatically refetched
const [deleteScene] = useDeleteSceneMutation();

await deleteScene('scene-123');
// useGetScenesQuery will automatically refetch
```

### Optimistic Updates

You can update the UI before the server responds:

```typescript
const [updateScene] = useUpdateSceneMutation();

await updateScene({
  sceneId: 'scene-123',
  updates: { name: 'New Name' },
});
```

### Polling

Automatically refetch data at intervals:

```typescript
const { data } = useGetSceneByIdQuery('scene-123', {
  pollingInterval: 5000, // Refetch every 5 seconds
});
```

### Conditional Fetching

Skip queries based on conditions:

```typescript
const { data } = useGetSceneByIdQuery(sceneId, {
  skip: !sceneId, // Don't fetch if sceneId is null/undefined
});
```

## HTTP Interceptor

The `httpInterceptor.ts` provides a wrapper around fetch with:
- Automatic JWT token injection
- 401 error handling (auto-logout)
- Consistent error parsing
- Type-safe methods (get, post, put, patch, delete)

```typescript
import { httpClient } from '../services/httpInterceptor';

// GET request
const data = await httpClient.get<MyType>('/endpoint');

// POST request
const result = await httpClient.post<MyType>('/endpoint', { data });

// Skip authentication for public endpoints
const public Data = await httpClient.get('/public', { skipAuth: true });
```

## API Middleware

The `apiMiddleware.ts` intercepts all actions and:
- Handles 401 errors (dispatches logout)
- Handles network errors (shows notification)
- Handles server errors (shows notification)
- Logs API calls in development

## Best Practices

### 1. Use Generated Hooks

Always use the generated hooks instead of manual dispatch:

```typescript
// ✅ Good
const { data } = useGetSceneByIdQuery(sceneId);

// ❌ Bad
const data = useSelector(state => state.api.queries[...]);
```

### 2. Handle Loading and Error States

```typescript
const { data, isLoading, error, isFetching } = useGetSceneByIdQuery(sceneId);

if (isLoading) return <Spinner />;
if (error) return <ErrorMessage error={error} />;
if (!data) return <EmptyState />;

return <SceneView scene={data} />;
```

### 3. Use unwrap() for Mutations

```typescript
try {
  const result = await mutation(args).unwrap();
  // Handle success
} catch (error) {
  // Handle error
}
```

### 4. Invalidate Tags Properly

```typescript
// Invalidate specific item
invalidatesTags: [{ type: 'Scene', id: sceneId }]

// Invalidate list
invalidatesTags: [{ type: 'Scene', id: 'LIST' }]

// Invalidate both
invalidatesTags: [
  { type: 'Scene', id: sceneId },
  { type: 'Scene', id: 'LIST' },
]
```

### 5. Type Your Responses

```typescript
interface Scene {
  id: string;
  name: string;
  // ...
}

getScene: builder.query<Scene, string>({
  query: (id) => `/scenes/${id}`,
}),
```

## Debugging

### Redux DevTools

RTK Query integrates with Redux DevTools. You can see:
- All API requests
- Cache state
- Query subscriptions
- Mutation status

### Enable Logging

API calls are logged in development mode automatically.

## Migration from Thunks

If you have existing thunks, migrate to RTK Query:

**Before (Thunk):**
```typescript
export const fetchScene = createAsyncThunk(
  'scene/fetch',
  async (id: string) => {
    const response = await fetch(`/api/scenes/${id}`);
    return response.json();
  }
);

// In component
useEffect(() => {
  dispatch(fetchScene(sceneId));
}, [sceneId]);
```

**After (RTK Query):**
```typescript
// In API file
getScene: builder.query<Scene, string>({
  query: (id) => `/scenes/${id}`,
}),

// In component
const { data } = useGetSceneByIdQuery(sceneId);
```

## Resources

- [RTK Query Documentation](https://redux-toolkit.js.org/rtk-query/overview)
- [RTK Query Examples](https://redux-toolkit.js.org/rtk-query/usage/examples)
- [Cache Behavior](https://redux-toolkit.js.org/rtk-query/usage/cache-behavior)
