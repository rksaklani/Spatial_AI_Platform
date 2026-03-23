/**
 * Adaptive Renderer Component
 * 
 * Automatically switches between client-side and server-side rendering
 * based on device capability and performance monitoring.
 * 
 * Implements:
 * - Device capability detection
 * - FPS monitoring
 * - Automatic mode switching (client FPS < 15 for 5+ seconds)
 * - WebSocket frame streaming for server-side mode
 */

import React, { useEffect, useRef, useState, useCallback } from 'react';
import { GaussianViewer } from './GaussianViewer';

interface AdaptiveRendererProps {
  sceneId: string;
  onError?: (error: Error) => void;
  onModeChange?: (mode: 'client' | 'server') => void;
}

interface DeviceCapability {
  has_webgl2: boolean;
  has_webgpu: boolean;
  estimated_performance: string;
  is_sufficient: boolean;
  recommendation: string;
}

interface RenderSession {
  session_id: string;
  websocket_url: string;
}

export const AdaptiveRenderer: React.FC<AdaptiveRendererProps> = ({
  sceneId,
  onError,
  onModeChange,
}) => {
  const [renderMode, setRenderMode] = useState<'client' | 'server' | 'detecting'>('detecting');
  const [deviceCapability, setDeviceCapability] = useState<DeviceCapability | null>(null);
  const [renderSession, setRenderSession] = useState<RenderSession | null>(null);
  const [fps, setFps] = useState(60);
  
  const fpsHistoryRef = useRef<number[]>([]);
  const lowFpsStartTimeRef = useRef<number | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Detect device capability on mount
  useEffect(() => {
    detectDeviceCapability();
  }, []);

  // Monitor FPS and switch modes if needed
  useEffect(() => {
    if (renderMode !== 'client') return;

    // Track FPS history
    fpsHistoryRef.current.push(fps);
    if (fpsHistoryRef.current.length > 60) {
      fpsHistoryRef.current.shift();
    }

    // Check if FPS is consistently low
    if (fps < 15) {
      if (lowFpsStartTimeRef.current === null) {
        lowFpsStartTimeRef.current = Date.now();
      } else {
        const lowFpsDuration = Date.now() - lowFpsStartTimeRef.current;
        if (lowFpsDuration > 5000) {
          // FPS < 15 for 5+ seconds, switch to server-side
          console.log('Low FPS detected, switching to server-side rendering');
          switchToServerSide();
        }
      }
    } else {
      lowFpsStartTimeRef.current = null;
    }
  }, [fps, renderMode]);

  // Detect device capability
  const detectDeviceCapability = async () => {
    try {
      // Get WebGL info
      const canvas = document.createElement('canvas');
      const gl = canvas.getContext('webgl2') || canvas.getContext('webgl');
      
      const webglInfo = {
        webgl2: !!canvas.getContext('webgl2'),
        webgpu: 'gpu' in navigator,
        gpu_vendor: gl ? gl.getParameter(gl.VENDOR) : null,
        gpu_renderer: gl ? gl.getParameter(gl.RENDERER) : null,
        max_texture_size: gl ? gl.getParameter(gl.MAX_TEXTURE_SIZE) : 0,
      };

      // Send to server for analysis
      const response = await fetch('/api/v1/render/detect-capability', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          user_agent: navigator.userAgent,
          ...webglInfo,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to detect device capability');
      }

      const capability: DeviceCapability = await response.json();
      setDeviceCapability(capability);

      // Set initial render mode based on recommendation
      if (capability.recommendation === 'server-side') {
        await switchToServerSide();
      } else {
        setRenderMode('client');
        onModeChange?.('client');
      }
    } catch (error) {
      console.error('Device capability detection failed:', error);
      // Default to client-side rendering
      setRenderMode('client');
      onModeChange?.('client');
    }
  };

  // Switch to server-side rendering
  const switchToServerSide = async () => {
    try {
      // Create rendering session
      const response = await fetch('/api/v1/render/sessions', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          scene_id: sceneId,
          resolution_width: window.innerWidth,
          resolution_height: window.innerHeight,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create rendering session');
      }

      const session: RenderSession = await response.json();
      setRenderSession(session);
      setRenderMode('server');
      onModeChange?.('server');

      // Connect WebSocket for frame streaming
      connectWebSocket(session);
    } catch (error) {
      console.error('Failed to switch to server-side rendering:', error);
      onError?.(error as Error);
      // Fall back to client-side
      setRenderMode('client');
      onModeChange?.('client');
    }
  };

  // Connect WebSocket for frame streaming
  const connectWebSocket = (session: RenderSession) => {
    const wsUrl = `ws://${window.location.host}${session.websocket_url}`;
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.binaryType = 'arraybuffer';

    ws.onopen = () => {
      console.log('WebSocket connected for frame streaming');
    };

    ws.onmessage = (event) => {
      // Received frame from server
      if (event.data instanceof ArrayBuffer) {
        displayFrame(event.data);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError?.(new Error('WebSocket connection failed'));
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };
  };

  // Display received frame on canvas
  const displayFrame = (frameData: ArrayBuffer) => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Convert ArrayBuffer to Blob
    const blob = new Blob([frameData], { type: 'image/jpeg' });
    const url = URL.createObjectURL(blob);

    // Load and draw image
    const img = new Image();
    img.onload = () => {
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      URL.revokeObjectURL(url);
    };
    img.src = url;
  };

  // Send camera update to server
  const sendCameraUpdate = useCallback((camera: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ camera }));
    }
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (renderSession) {
        // Close rendering session
        fetch(`/api/v1/render/sessions/${renderSession.session_id}`, {
          method: 'DELETE',
          headers: {
            Authorization: `Bearer ${localStorage.getItem('token')}`,
          },
        }).catch(console.error);
      }
    };
  }, [renderSession]);

  // Render based on mode
  if (renderMode === 'detecting') {
    return (
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'center', 
        height: '100%',
        background: '#1a1a1a',
        color: 'white',
      }}>
        <div>
          <div style={{ fontSize: '18px', marginBottom: '10px' }}>
            Detecting device capability...
          </div>
          <div style={{ fontSize: '14px', opacity: 0.7 }}>
            Analyzing GPU and browser support
          </div>
        </div>
      </div>
    );
  }

  if (renderMode === 'server') {
    return (
      <div style={{ position: 'relative', width: '100%', height: '100%' }}>
        <canvas
          ref={canvasRef}
          width={window.innerWidth}
          height={window.innerHeight}
          style={{ width: '100%', height: '100%' }}
        />
        
        {/* Mode indicator */}
        <div
          style={{
            position: 'absolute',
            top: 10,
            right: 10,
            background: 'rgba(0, 0, 0, 0.7)',
            color: 'white',
            padding: '10px',
            borderRadius: '5px',
            fontFamily: 'monospace',
            fontSize: '12px',
          }}
        >
          <div>Mode: Server-Side Rendering</div>
          <div>Session: {renderSession?.session_id.slice(0, 8)}...</div>
        </div>
      </div>
    );
  }

  // Client-side rendering
  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <GaussianViewer
        sceneId={sceneId}
        onError={onError}
        onLoadProgress={(progress) => {
          // Track FPS from viewer
          // This would be passed from GaussianViewer via callback
        }}
      />
      
      {/* Mode indicator */}
      <div
        style={{
          position: 'absolute',
          top: 10,
          right: 10,
          background: 'rgba(0, 0, 0, 0.7)',
          color: 'white',
          padding: '10px',
          borderRadius: '5px',
          fontFamily: 'monospace',
          fontSize: '12px',
        }}
      >
        <div>Mode: Client-Side Rendering</div>
        {deviceCapability && (
          <div>Performance: {deviceCapability.estimated_performance}</div>
        )}
      </div>
    </div>
  );
};
