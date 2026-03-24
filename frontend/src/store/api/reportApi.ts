/**
 * Report API endpoints using RTK Query
 * Requirements: 16.1, 16.4
 */

import { baseApi } from './baseApi';

interface ReportRequest {
  include_metadata: boolean;
  include_annotations: boolean;
  include_photos: boolean;
  include_measurements: boolean;
}

interface Report {
  id: string;
  scene_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  download_url: string | null;
  created_at: string;
  completed_at: string | null;
}

export const reportApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Generate report
    generateReport: builder.mutation<Report, { sceneId: string; options: ReportRequest }>({
      query: ({ sceneId, options }) => ({
        url: `/scenes/${sceneId}/reports`,
        method: 'POST',
        body: options,
      }),
    }),

    // Get report status
    getReportStatus: builder.query<Report, { sceneId: string; reportId: string }>({
      query: ({ sceneId, reportId }) => `/scenes/${sceneId}/reports/${reportId}`,
      providesTags: (_result, _error, { reportId }) => [{ type: 'Report', id: reportId }],
    }),

    // Download report
    downloadReport: builder.query<Blob, { sceneId: string; reportId: string }>({
      query: ({ sceneId, reportId }) => ({
        url: `/scenes/${sceneId}/reports/${reportId}/download`,
        responseHandler: (response: Response) => response.blob(),
      }),
    }),
  }),
});

export const {
  useGenerateReportMutation,
  useGetReportStatusQuery,
  useLazyDownloadReportQuery,
} = reportApi;
