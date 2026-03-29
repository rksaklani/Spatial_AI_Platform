/**
 * Base API configuration using RTK Query
 * Includes automatic token refresh and retry logic
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';
import { refreshTokenThunk, logout } from '../slices/authSlice';

const baseQuery = fetchBaseQuery({
  baseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  prepareHeaders: (headers, { getState }) => {
    // Get token from auth state
    const token = (getState() as RootState).auth.token;
    
    // Add authorization header if token exists
    if (token) {
      headers.set('Authorization', `Bearer ${token}`);
    }
    
    return headers;
  },
});

// Track if a refresh is in progress to avoid multiple simultaneous refreshes
let isRefreshing = false;
let refreshPromise: Promise<any> | null = null;

// Base query with automatic token refresh and retry
const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  // Wait for any in-progress refresh before making the request
  if (isRefreshing && refreshPromise) {
    await refreshPromise;
  }

  let result = await baseQuery(args, api, extraOptions);
  
  // Handle 401 Unauthorized - attempt token refresh
  if (result.error && result.error.status === 401) {
    const state = api.getState() as RootState;
    
    // Only attempt refresh if we have a refresh token and aren't already refreshing
    if (state.auth.refreshToken && !isRefreshing) {
      isRefreshing = true;
      
      try {
        // Create a promise for the refresh operation
        refreshPromise = api.dispatch(refreshTokenThunk()).unwrap();
        await refreshPromise;
        
        // Token refresh succeeded, retry the original request
        result = await baseQuery(args, api, extraOptions);
      } catch (error) {
        // Token refresh failed, logout the user
        api.dispatch(logout());
      } finally {
        isRefreshing = false;
        refreshPromise = null;
      }
    } else if (!state.auth.refreshToken) {
      // No refresh token available, logout immediately
      api.dispatch(logout());
    }
  }
  
  return result;
};

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Scene', 'User', 'Annotation', 'Tour', 'Photo', 'Orthophoto', 'Report', 'Organization', 'Import', 'Geospatial', 'Share', 'Collaboration'],
  endpoints: () => ({}),
});
