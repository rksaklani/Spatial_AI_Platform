/**
 * Authentication slice for managing user authentication state
 */

import { createSlice, type PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import type { RootState } from '../index';

interface User {
  id: string;
  email: string;
  name: string;
  organizationId: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  refreshToken: string | null;
  tokenExpiresAt: number | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  refreshing: boolean;
  refreshRetryCount: number;
}

const initialState: AuthState = {
  user: null,
  token: null,
  refreshToken: null,
  tokenExpiresAt: null,
  isAuthenticated: false,
  loading: false,
  error: null,
  refreshing: false,
  refreshRetryCount: 0,
};

// Async thunk for refreshing token with automatic retry
export const refreshTokenThunk = createAsyncThunk<
  { token: string; refreshToken: string; expiresIn: number },
  void,
  { state: RootState; rejectValue: string }
>(
  'auth/refreshToken',
  async (_, { getState, rejectWithValue }) => {
    const state = getState();
    const currentRefreshToken = state.auth.refreshToken;

    if (!currentRefreshToken) {
      return rejectWithValue('No refresh token available');
    }

    try {
      const response = await fetch(
        `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'}/auth/refresh`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ refresh_token: currentRefreshToken }),
        }
      );

      if (!response.ok) {
        throw new Error('Token refresh failed');
      }

      const data = await response.json();
      
      // JWT tokens typically expire in 15 minutes (900 seconds)
      // We'll use the standard expiration or default to 15 minutes
      const expiresIn = data.expires_in || 900;

      return {
        token: data.access_token,
        refreshToken: data.refresh_token || currentRefreshToken,
        expiresIn,
      };
    } catch (error) {
      return rejectWithValue(error instanceof Error ? error.message : 'Token refresh failed');
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (
      state,
      action: PayloadAction<{ user: User; token: string; refreshToken: string; expiresIn?: number }>
    ) => {
      state.loading = false;
      state.isAuthenticated = true;
      state.user = action.payload.user;
      state.token = action.payload.token;
      state.refreshToken = action.payload.refreshToken;
      
      // Calculate token expiration time (default to 15 minutes if not provided)
      const expiresIn = action.payload.expiresIn || 900;
      state.tokenExpiresAt = Date.now() + expiresIn * 1000;
      
      state.error = null;
      state.refreshRetryCount = 0;
    },
    loginFailure: (state, action: PayloadAction<string>) => {
      state.loading = false;
      state.isAuthenticated = false;
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.tokenExpiresAt = null;
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = null;
      state.token = null;
      state.refreshToken = null;
      state.tokenExpiresAt = null;
      state.isAuthenticated = false;
      state.error = null;
      state.refreshing = false;
      state.refreshRetryCount = 0;
    },
    setUser: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      state.isAuthenticated = true;
    },
    clearError: (state) => {
      state.error = null;
    },
    resetRefreshRetryCount: (state) => {
      state.refreshRetryCount = 0;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(refreshTokenThunk.pending, (state) => {
        state.refreshing = true;
        state.error = null;
      })
      .addCase(refreshTokenThunk.fulfilled, (state, action) => {
        state.refreshing = false;
        state.token = action.payload.token;
        state.refreshToken = action.payload.refreshToken;
        state.tokenExpiresAt = Date.now() + action.payload.expiresIn * 1000;
        state.refreshRetryCount = 0;
        state.error = null;
      })
      .addCase(refreshTokenThunk.rejected, (state, action) => {
        state.refreshing = false;
        state.refreshRetryCount += 1;
        
        // If retry count exceeds 3, clear auth state
        if (state.refreshRetryCount >= 3) {
          state.user = null;
          state.token = null;
          state.refreshToken = null;
          state.tokenExpiresAt = null;
          state.isAuthenticated = false;
          state.error = 'Session expired. Please log in again.';
        } else {
          state.error = action.payload || 'Token refresh failed';
        }
      });
  },
});

export const {
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  setUser,
  clearError,
  resetRefreshRetryCount,
} = authSlice.actions;

// Selectors
export const selectIsTokenExpired = (state: RootState): boolean => {
  if (!state.auth.tokenExpiresAt) return false;
  // Consider token expired if it expires in less than 1 minute
  return Date.now() >= state.auth.tokenExpiresAt - 60000;
};

export const selectShouldRefreshToken = (state: RootState): boolean => {
  return (
    state.auth.isAuthenticated &&
    !state.auth.refreshing &&
    selectIsTokenExpired(state) &&
    state.auth.refreshRetryCount < 3
  );
};

export default authSlice.reducer;
