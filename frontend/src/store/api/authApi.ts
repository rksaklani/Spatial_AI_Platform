/**
 * Authentication API endpoints using RTK Query
 * Connected to FastAPI backend at /api/v1/auth
 */

import { baseApi } from './baseApi';

// Backend response types
interface UserResponse {
  _id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// Frontend types
interface User {
  id: string;
  email: string;
  name: string;
  organizationId: string;
}

interface LoginRequest {
  username: string; // Backend expects 'username' field (OAuth2 standard)
  password: string;
}

interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

interface AuthResponse {
  user: User;
  token: string;
  refreshToken: string;
}

export const authApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Login - OAuth2 password flow
    login: builder.mutation<AuthResponse, { email: string; password: string }>({
      query: (credentials) => {
        // Convert to form data for OAuth2
        const formData = new URLSearchParams();
        formData.append('username', credentials.email);
        formData.append('password', credentials.password);
        
        return {
          url: '/auth/login',
          method: 'POST',
          body: formData,
          headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
          },
        };
      },
      transformResponse: async (response: TokenResponse, meta, arg) => {
        // Fetch user info after login
        const userResponse = await fetch(
          `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/auth/me`,
          {
            headers: {
              Authorization: `Bearer ${response.access_token}`,
            },
          }
        );
        
        const userData: UserResponse = await userResponse.json();
        
        return {
          user: {
            id: userData._id,
            email: userData.email,
            name: userData.full_name,
            organizationId: 'default-org', // TODO: Get from user data
          },
          token: response.access_token,
          refreshToken: response.refresh_token,
        };
      },
      invalidatesTags: ['User'],
    }),

    // Register
    register: builder.mutation<UserResponse, RegisterRequest>({
      query: (userData) => ({
        url: '/auth/register',
        method: 'POST',
        body: userData,
      }),
      invalidatesTags: ['User'],
    }),

    // Logout
    logout: builder.mutation<{ message: string }, void>({
      query: () => ({
        url: '/auth/logout',
        method: 'POST',
      }),
      invalidatesTags: ['User'],
    }),

    // Get current user
    getCurrentUser: builder.query<UserResponse, void>({
      query: () => '/auth/me',
      providesTags: ['User'],
    }),

    // Refresh token
    refreshToken: builder.mutation<TokenResponse, { refresh_token: string }>({
      query: (body) => ({
        url: '/auth/refresh',
        method: 'POST',
        body,
      }),
    }),
  }),
});

export const {
  useLoginMutation,
  useRegisterMutation,
  useLogoutMutation,
  useGetCurrentUserQuery,
  useRefreshTokenMutation,
} = authApi;
