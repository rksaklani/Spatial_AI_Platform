/**
 * Geospatial API endpoints using RTK Query
 * Handles coordinate management, georeferencing, and transformations
 */

import { baseApi } from './baseApi';

interface GeospatialCoordinates {
  latitude: number;
  longitude: number;
  altitude?: number;
}

interface ProjectedCoordinates {
  x: number;
  y: number;
  z?: number;
  epsg_code?: number;
  proj_string?: string;
}

interface GroundControlPoint {
  id?: string;
  name: string;
  scene_coordinates: [number, number, number];
  geospatial_coordinates: GeospatialCoordinates;
  accuracy?: number;
  created_at?: string;
}

interface SceneGeoreferencing {
  scene_id: string;
  is_georeferenced: boolean;
  origin_coordinates?: GeospatialCoordinates;
  coordinate_system?: string;
  epsg_code?: number;
  wkt?: string;
  ground_control_points: GroundControlPoint[];
  created_at?: string;
  updated_at?: string;
}

interface PointCoordinatesCreate {
  scene_id: string;
  point_id: string;
  point_type: string;
  scene_coordinates: [number, number, number];
  geospatial_coordinates?: GeospatialCoordinates;
  projected_coordinates?: ProjectedCoordinates;
}

interface PointCoordinatesUpdate {
  scene_coordinates?: [number, number, number];
  geospatial_coordinates?: GeospatialCoordinates;
  projected_coordinates?: ProjectedCoordinates;
}

interface PointCoordinatesResponse {
  id: string;
  scene_id: string;
  point_id: string;
  point_type: string;
  scene_coordinates: [number, number, number];
  geospatial_coordinates?: GeospatialCoordinates;
  projected_coordinates?: ProjectedCoordinates;
  created_at: string;
  updated_at: string;
}

interface CoordinateTransformRequest {
  source_coordinates: GeospatialCoordinates | ProjectedCoordinates;
  target_system: string;
  target_epsg_code?: number;
  target_proj_string?: string;
}

interface CoordinateTransformResponse {
  source_coordinates: GeospatialCoordinates | ProjectedCoordinates;
  target_coordinates: GeospatialCoordinates | ProjectedCoordinates;
  accuracy_meters?: number;
}

interface DistanceResponse {
  distance_meters: number;
  distance_kilometers: number;
  distance_miles: number;
}

interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: number[];
  };
  properties: Record<string, any>;
}

interface GeoJSONFeatureCollection {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
  crs?: any;
}

export const geospatialApi = baseApi.injectEndpoints({
  endpoints: (builder) => ({
    // Set or update georeferencing for a scene
    setSceneGeoreferencing: builder.mutation<
      SceneGeoreferencing,
      { sceneId: string; georeferencing: Partial<SceneGeoreferencing> }
    >({
      query: ({ sceneId, georeferencing }) => ({
        url: `/geospatial/scenes/${sceneId}/georeferencing`,
        method: 'POST',
        body: georeferencing,
      }),
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Scene', id: sceneId }],
    }),

    // Get georeferencing information for a scene
    getSceneGeoreferencing: builder.query<SceneGeoreferencing | null, string>({
      query: (sceneId) => `/geospatial/scenes/${sceneId}/georeferencing`,
      providesTags: (_result, _error, sceneId) => [{ type: 'Scene', id: sceneId }],
    }),

    // Add a ground control point to a scene
    addGroundControlPoint: builder.mutation<
      GroundControlPoint,
      { sceneId: string; gcp: GroundControlPoint }
    >({
      query: ({ sceneId, gcp }) => ({
        url: `/geospatial/scenes/${sceneId}/ground-control-points`,
        method: 'POST',
        body: gcp,
      }),
      invalidatesTags: (_result, _error, { sceneId }) => [{ type: 'Scene', id: sceneId }],
    }),

    // Create point coordinates
    createPointCoordinates: builder.mutation<PointCoordinatesResponse, PointCoordinatesCreate>({
      query: (pointCoords) => ({
        url: '/geospatial/points',
        method: 'POST',
        body: pointCoords,
      }),
    }),

    // Get point coordinates by ID
    getPointCoordinates: builder.query<PointCoordinatesResponse, string>({
      query: (pointId) => `/geospatial/points/${pointId}`,
    }),

    // Get all point coordinates for a scene
    getScenePointCoordinates: builder.query<
      PointCoordinatesResponse[],
      { sceneId: string; pointType?: string }
    >({
      query: ({ sceneId, pointType }) => {
        const params = new URLSearchParams();
        if (pointType) params.append('point_type', pointType);
        return `/geospatial/scenes/${sceneId}/points?${params}`;
      },
    }),

    // Update point coordinates
    updatePointCoordinates: builder.mutation<
      PointCoordinatesResponse,
      { pointId: string; update: PointCoordinatesUpdate }
    >({
      query: ({ pointId, update }) => ({
        url: `/geospatial/points/${pointId}`,
        method: 'PUT',
        body: update,
      }),
    }),

    // Delete point coordinates
    deletePointCoordinates: builder.mutation<void, string>({
      query: (pointId) => ({
        url: `/geospatial/points/${pointId}`,
        method: 'DELETE',
      }),
    }),

    // Transform coordinates between systems
    transformCoordinates: builder.mutation<CoordinateTransformResponse, CoordinateTransformRequest>(
      {
        query: (request) => ({
          url: '/geospatial/transform',
          method: 'POST',
          body: request,
        }),
      }
    ),

    // Calculate distance between two coordinates
    calculateDistance: builder.mutation<
      DistanceResponse,
      { coord1: GeospatialCoordinates; coord2: GeospatialCoordinates }
    >({
      query: ({ coord1, coord2 }) => ({
        url: '/geospatial/distance',
        method: 'POST',
        body: { coord1, coord2 },
      }),
    }),

    // Export scene as GeoJSON
    exportSceneGeoJSON: builder.query<
      GeoJSONFeatureCollection,
      { sceneId: string; includeAnnotations?: boolean; includePoints?: boolean }
    >({
      query: ({ sceneId, includeAnnotations = true, includePoints = true }) => {
        const params = new URLSearchParams({
          include_annotations: includeAnnotations.toString(),
          include_points: includePoints.toString(),
        });
        return `/geospatial/scenes/${sceneId}/export/geojson?${params}`;
      },
    }),
  }),
});

export const {
  useSetSceneGeoreferencingMutation,
  useGetSceneGeoreferencingQuery,
  useAddGroundControlPointMutation,
  useCreatePointCoordinatesMutation,
  useGetPointCoordinatesQuery,
  useGetScenePointCoordinatesQuery,
  useUpdatePointCoordinatesMutation,
  useDeletePointCoordinatesMutation,
  useTransformCoordinatesMutation,
  useCalculateDistanceMutation,
  useExportSceneGeoJSONQuery,
} = geospatialApi;
