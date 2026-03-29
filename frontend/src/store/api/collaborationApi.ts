/**
 * Collaboration API endpoints using RTK Query
 * Handles REST endpoints for collaboration (WebSocket handled separately)
 */

import { baseApi } from './baseApi';

interface ActiveUser {
  user_id: string;
  user_name: string;
  cursor_position?: [number, number, number];
  joined_at: string;
  last_heartbeat: string;
}

interface ActiveUsersResponse {
  scene_id: string;
  active_users: ActiveUser[];
  count: number;
}

export const collaborationApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get list of active users in a scene
    getActiveUsers: builder.query<ActiveUsersResponse, string>({
      query: (sceneId) => `/scenes/${sceneId}/active-users`,
      // Poll every 5 seconds to keep active users list updated
      pollingInterval: 5000,
    }),
  }),
});

export const { useGetActiveUsersQuery } = collaborationApi;
