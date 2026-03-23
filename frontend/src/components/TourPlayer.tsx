import React, { useState, useEffect, useRef } from 'react';
import * as THREE from 'three';

interface CameraKeyframe {
  position: [number, number, number];
  rotation: [number, number, number, number]; // quaternion
  timestamp: number;
}

interface Narration {
  timestamp: number;
  text: string;
}

interface GuidedTour {
  id: string;
  name: string;
  camera_path: CameraKeyframe[];
  narration: Narration[];
  duration: number;
}

interface TourPlayerProps {
  tour: GuidedTour;
  camera: THREE.PerspectiveCamera;
  onComplete?: () => void;
}

export const TourPlayer: React.FC<TourPlayerProps> = ({ tour, camera, onComplete }) => {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [currentNarration, setCurrentNarration] = useState<string | null>(null);
  
  const animationFrameRef = useRef<number>();
  const startTimeRef = useRef<number>(0);
  const pausedTimeRef = useRef<number>(0);

  // Interpolate between two keyframes
  const interpolateKeyframes = (
    kf1: CameraKeyframe,
    kf2: CameraKeyframe,
    t: number
  ): { position: THREE.Vector3; quaternion: THREE.Quaternion } => {
    const alpha = (t - kf1.timestamp) / (kf2.timestamp - kf1.timestamp);
    
    // Interpolate position
    const pos1 = new THREE.Vector3(...kf1.position);
    const pos2 = new THREE.Vector3(...kf2.position);
    const position = pos1.lerp(pos2, alpha);
    
    // Interpolate rotation (quaternion slerp)
    const quat1 = new THREE.Quaternion(...kf1.rotation);
    const quat2 = new THREE.Quaternion(...kf2.rotation);
    const quaternion = quat1.slerp(quat2, alpha);
    
    return { position, quaternion };
  };

  // Find keyframes surrounding current time
  const findKeyframes = (time: number): [CameraKeyframe, CameraKeyframe] | null => {
    const path = tour.camera_path;
    
    for (let i = 0; i < path.length - 1; i++) {
      if (time >= path[i].timestamp && time <= path[i + 1].timestamp) {
        return [path[i], path[i + 1]];
      }
    }
    
    return null;
  };

  // Update camera position based on current time
  const updateCamera = (time: number) => {
    const keyframes = findKeyframes(time);
    
    if (keyframes) {
      const [kf1, kf2] = keyframes;
      const { position, quaternion } = interpolateKeyframes(kf1, kf2, time);
      
      camera.position.copy(position);
      camera.quaternion.copy(quaternion);
    }
  };

  // Update narration based on current time
  const updateNarration = (time: number) => {
    // Find narration closest to current time (within 0.5 seconds)
    const activeNarration = tour.narration.find(
      n => Math.abs(n.timestamp - time) < 0.5
    );
    
    if (activeNarration) {
      setCurrentNarration(activeNarration.text);
    } else {
      setCurrentNarration(null);
    }
  };

  // Animation loop
  const animate = (timestamp: number) => {
    if (!isPlaying || isPaused) return;
    
    const elapsed = (timestamp - startTimeRef.current) / 1000; // Convert to seconds
    const currentTime = pausedTimeRef.current + elapsed;
    
    if (currentTime >= tour.duration) {
      // Tour completed
      setIsPlaying(false);
      setCurrentTime(tour.duration);
      updateCamera(tour.duration);
      updateNarration(tour.duration);
      
      if (onComplete) {
        onComplete();
      }
      return;
    }
    
    setCurrentTime(currentTime);
    updateCamera(currentTime);
    updateNarration(currentTime);
    
    animationFrameRef.current = requestAnimationFrame(animate);
  };

  // Play tour
  const play = () => {
    if (currentTime >= tour.duration) {
      // Restart from beginning
      pausedTimeRef.current = 0;
      setCurrentTime(0);
    }
    
    setIsPlaying(true);
    setIsPaused(false);
    startTimeRef.current = performance.now();
    animationFrameRef.current = requestAnimationFrame(animate);
  };

  // Pause tour
  const pause = () => {
    setIsPaused(true);
    pausedTimeRef.current = currentTime;
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  // Resume tour
  const resume = () => {
    setIsPaused(false);
    startTimeRef.current = performance.now();
    animationFrameRef.current = requestAnimationFrame(animate);
  };

  // Restart tour
  const restart = () => {
    pausedTimeRef.current = 0;
    setCurrentTime(0);
    setIsPlaying(false);
    setIsPaused(false);
    updateCamera(0);
    updateNarration(0);
    
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, []);

  // Format time as MM:SS
  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="tour-player">
      <div className="tour-controls">
        <h3>{tour.name}</h3>
        
        <div className="playback-controls">
          {!isPlaying ? (
            <button onClick={play} className="btn-play">
              ▶ Play
            </button>
          ) : isPaused ? (
            <button onClick={resume} className="btn-resume">
              ▶ Resume
            </button>
          ) : (
            <button onClick={pause} className="btn-pause">
              ⏸ Pause
            </button>
          )}
          
          <button onClick={restart} className="btn-restart">
            ⏮ Restart
          </button>
        </div>
        
        <div className="time-display">
          <span>{formatTime(currentTime)}</span>
          <span> / </span>
          <span>{formatTime(tour.duration)}</span>
        </div>
        
        <div className="progress-bar">
          <div 
            className="progress-fill" 
            style={{ width: `${(currentTime / tour.duration) * 100}%` }}
          />
        </div>
      </div>
      
      {currentNarration && (
        <div className="narration-overlay">
          <p>{currentNarration}</p>
        </div>
      )}
      
      <style>{`
        .tour-player {
          position: absolute;
          bottom: 20px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 0, 0, 0.8);
          color: white;
          padding: 20px;
          border-radius: 10px;
          min-width: 400px;
          z-index: 1000;
        }
        
        .tour-controls h3 {
          margin: 0 0 15px 0;
          font-size: 18px;
        }
        
        .playback-controls {
          display: flex;
          gap: 10px;
          margin-bottom: 10px;
        }
        
        .playback-controls button {
          padding: 8px 16px;
          border: none;
          border-radius: 5px;
          background: #4CAF50;
          color: white;
          cursor: pointer;
          font-size: 14px;
        }
        
        .playback-controls button:hover {
          background: #45a049;
        }
        
        .btn-pause {
          background: #ff9800 !important;
        }
        
        .btn-pause:hover {
          background: #e68900 !important;
        }
        
        .btn-restart {
          background: #2196F3 !important;
        }
        
        .btn-restart:hover {
          background: #0b7dda !important;
        }
        
        .time-display {
          margin-bottom: 10px;
          font-size: 14px;
        }
        
        .progress-bar {
          width: 100%;
          height: 6px;
          background: rgba(255, 255, 255, 0.3);
          border-radius: 3px;
          overflow: hidden;
        }
        
        .progress-fill {
          height: 100%;
          background: #4CAF50;
          transition: width 0.1s linear;
        }
        
        .narration-overlay {
          position: absolute;
          top: -80px;
          left: 50%;
          transform: translateX(-50%);
          background: rgba(0, 0, 0, 0.9);
          padding: 15px 20px;
          border-radius: 8px;
          max-width: 500px;
          text-align: center;
        }
        
        .narration-overlay p {
          margin: 0;
          font-size: 16px;
          line-height: 1.4;
        }
      `}</style>
    </div>
  );
};
