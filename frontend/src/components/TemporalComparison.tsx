/**
 * Temporal Comparison Component
 * 
 * Implements before/after visualization with opacity blending
 * 
 * Requirements: 32.4, 32.5
 */

import React, { useState, useCallback } from 'react';
import { SceneComparison } from './SceneComparison';

interface TemporalComparisonProps {
  beforeSceneId: string;
  afterSceneId: string;
  onError?: (error: Error) => void;
}

export const TemporalComparison: React.FC<TemporalComparisonProps> = ({
  beforeSceneId,
  afterSceneId,
  onError,
}) => {
  const [opacity, setOpacity] = useState(0.5);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackSpeed, setPlaybackSpeed] = useState(1);

  // Animate opacity for before/after transition
  const handlePlayPause = useCallback(() => {
    if (isPlaying) {
      setIsPlaying(false);
    } else {
      setIsPlaying(true);
      
      // Animate opacity from 0 to 1 and back
      const duration = 3000 / playbackSpeed; // 3 seconds per cycle
      const startTime = Date.now();
      const startOpacity = opacity;
      
      const animate = () => {
        const elapsed = Date.now() - startTime;
        const progress = (elapsed % duration) / duration;
        
        // Ping-pong between 0 and 1
        const newOpacity = progress < 0.5 
          ? progress * 2 
          : 2 - (progress * 2);
        
        setOpacity(newOpacity);
        
        if (isPlaying) {
          requestAnimationFrame(animate);
        }
      };
      
      animate();
    }
  }, [isPlaying, opacity, playbackSpeed]);

  const handleOpacityChange = useCallback((value: number) => {
    setOpacity(value);
    setIsPlaying(false);
  }, []);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%', width: '100%' }}>
      {/* Controls */}
      <div style={{ padding: '15px', background: '#2a2a2a', color: 'white', borderBottom: '1px solid #444' }}>
        <div style={{ marginBottom: '15px' }}>
          <h3 style={{ margin: '0 0 10px 0' }}>Temporal Comparison (Before/After)</h3>
          <div style={{ fontSize: '12px', color: '#aaa' }}>
            Compare scenes over time with opacity blending
          </div>
        </div>
        
        {/* Opacity Slider */}
        <div style={{ marginBottom: '15px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
            <label style={{ fontSize: '14px' }}>
              Opacity: {opacity.toFixed(2)}
            </label>
            <div style={{ fontSize: '12px', color: '#aaa' }}>
              <span style={{ marginRight: '10px' }}>Before (0)</span>
              <span>After (1)</span>
            </div>
          </div>
          <input
            type="range"
            min="0"
            max="1"
            step="0.01"
            value={opacity}
            onChange={(e) => handleOpacityChange(parseFloat(e.target.value))}
            style={{ 
              width: '100%',
              height: '6px',
              borderRadius: '3px',
              background: `linear-gradient(to right, #ff4444 0%, #44ff44 100%)`,
              outline: 'none',
              cursor: 'pointer',
            }}
          />
        </div>
        
        {/* Playback Controls */}
        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <button
            onClick={handlePlayPause}
            style={{
              padding: '8px 16px',
              background: isPlaying ? '#ff4444' : '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '14px',
            }}
          >
            {isPlaying ? '⏸ Pause' : '▶ Play'}
          </button>
          
          <label style={{ fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            Speed:
            <select
              value={playbackSpeed}
              onChange={(e) => setPlaybackSpeed(parseFloat(e.target.value))}
              style={{
                padding: '6px',
                background: '#333',
                color: 'white',
                border: '1px solid #555',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              <option value="0.5">0.5x</option>
              <option value="1">1x</option>
              <option value="2">2x</option>
              <option value="4">4x</option>
            </select>
          </label>
          
          <button
            onClick={() => setOpacity(0)}
            style={{
              padding: '8px 12px',
              background: '#555',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Show Before
          </button>
          
          <button
            onClick={() => setOpacity(1)}
            style={{
              padding: '8px 12px',
              background: '#555',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            Show After
          </button>
          
          <button
            onClick={() => setOpacity(0.5)}
            style={{
              padding: '8px 12px',
              background: '#555',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
            }}
          >
            50/50
          </button>
        </div>
      </div>
      
      {/* Scene Comparison Viewer */}
      <div style={{ flex: 1 }}>
        <SceneComparison
          sceneId1={beforeSceneId}
          sceneId2={afterSceneId}
          mode="temporal"
          onError={onError}
        />
      </div>
    </div>
  );
};

export default TemporalComparison;
