/**
 * Scene API endpoints using RTK Query
 */

import { baseApi } from './baseApi';
import type { SceneMetadata, SceneTile } from '../../types/scene.types';

export const sceneApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get scene by ID
    getSceneById: builder.query<SceneMetadata, string>({
      query: (sceneId) => `/scenes/${sceneId}`,
      providesTags: (_result, _error, sceneId) => [{ type: 'Scene', id: sceneId }],
    }),

    // Get all scenes for organization
    getScenes: builder.query<SceneMetadata[], void>({
      query: () => '/scenes',
      transformResponse: (response: { items: any[] }) => {
        // Transform backend response (_id) to frontend format (sceneId)
        return response.items.map(scene => ({
          ...scene,
          sceneId: scene._id || scene.sceneId,
          organizationId: scene.organization_id || scene.organizationId,
          userId: scene.owner_id || scene.userId,
          sourceType: scene.source_type || scene.sourceType,
          sourceFormat: scene.source_format || scene.sourceFormat,
          fileUrl: scene.file_url || scene.fileUrl,
          captureDate: scene.capture_date || scene.captureDate,
          processingTime: scene.processing_time || scene.processingTime,
          createdAt: scene.created_at || scene.createdAt,
          updatedAt: scene.updated_at || scene.updatedAt,
          tileCount: scene.tile_count || scene.tileCount || 0,
          gaussianCount: scene.gaussian_count || scene.gaussianCount || 0,
          bounds: scene.bounds || { min: [0, 0, 0], max: [0, 0, 0] },
        })),
      },
      providesTags: (result) =>
        result
          ? [
              ...result.map(({ sceneId }) => ({ type: 'Scene' as const, id: sceneId })),
              { type: 'Scene', id: 'LIST' },
            ]
          : [{ type: 'Scene', id: 'LIST' }],
    }),

    // Get scene tiles
    getSceneTiles: builder.query<
      { tiles: SceneTile[] },
      {
        sceneId: string;
        cameraPosition: [number, number, number];
        cameraDirection: [number, number, number];
        fov: number;
        bandwidth: number;
      }
    >({
      query: ({ sceneId, cameraPosition, cameraDirection, fov, bandwidth }) => {
        const params = new URLSearchParams({
          cameraPosition: cameraPosition.join(','),
          cameraDirection: cameraDirection.join(','),
          fov: fov.toString(),
          bandwidth: bandwidth.toString(),
        });
        return `/scenes/${sceneId}/tiles?${params}`;
      },
    }),

    // Upload video
    uploadVideo: builder.mutation<
      SceneMetadata,
      { file: File; organizationId: string }
    >({
      query: ({ file, organizationId }) => {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('organizationId', organizationId);
        return {
          url: '/scenes/upload',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: [{ type: 'Scene', id: 'LIST' }],
    }),

    // Get scene jobs
    getSceneJobs: builder.query<any[], string>({
      query: (sceneId) => `/scenes/${sceneId}/jobs`,
    }),

    // Update scene
    updateScene: builder.mutation<
      SceneMetadata,
      { sceneId: string; updates: Partial<SceneMetadata> }
    >({
      query: ({ sceneId, updates }) => ({
        url: `/scenes/${sceneId}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Scene', id: sceneId }],
    }),

    // Delete scene
    deleteScene: builder.mutation<void, string>({
      query: (sceneId) => ({
        url: `/scenes/${sceneId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, sceneId) => [
        { type: 'Scene', id: sceneId },
        { type: 'Scene', id: 'LIST' },
      ],
    }),
  }),
});

export const {
  useGetSceneByIdQuery,
  useGetScenesQuery,
  useGetSceneTilesQuery,
  useUploadVideoMutation,
  useUpdateSceneMutation,
  useDeleteSceneMutation,
  useGetSceneJobsQuery,
} = sceneApi;
