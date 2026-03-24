/**
 * Photo API endpoints using RTK Query
 * Requirements: 13.1, 14.6
 */

import { baseApi } from './baseApi';

interface Photo {
  id: string;
  scene_id: string;
  filename: string;
  width: number;
  height: number;
  file_size: number;
  capture_time: string | null;
  gps_latitude: number | null;
  gps_longitude: number | null;
  gps_altitude: number | null;
  camera_make: string | null;
  camera_model: string | null;
  focal_length: number | null;
  iso: number | null;
  shutter_speed: string | null;
  aperture: string | null;
  aligned: boolean;
  alignment_confidence: number | null;
  position: [number, number, number] | null;
  rotation: [number, number, number, number] | null;
  created_at: string;
}

interface PhotoMarker {
  photo_id: string;
  position: [number, number, number];
  thumbnail_url: string;
}

interface AlignPhotoRequest {
  position: [number, number, number];
  rotation: [number, number, number, number];
}

export const photoApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get all photos for a scene
    getPhotos: builder.query<Photo[], string>({
      query: (sceneId) => `/scenes/${sceneId}/photos`,
      providesTags: (result, _error, sceneId) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Photo' as const, id })),
              { type: 'Photo', id: sceneId },
            ]
          : [{ type: 'Photo', id: sceneId }],
    }),

    // Get specific photo
    getPhoto: builder.query<Photo, { sceneId: string; photoId: string }>({
      query: ({ sceneId, photoId }) => `/scenes/${sceneId}/photos/${photoId}`,
      providesTags: (_result, _error, { photoId }) => [{ type: 'Photo', id: photoId }],
    }),

    // Upload photo
    uploadPhoto: builder.mutation<Photo, { sceneId: string; file: File }>({
      query: ({ sceneId, file }) => {
        const formData = new FormData();
        formData.append('photo', file);
        return {
          url: `/scenes/${sceneId}/photos`,
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Photo', id: sceneId }],
    }),

    // Align photo
    alignPhoto: builder.mutation<
      Photo,
      { sceneId: string; photoId: string; alignment: AlignPhotoRequest }
    >({
      query: ({ sceneId, photoId, alignment }) => ({
        url: `/scenes/${sceneId}/photos/${photoId}/align`,
        method: 'POST',
        body: alignment,
      }),
      invalidatesTags: (_result, _error, { photoId, sceneId }) => [
        { type: 'Photo', id: photoId },
        { type: 'Photo', id: sceneId },
      ],
    }),

    // Get photo markers for scene
    getPhotoMarkers: builder.query<PhotoMarker[], string>({
      query: (sceneId) => `/scenes/${sceneId}/photos/markers`,
      providesTags: (_result, _error, sceneId) => [{ type: 'Photo', id: `${sceneId}-markers` }],
    }),
  }),
});

export const {
  useGetPhotosQuery,
  useGetPhotoQuery,
  useUploadPhotoMutation,
  useAlignPhotoMutation,
  useGetPhotoMarkersQuery,
} = photoApi;
