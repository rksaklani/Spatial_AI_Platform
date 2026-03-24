/**
 * Sharing API endpoints using RTK Query
 * Requirements: 15.2, 15.5
 */

import { baseApi } from './baseApi';
import type { SceneMetadata } from '../../types/scene.types';

interface ShareToken {
  token: string;
  scene_id: string;
  created_at: string;
  expires_at: string | null;
}

export const sharingApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Generate share token
    generateShareToken: builder.mutation<ShareToken, string>({
      query: (sceneId) => ({
        url: `/scenes/${sceneId}/share`,
        method: 'POST',
      }),
      invalidatesTags: (_result, _error, sceneId) => [{ type: 'Scene', id: sceneId }],
    }),

    // Revoke share token
    revokeShareToken: builder.mutation<void, string>({
      query: (sceneId) => ({
        url: `/scenes/${sceneId}/share`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, sceneId) => [{ type: 'Scene', id: sceneId }],
    }),

    // Get public scene (no auth required)
    getPublicScene: builder.query<SceneMetadata, { sceneId: string; token: string }>({
      query: ({ sceneId, token }) => `/public/scenes/${sceneId}?token=${token}`,
    }),
  }),
});

export const {
  useGenerateShareTokenMutation,
  useRevokeShareTokenMutation,
  useGetPublicSceneQuery,
} = sharingApi;
