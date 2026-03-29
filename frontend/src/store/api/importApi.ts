/**
 * 3D Import API endpoints using RTK Query
 * Handles 3D file import (PLY, LAS, OBJ, GLB, SPLAT, etc.)
 */

import { baseApi } from './baseApi';

type ImportFormatType = 'point_cloud' | 'mesh' | 'gaussian' | 'bim';

type ImportStatus =
  | 'pending'
  | 'uploading'
  | 'validating'
  | 'processing'
  | 'optimizing'
  | 'tiling'
  | 'completed'
  | 'failed';

interface SupportedFormatInfo {
  extension: string;
  format_type: ImportFormatType;
  name: string;
  parser: string;
}

interface SupportedFormatsResponse {
  formats: SupportedFormatInfo[];
  max_file_size_mb: number;
}

interface ImportUploadResponse {
  scene_id: string;
  job_id: string;
  filename: string;
  format: string;
  format_type: ImportFormatType;
  file_size_bytes: number;
  status: ImportStatus;
  message: string;
}

interface ImportStatusResponse {
  scene_id: string;
  job_id: string;
  status: ImportStatus;
  progress_percent: number;
  current_step: string | null;
  message: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export const importApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get list of supported 3D file formats
    getSupportedFormats: builder.query<SupportedFormatsResponse, void>({
      query: () => '/scenes/import/formats',
    }),

    // Upload a 3D file for import
    upload3DFile: builder.mutation<ImportUploadResponse, { file: File; name?: string }>({
      query: ({ file, name }) => {
        const formData = new FormData();
        formData.append('file', file);
        if (name) {
          formData.append('name', name);
        }
        return {
          url: '/scenes/import/upload',
          method: 'POST',
          body: formData,
        };
      },
      invalidatesTags: [{ type: 'Scene', id: 'LIST' }],
    }),

    // Get import job status
    getImportStatus: builder.query<ImportStatusResponse, string>({
      query: (jobId) => `/scenes/import/status/${jobId}`,
    }),

    // Cancel an import and delete the scene
    cancelImport: builder.mutation<{ message: string }, string>({
      query: (sceneId) => ({
        url: `/scenes/import/${sceneId}`,
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
  useGetSupportedFormatsQuery,
  useUpload3DFileMutation,
  useGetImportStatusQuery,
  useCancelImportMutation,
} = importApi;
