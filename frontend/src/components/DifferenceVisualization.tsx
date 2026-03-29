/**
 * Difference Visualization Component
 * 
 * Displays geometric differences between two scenes with color-coded overlays:
 * - Red: Removed points
 * - Green: Added points
 * - Yellow: Changed points
 * 
 * Requirements: 32.6, 32.7, 32.10
 */

import React, { useState, useEffect, useCallback } from 'react';
import { SceneComparison } from './SceneComparison';
import { ChangeMetrics } from '../hooks/useSceneComparison';

interface DifferenceVisualizationProps {
  sceneId1: string;
  sceneId2: string;
  onError?: (error: Error) => void;
}

interface DifferenceLayer {
  id: string;
  name: string;
  color: string;
  visible: boolean;
  count: number;
}

export const DifferenceVisualization: React.FC<DifferenceVisualizationProps> = ({
  sceneId1,
  sceneId2,
  onError,
}) => {
  const [metrics, setMetrics] = useState<ChangeMetrics | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [layers, setLayers] = useState<DifferenceLayer[]>([
    { id: 'removed', name: 'Removed', color: '#ff0000', visible: true, count: 0 },
    { id: 'added', name: 'Added', color: '#00ff00', visible: true, count: 0 },
    { id: 'changed', name: 'Changed', color: '#ffff00', visible: true, count: 0 },
  ]);

  // Load difference metrics
  useEffect(() => {
    const loadMetrics = async () => {
      try {
        setIsLoading(true);
        const response = await fetch(`/api/v1/comparison/${sceneId1}/${sceneId2}/metrics`);
        
        if (!response.ok) {
          throw new Error('Failed to load comparison metrics');
        }
        
        const data = await response.json();
        setMetrics(data);
        
        // Update layer counts
        setLayers(prev => prev.map(layer => {
          if (layer.id === 'removed') {
            return { ...layer, count: data.removed_points };
          } else if (layer.id === 'added') {
            return { ...layer, count: data.added_points };
          } else if (layer.id === 'changed') {
            return { ...layer, count: data.changed_points };
          }
          return layer;
        }));
        
        setIsLoading(false);
      } catch (error) {
        if (onError) {
          onError(error as Error);
        }
        setIsLoading(false);
      }
    };
    
    loadMetrics();
  }, [sceneId1, sceneId2, onError]);

  const toggleLayer = useCallback((layerId: string) => {
    setLayers(prev => prev.map(layer => 
      layer.id === layerId ? { ...layer, visible: !layer.visible } : layer
    ));
  }, []);

  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(2)}M`;
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(2)}K`;
    }
    return num.toString();
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      {/* Controls */}
      <div style={{ padding: '15px', background: '#2a2a2a', color: 'white', borderBottom: '1px solid #444' }}>
        <div style={{ marginBottom: '15px' }}>
          <h3 style={{ margin: '0 0 10px 0' }}>Difference Visualization</h3>
          <div style={{ fontSize: '12px', color: '#aaa' }}>
            Color-coded overlay showing changes between scenes
          </div>
        </div>
        
        {/* Change Metrics */}
        {metrics && (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '10px',
            marginBottom: '15px',
            padding: '10px',
            background: '#1a1a1a',
            borderRadius: '4px',
          }}>
            <div>
              <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '4px' }}>Volume Difference</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                {metrics.volumeDifference.toFixed(2)} m³
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '4px' }}>Area Difference</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                {metrics.areaDifference.toFixed(2)} m²
              </div>
            </div>
            <div>
              <div style={{ fontSize: '12px', color: '#aaa', marginBottom: '4px' }}>Point Count Difference</div>
              <div style={{ fontSize: '18px', fontWeight: 'bold' }}>
                {metrics.pointCountDifference > 0 ? '+' : ''}{formatNumber(metrics.pointCountDifference)}
              </div>
            </div>
          </div>
        )}
        
        {/* Layer Controls */}
        <div style={{ marginBottom: '10px' }}>
          <div style={{ fontSize: '14px', fontWeight: 'bold', marginBottom: '8px' }}>
            Difference Layers
          </div>
          <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
            {layers.map(layer => (
              <button
                key={layer.id}
                onClick={() => toggleLayer(layer.id)}
                style={{
                  padding: '8px 12px',
                  background: layer.visible ? layer.color : '#555',
                  color: layer.visible ? '#000' : '#fff',
                  border: 'none',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '12px',
                  fontWeight: 'bold',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px',
                  opacity: layer.visible ? 1 : 0.5,
                  transition: 'all 0.2s',
                }}
              >
                <span style={{
                  width: '12px',
                  height: '12px',
                  borderRadius: '50%',
                  background: layer.color,
                  border: '2px solid #fff',
                }}></span>
                {layer.name}
                <span style={{
                  marginLeft: '4px',
                  padding: '2px 6px',
                  background: 'rgba(0,0,0,0.3)',
                  borderRadius: '10px',
                  fontSize: '10px',
                }}>
                  {formatNumber(layer.count)}
                </span>
              </button>
            ))}
          </div>
        </div>
        
        {/* Legend */}
        <div style={{ 
          fontSize: '11px', 
          color: '#aaa',
          padding: '8px',
          background: '#1a1a1a',
          borderRadius: '4px',
        }}>
          <div style={{ marginBottom: '4px', fontWeight: 'bold' }}>Legend:</div>
          <div style={{ display: 'flex', gap: '15px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#ff0000' }}>●</span> Removed (in Scene 1, not in Scene 2)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#00ff00' }}>●</span> Added (in Scene 2, not in Scene 1)
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <span style={{ color: '#ffff00' }}>●</span> Changed (position or properties modified)
            </div>
          </div>
        </div>
      </div>
      
      {/* Scene Comparison Viewer */}
      <div style={{ flex: 1 }}>
        {isLoading ? (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: 'white',
          }}>
            Loading difference visualization...
          </div>
        ) : (
          <SceneComparison
            sceneId1={sceneId1}
            sceneId2={sceneId2}
            mode="difference"
            onError={onError}
            onMetricsCalculated={setMetrics}
          />
        )}
      </div>
    </div>
  );
};

export default DifferenceVisualization;
