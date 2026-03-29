/**
 * Sharing API endpoints using RTK Query
 */

import { baseApi } from './baseApi';

export interface ShareToken {
  token: string;
  sceneId: string;
  permissions: 'view' | 'edit';
  createdAt: string;
  expiresAt: string;
  isExpired: boolean;
  createdBy: string;
}

export interface CreateShareTokenRequest {
  sceneId: string;
  expiresInDays: number;
  permissions: 'view' | 'edit';
}

export interface ShareTokenResponse {
  token: string;
  url: string;
  expiresAt: string;
}

export const sharingApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get all share tokens for a scene
    getShareTokens: builder.query<ShareToken[], string>({
      query: (sceneId) => `/scenes/${sceneId}/share`,
      providesTags: (_result, _error, sceneId) => [{ type: 'Share', id: sceneId }],
    }),

    // Create a new share token
    createShareToken: builder.mutation<ShareTokenResponse, CreateShareTokenRequest>({
      query: ({ sceneId, expiresInDays, permissions }) => ({
        url: `/scenes/${sceneId}/share`,
        method: 'POST',
        body: {
          expires_in_days: expiresInDays,
          permissions,
        },
      }),
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Share', id: sceneId }],
    }),

    // Revoke a share token
    revokeShareToken: builder.mutation<void, { sceneId: string; token: string }>({
      query: ({ sceneId, token }) => ({
        url: `/scenes/${sceneId}/share/${token}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Share', id: sceneId }],
    }),

    // Get scene by share token (public access)
    getSceneByShareToken: builder.query<any, string>({
      query: (token) => `/shared/${token}`,
    }),

    // Validate share token
    validateShareToken: builder.query<{ valid: boolean; permissions: string }, string>({
      query: (token) => `/shared/${token}/validate`,
    }),
  }),
});

export const {
  useGetShareTokensQuery,
  useCreateShareTokenMutation,
  useRevokeShareTokenMutation,
  useGetSceneByShareTokenQuery,
  useValidateShareTokenQuery,
} = sharingApi;
