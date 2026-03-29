/**
 * Tiles API endpoints using RTK Query
 * Handles scene tile streaming with frustum culling and LOD selection
 */

import { baseApi } from './baseApi';

interface CameraParams {
  position: [number, number, number];
  direction: [number, number, number];
  fov: number;
  near: number;
  far: number;
}

interface TileRequest {
  camera: CameraParams;
  bandwidth_mbps?: number;
  max_tiles?: number;
}

interface TileResponse {
  tile_id: string;
  level: number;
  x: number;
  y: number;
  z: number;
  lod: string;
  priority: number;
  distance: number;
  file_path: string;
  file_size_bytes: number;
  gaussian_count: number;
  bounding_box: {
    min_x: number;
    max_x: number;
    min_y: number;
    max_y: number;
    min_z: number;
    max_z: number;
  };
}

interface TileListResponse {
  tiles: TileResponse[];
  total_tiles: number;
  selected_lod: string;
  bandwidth_adjusted: boolean;
}

export const tilesApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Get prioritized tiles for a scene based on camera parameters
    getSceneTiles: builder.mutation<TileListResponse, { sceneId: string; request: TileRequest }>({
      query: ({ sceneId, request }) => ({
        url: `/scenes/${sceneId}/tiles`,
        method: 'POST',
        body: request,
      }),
    }),

    // Download a specific tile file
    downloadTile: builder.query<Blob, { sceneId: string; tileId: string }>({
      query: ({ sceneId, tileId }) => ({
        url: `/scenes/${sceneId}/tiles/${tileId}`,
        responseHandler: (response) => response.blob(),
      }),
    }),
  }),
});

export const { useGetSceneTilesMutation, useDownloadTileQuery } = tilesApi;
