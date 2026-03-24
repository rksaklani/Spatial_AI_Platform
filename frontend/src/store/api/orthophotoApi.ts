/**
 * Orthophoto API endpoints using RTK Query
 * Requirements: 17.2
 */

import { baseApi } from './baseApi';

interface Orthophoto {
  id: string;
  scene_id: string;
  filename: string;
  width: number;
  height: number;
  bounds: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
  };
  resolution: number;
  coordinate_system: string;
  tile_url_template: string;
  created_at: string;
}

export const orthophotoApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get orthophoto for scene
    getOrthophoto: builder.query<Orthophoto, string>({
      query: (sceneId) => `/scenes/${sceneId}/orthophoto`,
      providesTags: (_result, _error, sceneId) => [{ type: 'Orthophoto', id: sceneId }],
    }),

    // Upload orthophoto
    uploadOrthophoto: builder.mutation<Orthophoto, { sceneId: string; file: File }>({
      query: ({ sceneId, file }) => {
        const formData = new FormData();
        formData.append('orthophoto', file);
        return {
          url: `/scenes/${sceneId}/orthophoto`,
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Orthophoto', id: sceneId }],
    }),

    // Delete orthophoto
    deleteOrthophoto: builder.mutation<void, string>({
      query: (sceneId) => ({
        url: `/scenes/${sceneId}/orthophoto`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, sceneId) => [{ type: 'Orthophoto', id: sceneId }],
    }),
  }),
});

export const {
  useGetOrthophotoQuery,
  useUploadOrthophotoMutation,
  useDeleteOrthophotoMutation,
} = orthophotoApi;
