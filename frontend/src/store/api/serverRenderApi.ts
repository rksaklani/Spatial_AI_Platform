/**
 * Server-Side Rendering API endpoints using RTK Query
 * Handles device capability detection and server-side rendering sessions
 */

import { baseApi } from './baseApi';

interface DeviceCapabilityRequest {
  user_agent: string;
  webgl2: boolean;
  webgpu: boolean;
  gpu_vendor?: string;
  gpu_renderer?: string;
  max_texture_size: number;
}

interface DeviceCapabilityResponse {
  has_webgl2: boolean;
  has_webgpu: boolean;
  estimated_performance: string;
  is_sufficient: boolean;
  recommendation: 'client-side' | 'server-side';
}

interface CreateSessionRequest {
  scene_id: string;
  resolution_width?: number;
  resolution_height?: number;
}

interface CreateSessionResponse {
  session_id: string;
  websocket_url: string;
}

interface UpdateCameraRequest {
  position: [number, number, number];
  target: [number, number, number];
  fov?: number;
}

interface RenderStatsResponse {
  active_sessions: number;
  total_sessions: number;
  max_sessions: number;
  total_frames_rendered: number;
  avg_render_time_ms: number;
  avg_fps: number;
}

export const serverRenderApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Detect device capability and get rendering recommendation
    detectDeviceCapability: builder.mutation<DeviceCapabilityResponse, DeviceCapabilityRequest>({
      query: (request) => ({
        url: '/render/detect-capability',
        method: 'POST',
        body: request,
      }),
    }),

    // Create a new server-side rendering session
    createRenderSession: builder.mutation<CreateSessionResponse, CreateSessionRequest>({
      query: (request) => ({
        url: '/render/sessions',
        method: 'POST',
        body: request,
      }),
    }),

    // Update camera parameters for a rendering session
    updateSessionCamera: builder.mutation<
      { status: string },
      { sessionId: string; camera: UpdateCameraRequest }
    >({
      query: ({ sessionId, camera }) => ({
        url: `/render/sessions/${sessionId}/camera`,
        method: 'POST',
        body: camera,
      }),
    }),

    // Close a rendering session
    closeRenderSession: builder.mutation<{ status: string }, string>({
      query: (sessionId) => ({
        url: `/render/sessions/${sessionId}`,
        method: 'DELETE',
      }),
    }),

    // Get a single rendered frame (polling-based alternative to WebSocket)
    getRenderedFrame: builder.query<Blob, string>({
      query: (sessionId) => ({
        url: `/render/sessions/${sessionId}/frame`,
        responseHandler: (response) => response.blob(),
      }),
    }),

    // Get server rendering statistics
    getRenderStats: builder.query<RenderStatsResponse, void>({
      query: () => '/render/stats',
    }),
  }),
});

export const {
  useDetectDeviceCapabilityMutation,
  useCreateRenderSessionMutation,
  useUpdateSessionCameraMutation,
  useCloseRenderSessionMutation,
  useGetRenderedFrameQuery,
  useGetRenderStatsQuery,
} = serverRenderApi;
