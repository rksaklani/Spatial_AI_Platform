/**
 * Base API configuration using RTK Query
 */

import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import type { RootState } from '../index';

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

// Base query with error handling and token refresh
const baseQueryWithReauth = async (args: any, api: any, extraOptions: any) => {
  const result = await baseQuery(args, api, extraOptions);
  
  // Handle 401 Unauthorized
  if (result.error && result.error.status === 401) {
    // Dispatch logout action
    const { logout } = await import('../slices/authSlice');
    api.dispatch(logout());
  }
  
  return result;
};

export const baseApi = createApi({
  reducerPath: 'api',
  baseQuery: baseQueryWithReauth,
  tagTypes: ['Scene', 'User', 'Annotation', 'Tour'],
  endpoints: () => ({}),
});
