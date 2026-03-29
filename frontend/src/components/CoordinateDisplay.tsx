/**
 * Coordinate Display Component
 * 
 * Displays GPS coordinates for clicked points in the 3D scene.
 * Allows user selection of display coordinate system.
 * Shows coordinate grid overlay when enabled.
 */

import React, { useState, useEffect } from 'react';
import * as THREE from 'three';

interface GeospatialCoordinates {
  latitude: number;
  longitude: number;
  altitude?: number;
}

interface ProjectedCoordinates {
  x: number;
  y: number;
  z?: number;
  coordinate_system: string;
  epsg_code?: number;
}

interface CoordinateDisplayProps {
  sceneId: string;
  clickedPosition?: THREE.Vector3;
  showGrid?: boolean;
  onCoordinateSystemChange?: (system: string) => void;
}

type CoordinateSystem = 'WGS84' | 'UTM' | 'STATE_PLANE' | 'CUSTOM';

const CoordinateDisplay: React.FC<CoordinateDisplayProps> = ({
  sceneId,
  clickedPosition,
  showGrid = false,
  onCoordinateSystemChange,
}) => {
  const [selectedSystem, setSelectedSystem] = useState<CoordinateSystem>('WGS84');
  const [coordinates, setCoordinates] = useState<GeospatialCoordinates | ProjectedCoordinates | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch coordinates for clicked position
  useEffect(() => {
    if (!clickedPosition) {
      setCoordinates(null);
      return;
    }

    const fetchCoordinates = async () => {
      setLoading(true);
      setError(null);

      try {
        // Get scene georeferencing
        const geoResponse = await fetch(
          `/api/v1/geospatial/scenes/${sceneId}/georeferencing`,
          {
            headers: {
              'Authorization': `Bearer ${localStorage.getItem('token')}`,
            },
          }
        );

        if (!geoResponse.ok) {
          throw new Error('Failed to fetch georeferencing');
        }

        const georeferencing = await geoResponse.json();

        if (!georeferencing || !georeferencing.is_georeferenced) {
          setError('Scene is not georeferenced');
          setLoading(false);
          return;
        }

        // Transform scene coordinates to geospatial coordinates
        // This is a simplified version - in production, you'd use the transformation matrix
        // and call the transformation API
        
        // For now, display scene coordinates
        const sceneCoords: ProjectedCoordinates = {
          x: clickedPosition.x,
          y: clickedPosition.y,
          z: clickedPosition.z,
          coordinate_system: 'SCENE',
        };

        setCoordinates(sceneCoords);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchCoordinates();
  }, [clickedPosition, sceneId, selectedSystem]);

  const handleSystemChange = (system: CoordinateSystem) => {
    setSelectedSystem(system);
    if (onCoordinateSystemChange) {
      onCoordinateSystemChange(system);
    }
  };

  const formatCoordinates = () => {
    if (!coordinates) return null;

    if ('latitude' in coordinates) {
      // WGS84 format
      return (
        <div className="coordinate-values">
          <div className="coordinate-row">
            <span className="label">Latitude:</span>
            <span className="value">{coordinates.latitude.toFixed(8)}°</span>
          </div>
          <div className="coordinate-row">
            <span className="label">Longitude:</span>
            <span className="value">{coordinates.longitude.toFixed(8)}°</span>
          </div>
          {coordinates.altitude !== undefined && (
            <div className="coordinate-row">
              <span className="label">Altitude:</span>
              <span className="value">{coordinates.altitude.toFixed(2)} m</span>
            </div>
          )}
        </div>
      );
    } else {
      // Projected format
      return (
        <div className="coordinate-values">
          <div className="coordinate-row">
            <span className="label">X (Easting):</span>
            <span className="value">{coordinates.x.toFixed(3)} m</span>
          </div>
          <div className="coordinate-row">
            <span className="label">Y (Northing):</span>
            <span className="value">{coordinates.y.toFixed(3)} m</span>
          </div>
          {coordinates.z !== undefined && (
            <div className="coordinate-row">
              <span className="label">Z (Elevation):</span>
              <span className="value">{coordinates.z.toFixed(3)} m</span>
            </div>
          )}
          {coordinates.epsg_code && (
            <div className="coordinate-row">
              <span className="label">EPSG:</span>
              <span className="value">{coordinates.epsg_code}</span>
            </div>
          )}
        </div>
      );
    }
  };

  return (
    <div className="coordinate-display">
      <div className="coordinate-header">
        <h3>Coordinates</h3>
        <select
          value={selectedSystem}
          onChange={(e) => handleSystemChange(e.target.value as CoordinateSystem)}
          className="coordinate-system-selector"
        >
          <option value="WGS84">WGS84 (GPS)</option>
          <option value="UTM">UTM</option>
          <option value="STATE_PLANE">State Plane</option>
          <option value="CUSTOM">Custom</option>
        </select>
      </div>

      {loading && <div className="loading">Loading coordinates...</div>}
      
      {error && <div className="error">{error}</div>}
      
      {!loading && !error && coordinates && formatCoordinates()}
      
      {!loading && !error && !coordinates && (
        <div className="no-coordinates">
          Click on the scene to display coordinates
        </div>
      )}

      {showGrid && (
        <div className="grid-controls">
          <label>
            <input type="checkbox" defaultChecked />
            Show Coordinate Grid
          </label>
        </div>
      )}

      <style jsx>{`
        .coordinate-display {
          position: absolute;
          top: 20px;
          right: 20px;
          background: rgba(255, 255, 255, 0.95);
          border-radius: 8px;
          padding: 16px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
          min-width: 280px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
        }

        .coordinate-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 12px;
        }

        .coordinate-header h3 {
          margin: 0;
          font-size: 16px;
          font-weight: 600;
          color: #333;
        }

        .coordinate-system-selector {
          padding: 4px 8px;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 13px;
          background: white;
          cursor: pointer;
        }

        .coordinate-values {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .coordinate-row {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 6px 0;
          border-bottom: 1px solid #f0f0f0;
        }

        .coordinate-row:last-child {
          border-bottom: none;
        }

        .label {
          font-size: 13px;
          color: #666;
          font-weight: 500;
        }

        .value {
          font-size: 13px;
          color: #333;
          font-family: 'Monaco', 'Courier New', monospace;
        }

        .loading,
        .error,
        .no-coordinates {
          padding: 12px;
          text-align: center;
          font-size: 13px;
          color: #666;
        }

        .error {
          color: #d32f2f;
          background: #ffebee;
          border-radius: 4px;
        }

        .grid-controls {
          margin-top: 12px;
          padding-top: 12px;
          border-top: 1px solid #e0e0e0;
        }

        .grid-controls label {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 13px;
          color: #666;
          cursor: pointer;
        }

        .grid-controls input[type="checkbox"] {
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

export default CoordinateDisplay;
