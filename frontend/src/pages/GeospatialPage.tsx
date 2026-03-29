import { useState } from 'react';
import { useGetScenesQuery } from '../store/api/sceneApi';
import {
  useGetSceneGeoreferencingQuery,
  useTransformCoordinatesMutation,
} from '../store/api/geospatialApi';
import { Button } from '../components/common/Button';
import { MapIcon, ArrowsRightLeftIcon } from '@heroicons/react/24/outline';

export function GeospatialPage() {
  const [selectedSceneId, setSelectedSceneId] = useState<string>('');
  const [lat, setLat] = useState('');
  const [lon, setLon] = useState('');
  const [targetSystem, setTargetSystem] = useState('EPSG:3857');
  
  const { data: scenes = [] } = useGetScenesQuery();
  const { data: georeferencing } = useGetSceneGeoreferencingQuery(selectedSceneId, {
    skip: !selectedSceneId,
  });
  const [transformCoordinates, { data: transformResult, isLoading: isTransforming }] =
    useTransformCoordinatesMutation();

  const handleTransform = async () => {
    if (!lat || !lon) return;
    
    try {
      await transformCoordinates({
        source_coordinates: {
          latitude: parseFloat(lat),
          longitude: parseFloat(lon),
        },
        target_system: targetSystem,
      }).unwrap();
    } catch (error) {
      console.error('Transform failed:', error);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Geospatial Tools</h1>
        <p className="text-text-secondary">
          Coordinate transformation, georeferencing, and GeoJSON export
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Scene Georeferencing */}
        <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <MapIcon className="w-6 h-6 text-accent-primary" />
            <h2 className="text-xl font-bold text-text-primary">Scene Georeferencing</h2>
          </div>

          <div className="mb-4">
            <label className="block text-sm font-medium text-text-primary mb-2">
              Select Scene
            </label>
            <select
              value={selectedSceneId}
              onChange={(e) => setSelectedSceneId(e.target.value)}
              className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">Choose a scene...</option>
              {scenes.map((scene) => (
                <option key={scene.sceneId} value={scene.sceneId}>
                  {scene.name}
                </option>
              ))}
            </select>
          </div>

          {selectedSceneId && georeferencing && (
            <div className="space-y-3">
              <div className="p-4 bg-primary-bg rounded-lg">
                <p className="text-sm text-text-muted mb-1">Status</p>
                <p className="text-text-primary font-medium">
                  {georeferencing.is_georeferenced ? '✓ Georeferenced' : '✗ Not Georeferenced'}
                </p>
              </div>

              {georeferencing.origin_coordinates && (
                <div className="p-4 bg-primary-bg rounded-lg">
                  <p className="text-sm text-text-muted mb-1">Origin Coordinates</p>
                  <p className="text-text-primary font-mono text-sm">
                    {georeferencing.origin_coordinates.latitude.toFixed(6)},{' '}
                    {georeferencing.origin_coordinates.longitude.toFixed(6)}
                  </p>
                </div>
              )}

              {georeferencing.coordinate_system && (
                <div className="p-4 bg-primary-bg rounded-lg">
                  <p className="text-sm text-text-muted mb-1">Coordinate System</p>
                  <p className="text-text-primary font-medium">
                    {georeferencing.coordinate_system}
                  </p>
                </div>
              )}

              <div className="p-4 bg-primary-bg rounded-lg">
                <p className="text-sm text-text-muted mb-1">Ground Control Points</p>
                <p className="text-text-primary font-medium">
                  {georeferencing.ground_control_points.length} points
                </p>
              </div>
            </div>
          )}

          {selectedSceneId && !georeferencing && (
            <div className="text-center py-8">
              <p className="text-text-secondary">No georeferencing data available</p>
            </div>
          )}
        </div>

        {/* Coordinate Transformation */}
        <div className="bg-secondary-bg border border-border-color rounded-xl p-6">
          <div className="flex items-center gap-3 mb-4">
            <ArrowsRightLeftIcon className="w-6 h-6 text-accent-primary" />
            <h2 className="text-xl font-bold text-text-primary">Coordinate Transform</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Latitude
              </label>
              <input
                type="number"
                step="any"
                value={lat}
                onChange={(e) => setLat(e.target.value)}
                placeholder="40.7128"
                className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Longitude
              </label>
              <input
                type="number"
                step="any"
                value={lon}
                onChange={(e) => setLon(e.target.value)}
                placeholder="-74.0060"
                className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Target System
              </label>
              <select
                value={targetSystem}
                onChange={(e) => setTargetSystem(e.target.value)}
                className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
              >
                <option value="EPSG:3857">Web Mercator (EPSG:3857)</option>
                <option value="EPSG:4326">WGS 84 (EPSG:4326)</option>
                <option value="EPSG:32633">UTM Zone 33N (EPSG:32633)</option>
              </select>
            </div>

            <Button
              variant="primary"
              onClick={handleTransform}
              disabled={!lat || !lon || isTransforming}
              icon={<ArrowsRightLeftIcon className="w-5 h-5" />}
              className="w-full"
            >
              {isTransforming ? 'Transforming...' : 'Transform'}
            </Button>

            {transformResult && (
              <div className="p-4 bg-primary-bg rounded-lg">
                <p className="text-sm text-text-muted mb-2">Result</p>
                <pre className="text-text-primary font-mono text-sm overflow-x-auto">
                  {JSON.stringify(transformResult.target_coordinates, null, 2)}
                </pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
