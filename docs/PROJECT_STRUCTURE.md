# Frontend Project Structure

## Overview

This is a React + TypeScript + Vite application for the Ultimate Spatial AI Platform frontend. It uses Three.js and React Three Fiber for 3D rendering, Redux Toolkit for state management, and Tailwind CSS for styling.

## Directory Structure

```
frontend/
├── src/
│   ├── components/     # React components
│   │   ├── Scene3D.tsx # Example 3D scene component
│   │   └── SceneViewer.tsx # Scene viewer with Redux integration
│   ├── services/       # API clients and service layer
│   │   ├── api.service.ts # Backend API service
│   │   └── httpInterceptor.ts # HTTP client with auth interceptor
│   ├── store/          # Redux store configuration
│   │   ├── index.ts    # Store configuration
│   │   ├── hooks.ts    # Typed Redux hooks
│   │   ├── slices/     # Redux slices
│   │   │   ├── authSlice.ts # Authentication state
│   │   │   ├── sceneSlice.ts # Scene state
│   │   │   └── uiSlice.ts # UI state
│   │   ├── thunks/     # Async thunks
│   │   │   ├── authThunks.ts # Auth operations
│   │   │   └── sceneThunks.ts # Scene operations
│   │   └── middleware/ # Custom middleware
│   │       └── apiMiddleware.ts # API interceptor middleware
│   ├── hooks/          # Custom React hooks
│   │   └── useSceneLoader.ts # Hook for loading scene data
│   ├── types/          # TypeScript type definitions
│   │   └── scene.types.ts # Scene-related types
│   ├── assets/         # Static assets (images, icons)
│   ├── App.tsx         # Main application component
│   ├── App.css         # Application styles
│   ├── main.tsx        # Application entry point with Redux Provider
│   └── index.css       # Global styles with Tailwind directives
├── public/             # Public static files
├── .prettierrc.json    # Prettier configuration
├── .prettierignore     # Prettier ignore patterns
├── eslint.config.js    # ESLint configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── postcss.config.js   # PostCSS configuration
├── tsconfig.json       # TypeScript configuration
├── tsconfig.app.json   # TypeScript app configuration
├── tsconfig.node.json  # TypeScript node configuration
├── vite.config.ts      # Vite configuration
└── package.json        # Dependencies and scripts
```

## Key Technologies

- **React 18.3.1**: UI framework
- **TypeScript 5.9.3**: Type-safe JavaScript
- **Vite 8.0.1**: Build tool and dev server
- **Three.js 0.170.0**: 3D graphics library
- **React Three Fiber 8.17.10**: React renderer for Three.js
- **React Three Drei 9.117.3**: Useful helpers for React Three Fiber
- **Redux Toolkit 2.5.0**: State management
- **React Redux 9.2.0**: React bindings for Redux
- **Tailwind CSS 3.4.17**: Utility-first CSS framework

## Redux Store Structure

### Slices

1. **authSlice**: Manages authentication state
   - User information
   - JWT token
   - Authentication status
   - Loading and error states

2. **sceneSlice**: Manages 3D scene state
   - Current scene metadata
   - Scene list
   - Tiles and loaded tiles
   - Camera position and direction
   - Selected objects

3. **uiSlice**: Manages UI state
   - Sidebar visibility
   - Annotation and measurement modes
   - Notifications
   - Loading states
   - Modal state

### Middleware

- **apiMiddleware**: Intercepts API actions for error handling and logging
  - Handles 401 errors (logout)
  - Handles network errors
  - Handles server errors
  - Logs API calls in development

### HTTP Interceptor

- **httpInterceptor**: Wraps fetch API with authentication and error handling
  - Automatically adds JWT token to requests
  - Handles 401 responses
  - Provides typed methods (get, post, put, patch, delete)
  - Parses errors consistently

## Configuration

### TypeScript

- Strict mode enabled
- Target: ES2023
- Module: ESNext
- JSX: react-jsx

### ESLint

- TypeScript ESLint recommended rules
- React Hooks rules
- React Refresh plugin for HMR

### Prettier

- Single quotes
- 2-space indentation
- 100 character line width
- Trailing commas (ES5)
- Semicolons enabled

### Tailwind CSS

- JIT mode enabled
- Content paths configured for all source files
- Custom theme extensions available

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run lint` - Run ESLint
- `npm run preview` - Preview production build
- `npm run format` - Format code with Prettier
- `npm run format:check` - Check code formatting

## Getting Started

1. Install dependencies:
   ```bash
   npm install
   ```

2. Create environment file `.env`:
   ```
   VITE_API_BASE_URL=http://localhost:8000/api/v1
   ```

3. Start development server:
   ```bash
   npm run dev
   ```

4. Open browser to `http://localhost:5173`

## Using Redux

### Typed Hooks

Always use the typed hooks instead of plain Redux hooks:

```typescript
import { useAppDispatch, useAppSelector } from './store/hooks';

function MyComponent() {
  const dispatch = useAppDispatch();
  const user = useAppSelector((state) => state.auth.user);
  
  // ...
}
```

### Dispatching Actions

```typescript
import { loginSuccess } from './store/slices/authSlice';
import { loginUser } from './store/thunks/authThunks';

// Sync action
dispatch(loginSuccess({ user, token }));

// Async thunk
dispatch(loginUser({ email, password }));
```

### Accessing State

```typescript
const { currentScene, loading, error } = useAppSelector((state) => state.scene);
const { isAuthenticated, user } = useAppSelector((state) => state.auth);
const { sidebarOpen, notifications } = useAppSelector((state) => state.ui);
```

## API Service Usage

The API service uses the HTTP interceptor for all requests:

```typescript
import { apiService } from './services/api.service';

// Fetch scene metadata
const scene = await apiService.fetchSceneMetadata(sceneId);

// Upload video
const newScene = await apiService.uploadVideo(file, organizationId);

// Login (skips auth token)
const { user, token } = await apiService.login(email, password);
```

## Styling with Tailwind

Use Tailwind utility classes for styling:

```tsx
<div className="flex items-center justify-center h-screen bg-gray-900">
  <button className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
    Click Me
  </button>
</div>
```

## Next Steps

- Implement scene viewer components
- Add tile streaming logic
- Implement camera controls
- Add annotation UI
- Implement collaboration features
- Add authentication pages
- Implement file upload UI
