/**
 * Guided Tour API endpoints using RTK Query
 * Requirements: 11.4
 */

import { baseApi } from './baseApi';

interface CameraKeyframe {
  position: [number, number, number];
  rotation: [number, number, number, number];
  timestamp: number;
}

interface Narration {
  timestamp: number;
  text: string;
}

interface GuidedTour {
  id: string;
  scene_id: string;
  user_id: string;
  name: string;
  camera_path: CameraKeyframe[];
  narration: Narration[];
  duration: number;
  created_at: string;
}

interface CreateTourRequest {
  name: string;
  camera_path: CameraKeyframe[];
  narration: Narration[];
}

export const tourApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get all tours for a scene
    getTours: builder.query<GuidedTour[], string>({
      query: (sceneId) => `/scenes/${sceneId}/tours`,
      providesTags: (result, _error, sceneId) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Tour' as const, id })),
              { type: 'Tour', id: sceneId },
            ]
          : [{ type: 'Tour', id: sceneId }],
    }),

    // Get specific tour
    getTour: builder.query<GuidedTour, { sceneId: string; tourId: string }>({
      query: ({ sceneId, tourId }) => `/scenes/${sceneId}/tours/${tourId}`,
      providesTags: (_result, _error, { tourId }) => [{ type: 'Tour', id: tourId }],
    }),

    // Create tour
    createTour: builder.mutation<GuidedTour, { sceneId: string; tour: CreateTourRequest }>({
      query: ({ sceneId, tour }) => ({
        url: `/scenes/${sceneId}/tours`,
        method: 'POST',
        body: tour,
      }),
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Tour', id: sceneId }],
    }),

    // Update tour
    updateTour: builder.mutation<
      GuidedTour,
      { sceneId: string; tourId: string; updates: Partial<CreateTourRequest> }
    >({
      query: ({ sceneId, tourId, updates }) => ({
        url: `/scenes/${sceneId}/tours/${tourId}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_result, _error, { tourId, sceneId }) => [
        { type: 'Tour', id: tourId },
        { type: 'Tour', id: sceneId },
      ],
    }),

    // Delete tour
    deleteTour: builder.mutation<void, { sceneId: string; tourId: string }>({
      query: ({ sceneId, tourId }) => ({
        url: `/scenes/${sceneId}/tours/${tourId}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, { tourId, sceneId }) => [
        { type: 'Tour', id: tourId },
        { type: 'Tour', id: sceneId },
      ],
    }),
  }),
});

export const {
  useGetToursQuery,
  useGetTourQuery,
  useCreateTourMutation,
  useUpdateTourMutation,
  useDeleteTourMutation,
} = tourApi;
