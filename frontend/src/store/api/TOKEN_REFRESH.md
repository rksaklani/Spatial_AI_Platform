# Token Refresh Middleware Documentation

## Overview

The token refresh middleware automatically handles expired authentication tokens by intercepting 401 responses, refreshing the token, and retrying the original request. This provides a seamless user experience without requiring manual re-authentication.

## Requirements Satisfied

- **Requirement 1.3**: Automatically refresh access tokens using refresh tokens when they expire
- **Requirement 1.4**: Redirect to login page when refresh token expires or is invalid
- **Requirement 19.4**: Handle 401 errors appropriately across all API endpoints

## Implementation

### Location

- **File**: `frontend/src/store/api/baseApi.ts`
- **Function**: `baseQueryWithReauth`

### How It Works

```
┌─────────────────────────────────────────────────────────────┐
│  1. API Request Made                                         │
│     ↓                                                        │
│  2. Check if refresh in progress → Wait if yes              │
│     ↓                                                        │
│  3. Execute request with current token                       │
│     ↓                                                        │
│  4. Response received                                        │
│     ├─ Success (200-299) → Return response                  │
│     └─ 401 Unauthorized                                      │
│         ├─ Has refresh token?                               │
│         │   ├─ Yes → Attempt refresh                        │
│         │   │   ├─ Success → Retry original request         │
│         │   │   └─ Failure → Logout user                    │
│         │   └─ No → Logout user immediately                 │
│         └─ Return response                                   │
└─────────────────────────────────────────────────────────────┘
```

### Key Features

#### 1. Concurrent Request Handling

The middleware prevents multiple simultaneous token refresh attempts:

```typescript
let isRefreshing = false;
let refreshPromise: Promise<any> | null = null;

// Wait for any in-progress refresh before making the request
if (isRefreshing && refreshPromise) {
  await refreshPromise;
}
```

**Why this matters**: If multiple API calls fail with 401 at the same time, we only refresh the token once and all requests wait for that single refresh to complete.

#### 2. Automatic Token Injection

The `prepareHeaders` function automatically adds the Authorization header:

```typescript
prepareHeaders: (headers, { getState }) => {
  const token = (getState() as RootState).auth.token;
  if (token) {
    headers.set('Authorization', `Bearer ${token}`);
  }
  return headers;
}
```

#### 3. Graceful Failure Handling

When token refresh fails, the user is automatically logged out:

```typescript
try {
  refreshPromise = api.dispatch(refreshTokenThunk()).unwrap();
  await refreshPromise;
  result = await baseQuery(args, api, extraOptions);
} catch (error) {
  api.dispatch(logout());
}
```

## Usage

### For Developers

The middleware works automatically for all RTK Query endpoints. No special configuration needed:

```typescript
// Define your API endpoint normally
const sceneApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    getScenes: builder.query<Scene[], void>({
      query: () => '/scenes',
    }),
  }),
});

// Use it in your component
const { data, error } = useGetScenesQuery();

// Token refresh happens automatically if the token expires!
```

### Token Expiration Tracking

The auth slice tracks token expiration:

```typescript
interface AuthState {
  token: string | null;
  refreshToken: string | null;
  tokenExpiresAt: number | null;  // Timestamp when token expires
  refreshing: boolean;             // True during refresh
  refreshRetryCount: number;       // Number of failed refresh attempts
}
```

### Manual Token Refresh

You can manually trigger a token refresh if needed:

```typescript
import { refreshTokenThunk } from '@/store/slices/authSlice';

// In a component or thunk
dispatch(refreshTokenThunk());
```

## Testing

### Test Coverage

The implementation is tested in `frontend/src/store/api/__tests__/tokenRefresh.test.ts`:

1. **Automatic token refresh** - Verifies 401 triggers refresh
2. **Logout on refresh failure** - Verifies logout when refresh fails
3. **401 error handling** - Verifies all endpoints handle 401
4. **Token expiration tracking** - Verifies expiration timestamps
5. **Authorization headers** - Verifies tokens are included in requests

### Running Tests

```bash
cd frontend
npm test -- tokenRefresh.test.ts
```

## Error Scenarios

### Scenario 1: Token Expires During Request

```
User makes API call → 401 response → Token refresh → Retry with new token → Success
```

**User Experience**: Seamless, no interruption

### Scenario 2: Refresh Token Invalid

```
User makes API call → 401 response → Token refresh fails → User logged out → Redirect to login
```

**User Experience**: Redirected to login page with message

### Scenario 3: Multiple Concurrent Requests

```
Request A → 401
Request B → 401  } Both wait for single refresh
Request C → 401
↓
Single token refresh
↓
All requests retry with new token
```

**User Experience**: Seamless, efficient (only one refresh call)

### Scenario 4: Network Error During Refresh

```
User makes API call → 401 response → Token refresh network error → User logged out
```

**User Experience**: Redirected to login with error message

## Configuration

### Token Expiration Time

Default: 15 minutes (900 seconds)

Configure in login response:

```typescript
loginSuccess({
  user,
  token,
  refreshToken,
  expiresIn: 900  // seconds
})
```

### Refresh Retry Limit

Default: 3 attempts

Configured in `authSlice.ts`:

```typescript
if (state.refreshRetryCount >= 3) {
  // Clear auth state and logout
}
```

### API Base URL

Set via environment variable:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
```

## Security Considerations

1. **Tokens stored in Redux state** - Persisted securely with redux-persist
2. **Refresh tokens never exposed** - Only sent to `/auth/refresh` endpoint
3. **Automatic logout on failure** - Prevents unauthorized access
4. **HTTPS required in production** - Tokens transmitted securely

## Troubleshooting

### Issue: Token refresh loops infinitely

**Cause**: Backend returns 401 even after successful refresh

**Solution**: Verify backend is accepting the new token correctly

### Issue: User logged out unexpectedly

**Cause**: Refresh token expired or invalid

**Solution**: Check token expiration times and refresh token validity

### Issue: Multiple refresh calls being made

**Cause**: `isRefreshing` flag not working correctly

**Solution**: Verify the flag is properly scoped and shared across requests

## Future Enhancements

1. **Proactive token refresh** - Refresh before expiration (e.g., at 80% of lifetime)
2. **Token refresh queue** - Queue requests during refresh instead of waiting
3. **Exponential backoff** - Retry refresh with increasing delays
4. **Token refresh notifications** - Notify user when token is refreshed
5. **Offline token handling** - Handle token expiration when offline

## Related Files

- `frontend/src/store/api/baseApi.ts` - Main implementation
- `frontend/src/store/api/authApi.ts` - Auth endpoints
- `frontend/src/store/slices/authSlice.ts` - Auth state management
- `frontend/src/store/api/__tests__/tokenRefresh.test.ts` - Tests

## References

- [RTK Query Authentication](https://redux-toolkit.js.org/rtk-query/usage/customizing-queries#automatic-re-authorization-by-extending-fetchbasequery)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OAuth 2.0 Token Refresh](https://tools.ietf.org/html/rfc6749#section-6)
