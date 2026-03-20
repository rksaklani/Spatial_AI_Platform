/**
 * API middleware for intercepting and handling API requests
 * This middleware adds authentication tokens, handles errors, and logs requests
 */

import type { Middleware } from '@reduxjs/toolkit';
import { logout } from '../slices/authSlice';
import { addNotification } from '../slices/uiSlice';

export const apiMiddleware: Middleware = (store) => (next) => (action: any) => {
  // Pass the action to the next middleware/reducer
  const result = next(action);

  // Intercept specific action types for API calls
  if (action.type && typeof action.type === 'string') {
    // Handle authentication errors
    if (action.type.endsWith('/rejected') && action.payload?.status === 401) {
      store.dispatch(logout());
      store.dispatch(
        addNotification({
          type: 'error',
          message: 'Session expired. Please login again.',
          duration: 5000,
        })
      );
    }

    // Handle network errors
    if (action.type.endsWith('/rejected') && action.error?.message === 'Network Error') {
      store.dispatch(
        addNotification({
          type: 'error',
          message: 'Network error. Please check your connection.',
          duration: 5000,
        })
      );
    }

    // Handle server errors
    if (action.type.endsWith('/rejected') && action.payload?.status >= 500) {
      store.dispatch(
        addNotification({
          type: 'error',
          message: 'Server error. Please try again later.',
          duration: 5000,
        })
      );
    }

    // Log API calls in development
    if (import.meta.env.DEV && action.type.includes('api/')) {
      console.log('[API Middleware]', action.type, action);
    }
  }

  return result;
};
