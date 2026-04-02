import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/auth/ProtectedRoute';
import { AppLayout } from './components/layout/AppLayout';
import { PublicLayout } from './components/layout/PublicLayout';
import { LoadingSpinner } from './components/common';

// Lazy load page components for code splitting
const HomePage = lazy(() => import('./pages/HomePage').then(m => ({ default: m.HomePage })));
const AboutPage = lazy(() => import('./pages/AboutPage').then(m => ({ default: m.AboutPage })));
const PricingPage = lazy(() => import('./pages/PricingPage').then(m => ({ default: m.PricingPage })));
const HelpCenterPage = lazy(() => import('./pages/HelpCenterPage').then(m => ({ default: m.HelpCenterPage })));
const ContactPage = lazy(() => import('./pages/ContactPage').then(m => ({ default: m.ContactPage })));
const LoginPage = lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const RegisterPage = lazy(() => import('./pages/RegisterPage').then(m => ({ default: m.RegisterPage })));
const DashboardPage = lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const ScenesPage = lazy(() => import('./pages/ScenesPage').then(m => ({ default: m.ScenesPage })));
const ViewerPage = lazy(() => import('./pages/ViewerPage').then(m => ({ default: m.ViewerPage })));
const PhotosPage = lazy(() => import('./pages/PhotosPage').then(m => ({ default: m.PhotosPage })));
const GeospatialPage = lazy(() => import('./pages/GeospatialPage').then(m => ({ default: m.GeospatialPage })));
const ReportsPage = lazy(() => import('./pages/ReportsPage').then(m => ({ default: m.ReportsPage })));
const CollaborationPage = lazy(() => import('./pages/CollaborationPage').then(m => ({ default: m.CollaborationPage })));
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const PhotoInspectorPage = lazy(() => import('./pages/PhotoInspectorPage').then(m => ({ default: m.PhotoInspectorPage })));
const PublicSceneViewerPage = lazy(() => import('./pages/PublicSceneViewerPage').then(m => ({ default: m.PublicSceneViewerPage })));
const EmbedViewerPage = lazy(() => import('./pages/EmbedViewerPage').then(m => ({ default: m.EmbedViewerPage })));

// Suspense wrapper for lazy-loaded components
const SuspenseWrapper = ({ children }: { children: React.ReactNode }) => (
  <Suspense fallback={<LoadingSpinner fullScreen />}>
    {children}
  </Suspense>
);

/**
 * Router configuration for the application
 * 
 * Structure:
 * - Public pages (/, /login, /register) - accessible to all
 * - Protected pages (/dashboard, /scenes/:id, /photos/:id, /settings) - require authentication
 * 
 * All routes use React.lazy for code splitting to reduce initial bundle size
 * 
 * Requirements: 24.1, 24.5, 24.6, 21.1, 21.2
 */
export const router = createBrowserRouter([
  // Home page - standalone without layout
  {
    path: '/',
    element: (
      <SuspenseWrapper>
        <HomePage />
      </SuspenseWrapper>
    ),
  },

  // Public pages
  {
    path: '/about',
    element: (
      <SuspenseWrapper>
        <AboutPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/pricing',
    element: (
      <SuspenseWrapper>
        <PricingPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/help',
    element: (
      <SuspenseWrapper>
        <HelpCenterPage />
      </SuspenseWrapper>
    ),
  },
  {
    path: '/contact',
    element: (
      <SuspenseWrapper>
        <ContactPage />
      </SuspenseWrapper>
    ),
  },

  // Public routes with PublicLayout (login/register)
  {
    path: '/login',
    element: <PublicLayout />,
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <LoginPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/register',
    element: <PublicLayout />,
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <RegisterPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },

  // Protected routes with AppLayout
  {
    path: '/dashboard',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <DashboardPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/scenes',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <ScenesPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/scenes/:id',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <ViewerPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/photos',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <PhotosPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/photos/:photoId',
    element: (
      <ProtectedRoute>
        <SuspenseWrapper>
          <PhotoInspectorPage />
        </SuspenseWrapper>
      </ProtectedRoute>
    ),
  },
  {
    path: '/geospatial',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <GeospatialPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/reports',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <ReportsPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/collaboration',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <CollaborationPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },
  {
    path: '/settings',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      {
        index: true,
        element: (
          <SuspenseWrapper>
            <SettingsPage />
          </SuspenseWrapper>
        ),
      },
    ],
  },

  // Public scene viewer (no auth required)
  {
    path: '/public/scenes/:sceneId',
    element: (
      <SuspenseWrapper>
        <PublicSceneViewerPage />
      </SuspenseWrapper>
    ),
  },

  // Embed viewer (no auth required)
  {
    path: '/embed/scenes/:id',
    element: (
      <SuspenseWrapper>
        <EmbedViewerPage />
      </SuspenseWrapper>
    ),
  },

  // Catch-all redirect
  {
    path: '*',
    element: <Navigate to="/" replace />,
  },
]);
