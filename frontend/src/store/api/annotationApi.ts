/**
 * Annotation API endpoints using RTK Query
 */

import { baseApi } from './baseApi';

interface Annotation {
  id: string;
  sceneId: string;
  userId: string;
  type: 'comment' | 'measurement' | 'marker';
  position: [number, number, number];
  content: string;
  metadata?: {
    distance?: number;
    area?: number;
    points?: Array<[number, number, number]>;
    color?: string;
  };
  createdAt: string;
  updatedAt: string;
}

export const annotationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get annotations for a scene
    getAnnotations: builder.query<Annotation[], string>({
      query: (sceneId) => `/scenes/${sceneId}/annotations`,
      providesTags: (result, _error, sceneId) =>
        result
          ? [
              ...result.map(({ id }) => ({ type: 'Annotation' as const, id })),
              { type: 'Annotation', id: sceneId },
            ]
          : [{ type: 'Annotation', id: sceneId }],
    }),

    // Create annotation
    createAnnotation: builder.mutation<
      Annotation,
      Omit<Annotation, 'id' | 'userId' | 'createdAt' | 'updatedAt'>
    >({
      query: (annotation) => ({
        url: `/scenes/${annotation.sceneId}/annotations`,
        method: 'POST',
        body: annotation,
      }),
      invalidatesTags: (_result, _error, annotation) => [
        { type: 'Annotation', id: annotation.sceneId },
      ],
    }),

    // Update annotation
    updateAnnotation: builder.mutation<
      Annotation,
      { id: string; sceneId: string; updates: Partial<Annotation> }
    >({
      query: ({ id, sceneId, updates }) => ({
        url: `/scenes/${sceneId}/annotations/${id}`,
        method: 'PATCH',
        body: updates,
      }),
      invalidatesTags: (_result, _error, { id, sceneId }) => [
        { type: 'Annotation', id },
        { type: 'Annotation', id: sceneId },
      ],
    }),

    // Delete annotation
    deleteAnnotation: builder.mutation<void, { id: string; sceneId: string }>({
      query: ({ id, sceneId }) => ({
        url: `/scenes/${sceneId}/annotations/${id}`,
        method: 'DELETE',
      }),
      invalidatesTags: (_result, _error, { id, sceneId }) => [
        { type: 'Annotation', id },
        { type: 'Annotation', id: sceneId },
      ],
    }),
  }),
});

export const {
  useGetAnnotationsQuery,
  useCreateAnnotationMutation,
  useUpdateAnnotationMutation,
  useDeleteAnnotationMutation,
} = annotationApi;
