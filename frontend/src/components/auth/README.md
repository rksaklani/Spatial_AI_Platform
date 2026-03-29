# Authentication Components

## ProtectedRoute

The `ProtectedRoute` component wraps routes that require authentication. It provides the following features:

### Features

1. **Authentication Check**: Verifies if the user is authenticated via Redux state
2. **Loading State**: Shows a loading indicator while checking authentication
3. **Redirect to Login**: Redirects unauthenticated users to `/login`
4. **Preserve Intended Destination**: Saves the original URL the user tried to access

### How It Works

When an unauthenticated user tries to access a protected route:

1. `ProtectedRoute` detects the user is not authenticated
2. It captures the current location (the page they tried to access)
3. It redirects to `/login` with the location stored in navigation state
4. After successful login, `LoginForm` reads this state and redirects back to the original destination

### Usage Example

```tsx
// In router.tsx
{
  path: '/dashboard',
  element: (
    <ProtectedRoute>
      <AppLayout />
    </ProtectedRoute>
  ),
}
```

### Flow Example

1. User tries to access `/scenes/123` (not authenticated)
2. `ProtectedRoute` redirects to `/login` with `state={{ from: { pathname: '/scenes/123' } }}`
3. User logs in successfully
4. `LoginForm` reads `location.state.from.pathname` and redirects to `/scenes/123`
5. User lands on the page they originally intended to visit

### Requirements

- **1.1**: User authentication and session management
- **24.7**: Redirect to login when accessing protected routes without authentication
