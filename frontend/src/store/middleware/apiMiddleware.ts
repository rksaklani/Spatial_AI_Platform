/**
 * API middleware for intercepting and handling API requests
 * This middleware adds authentication tokens, handles errors, and manages token refresh
 */

import type { Middleware } from '@reduxjs/toolkit';
import { logout, refreshTokenThunk, selectShouldRefreshToken } from '../slices/authSlice';
import { addNotification } from '../slices/uiSlice';
import type { RootState } from '../index';

// Track if a refresh is in progress to avoid multiple simultaneous refreshes
let isRefreshing = false;

export const apiMiddleware: Middleware = (store) => (next) => (action: any) => {
  const state = store.getState() as RootState;

  // Check if we should refresh the token before processing the action
  if (selectShouldRefreshToken(state) && !isRefreshing) {
    isRefreshing = true;
    (store.dispatch as any)(refreshTokenThunk()).finally(() => {
      isRefreshing = false;
    });
  }

  // Pass the action to the next middleware/reducer
  const result = next(action);

  // Intercept specific action types for API calls
  if (action.type && typeof action.type === 'string') {
    // Handle 401 authentication errors
    if (action.type.endsWith('/rejected') && action.payload?.status === 401) {
      // If we have a refresh token, try to refresh
      if (state.auth.refreshToken && !isRefreshing) {
        isRefreshing = true;
        (store.dispatch as any)(refreshTokenThunk()).then(
          (refreshResult: any) => {
            isRefreshing = false;
            // If refresh succeeded, the original request will be retried by baseApi
            if (refreshResult.meta?.requestStatus === 'fulfilled') {
              console.log('[API Middleware] Token refreshed successfully');
            }
          },
          () => {
            isRefreshing = false;
            // If refresh failed, logout and show error
            store.dispatch(logout());
            store.dispatch(
              addNotification({
                type: 'error',
                message: 'Session expired. Please login again.',
                duration: 5000,
              })
            );
          }
        );
      } else if (!state.auth.refreshToken) {
        // No refresh token available, logout immediately
        store.dispatch(logout());
        store.dispatch(
          addNotification({
            type: 'error',
            message: 'Session expired. Please login again.',
            duration: 5000,
          })
        );
      }
    }

    // Handle 403 forbidden errors
    if (action.type.endsWith('/rejected') && action.payload?.status === 403) {
      store.dispatch(
        addNotification({
          type: 'error',
          message: 'Access denied. You do not have permission to perform this action.',
          duration: 5000,
        })
      );
    }

    // Handle 404 not found errors
    if (action.type.endsWith('/rejected') && action.payload?.status === 404) {
      store.dispatch(
        addNotification({
          type: 'error',
          message: 'Resource not found.',
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
