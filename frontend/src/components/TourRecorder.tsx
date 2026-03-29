import React, { useState, useRef, useEffect } from 'react';
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

interface TourRecorderProps {
  camera: THREE.PerspectiveCamera;
  onSave: (tourData: {
    name: string;
    camera_path: CameraKeyframe[];
    narration: Narration[];
  }) => void;
  onCancel: () => void;
}

export const TourRecorder: React.FC<TourRecorderProps> = ({ camera, onSave, onCancel }) => {
  const [isRecording, setIsRecording] = useState(false);
  const [tourName, setTourName] = useState('');
  const [cameraPath, setCameraPath] = useState<CameraKeyframe[]>([]);
  const [narrations, setNarrations] = useState<Narration[]>([]);
  const [currentNarration, setCurrentNarration] = useState('');
  const [recordingTime, setRecordingTime] = useState(0);
  
  const recordingStartRef = useRef<number>(0);
  const recordingIntervalRef = useRef<number>();
  const timeUpdateIntervalRef = useRef<number>();

  // Start recording
  const startRecording = () => {
    if (!tourName.trim()) {
      alert('Please enter a tour name');
      return;
    }
    
    setIsRecording(true);
    setCameraPath([]);
    setNarrations([]);
    setRecordingTime(0);
    recordingStartRef.current = performance.now();
    
    // Record camera position at 10 samples per second (every 100ms)
    recordingIntervalRef.current = window.setInterval(() => {
      const elapsed = (performance.now() - recordingStartRef.current) / 1000;
      
      const keyframe: CameraKeyframe = {
        position: [camera.position.x, camera.position.y, camera.position.z],
        rotation: [
          camera.quaternion.x,
          camera.quaternion.y,
          camera.quaternion.z,
          camera.quaternion.w
        ],
        timestamp: elapsed
      };
      
      setCameraPath(prev => [...prev, keyframe]);
    }, 100); // 10 samples per second
    
    // Update recording time display
    timeUpdateIntervalRef.current = window.setInterval(() => {
      const elapsed = (performance.now() - recordingStartRef.current) / 1000;
      setRecordingTime(elapsed);
    }, 100);
  };

  // Stop recording
  const stopRecording = () => {
    setIsRecording(false);
    
    if (recordingIntervalRef.current) {
      clearInterval(recordingIntervalRef.current);
    }
    
    if (timeUpdateIntervalRef.current) {
      clearInterval(timeUpdateIntervalRef.current);
    }
  };

  // Add narration at current timestamp
  const addNarration = () => {
    if (!currentNarration.trim()) {
      alert('Please enter narration text');
      return;
    }
    
    if (!isRecording) {
      alert('Start recording first');
      return;
    }
    
    const elapsed = (performance.now() - recordingStartRef.current) / 1000;
    
    const narration: Narration = {
      timestamp: elapsed,
      text: currentNarration.trim()
    };
    
    setNarrations(prev => [...prev, narration]);
    setCurrentNarration('');
  };

  // Save tour
  const handleSave = () => {
    if (cameraPath.length === 0) {
      alert('Record some camera movement first');
      return;
    }
    
    onSave({
      name: tourName,
      camera_path: cameraPath,
      narration: narrations
    });
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (recordingIntervalRef.current) {
        clearInterval(recordingIntervalRef.current);
      }
      if (timeUpdateIntervalRef.current) {
        clearInterval(timeUpdateIntervalRef.current);
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
    <div className="tour-recorder">
      <div className="recorder-panel">
        <h3>Record Guided Tour</h3>
        
        {!isRecording && cameraPath.length === 0 && (
          <div className="setup-section">
            <input
              type="text"
              placeholder="Tour name"
              value={tourName}
              onChange={(e) => setTourName(e.target.value)}
              className="tour-name-input"
            />
            
            <button onClick={startRecording} className="btn-start-recording">
              ⏺ Start Recording
            </button>
          </div>
        )}
        
        {isRecording && (
          <div className="recording-section">
            <div className="recording-indicator">
              <span className="recording-dot"></span>
              <span>Recording: {formatTime(recordingTime)}</span>
            </div>
            
            <div className="narration-input-section">
              <input
                type="text"
                placeholder="Add narration at this point..."
                value={currentNarration}
                onChange={(e) => setCurrentNarration(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addNarration()}
                className="narration-input"
              />
              <button onClick={addNarration} className="btn-add-narration">
                + Add
              </button>
            </div>
            
            <button onClick={stopRecording} className="btn-stop-recording">
              ⏹ Stop Recording
            </button>
          </div>
        )}
        
        {!isRecording && cameraPath.length > 0 && (
          <div className="review-section">
            <p>Recorded {cameraPath.length} camera positions ({formatTime(recordingTime)})</p>
            <p>{narrations.length} narration(s) added</p>
            
            {narrations.length > 0 && (
              <div className="narrations-list">
                <h4>Narrations:</h4>
                <ul>
                  {narrations.map((n, i) => (
                    <li key={i}>
                      <strong>{formatTime(n.timestamp)}:</strong> {n.text}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <div className="action-buttons">
              <button onClick={handleSave} className="btn-save">
                💾 Save Tour
              </button>
              <button onClick={onCancel} className="btn-cancel">
                ✕ Cancel
              </button>
            </div>
          </div>
        )}
      </div>
      
      <style>{`
        .tour-recorder {
          position: absolute;
          top: 20px;
          right: 20px;
          background: rgba(0, 0, 0, 0.9);
          color: white;
          padding: 20px;
          border-radius: 10px;
          min-width: 350px;
          z-index: 1000;
        }
        
        .recorder-panel h3 {
          margin: 0 0 15px 0;
          font-size: 18px;
        }
        
        .setup-section {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        
        .tour-name-input {
          padding: 10px;
          border: 1px solid #555;
          border-radius: 5px;
          background: #222;
          color: white;
          font-size: 14px;
        }
        
        .btn-start-recording {
          padding: 12px;
          border: none;
          border-radius: 5px;
          background: #f44336;
          color: white;
          cursor: pointer;
          font-size: 16px;
          font-weight: bold;
        }
        
        .btn-start-recording:hover {
          background: #da190b;
        }
        
        .recording-section {
          display: flex;
          flex-direction: column;
          gap: 15px;
        }
        
        .recording-indicator {
          display: flex;
          align-items: center;
          gap: 10px;
          font-size: 16px;
          font-weight: bold;
        }
        
        .recording-dot {
          width: 12px;
          height: 12px;
          background: #f44336;
          border-radius: 50%;
          animation: pulse 1.5s infinite;
        }
        
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.3; }
        }
        
        .narration-input-section {
          display: flex;
          gap: 10px;
        }
        
        .narration-input {
          flex: 1;
          padding: 8px;
          border: 1px solid #555;
          border-radius: 5px;
          background: #222;
          color: white;
          font-size: 14px;
        }
        
        .btn-add-narration {
          padding: 8px 16px;
          border: none;
          border-radius: 5px;
          background: #4CAF50;
          color: white;
          cursor: pointer;
          font-size: 14px;
        }
        
        .btn-add-narration:hover {
          background: #45a049;
        }
        
        .btn-stop-recording {
          padding: 12px;
          border: none;
          border-radius: 5px;
          background: #ff9800;
          color: white;
          cursor: pointer;
          font-size: 16px;
          font-weight: bold;
        }
        
        .btn-stop-recording:hover {
          background: #e68900;
        }
        
        .review-section {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        
        .review-section p {
          margin: 0;
          font-size: 14px;
        }
        
        .narrations-list {
          margin-top: 10px;
          max-height: 200px;
          overflow-y: auto;
        }
        
        .narrations-list h4 {
          margin: 0 0 10px 0;
          font-size: 14px;
        }
        
        .narrations-list ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }
        
        .narrations-list li {
          padding: 8px;
          background: rgba(255, 255, 255, 0.1);
          border-radius: 5px;
          margin-bottom: 5px;
          font-size: 13px;
        }
        
        .action-buttons {
          display: flex;
          gap: 10px;
          margin-top: 10px;
        }
        
        .btn-save {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 5px;
          background: #4CAF50;
          color: white;
          cursor: pointer;
          font-size: 16px;
          font-weight: bold;
        }
        
        .btn-save:hover {
          background: #45a049;
        }
        
        .btn-cancel {
          flex: 1;
          padding: 12px;
          border: none;
          border-radius: 5px;
          background: #666;
          color: white;
          cursor: pointer;
          font-size: 16px;
        }
        
        .btn-cancel:hover {
          background: #555;
        }
      `}</style>
    </div>
  );
};
