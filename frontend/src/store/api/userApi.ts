/**
 * User API endpoints using RTK Query
 * Requirements: 31.2, 31.3, 31.4, 31.5
 */

import { baseApi } from './baseApi';

interface UpdateProfileRequest {
  name?: string;
  email?: string;
}

interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

interface UserPreferences {
  theme: 'light' | 'dark';
  language: string;
  viewer_settings: {
    default_rendering_mode: 'client' | 'server';
    show_fps: boolean;
    show_coordinates: boolean;
    auto_rotate: boolean;
    quality: 'low' | 'medium' | 'high';
  };
  notification_settings: {
    processing_complete: boolean;
    mentions: boolean;
    collaboration_updates: boolean;
    email: boolean;
  };
}

export const userApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Update user profile
    updateProfile: builder.mutation<void, UpdateProfileRequest>({
      query: (updates) => ({
        url: '/users/profile',
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: [{ type: 'User', id: 'CURRENT' }],
    }),

    // Change password
    changePassword: builder.mutation<void, ChangePasswordRequest>({
      query: (passwords) => ({
        url: '/users/password',
        method: 'POST',
        body: passwords,
      }),
    }),

    // Get user preferences
    getPreferences: builder.query<UserPreferences, void>({
      query: () => '/users/preferences',
      providesTags: [{ type: 'User', id: 'PREFERENCES' }],
    }),

    // Update user preferences
    updatePreferences: builder.mutation<void, Partial<UserPreferences>>({
      query: (preferences) => ({
        url: '/users/preferences',
        method: 'PATCH',
        body: preferences,
      }),
      invalidatesTags: [{ type: 'User', id: 'PREFERENCES' }],
    }),
  }),
});

export const {
  useUpdateProfileMutation,
  useChangePasswordMutation,
  useGetPreferencesQuery,
  useUpdatePreferencesMutation,
} = userApi;
