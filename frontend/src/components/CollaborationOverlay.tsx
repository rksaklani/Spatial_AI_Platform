import React, { useEffect, useState, useRef } from 'react';
import * as THREE from 'three';

interface ActiveUser {
  user_id: string;
  user_name: string;
  scene_id: string;
  joined_at: number;
  last_heartbeat: number;
  cursor_position?: [number, number, number];
}

interface CollaborationOverlayProps {
  sceneId: string;
  userId: string;
  userName: string;
  token: string;
  scene: THREE.Scene;
  onAnnotationCreated?: (annotation: any) => void;
  onAnnotationUpdated?: (annotationId: string, changes: any) => void;
  onAnnotationDeleted?: (annotationId: string) => void;
}

export const CollaborationOverlay: React.FC<CollaborationOverlayProps> = ({
  sceneId,
  userId,
  userName,
  token,
  scene,
  onAnnotationCreated,
  onAnnotationUpdated,
  onAnnotationDeleted,
}) => {
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const cursorMarkersRef = useRef<Map<string, THREE.Mesh>>(new Map());

  useEffect(() => {
    // Connect to WebSocket
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/scenes/${sceneId}/collaborate?token=${token}`;
    
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);

      // Send join message
      ws.send(JSON.stringify({
        type: 'join',
        user_id: userId,
        user_name: userName,
      }));

      // Start heartbeat
      heartbeatIntervalRef.current = setInterval(() => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.send(JSON.stringify({ type: 'heartbeat' }));
        }
      }, 30000); // 30 seconds
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleMessage(message);
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    ws.onerror = (event) => {
      console.error('WebSocket error:', event);
      setError('Connection error');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Clear heartbeat
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }

      // Clean up cursor markers
      cursorMarkersRef.current.forEach((marker) => {
        scene.remove(marker);
      });
      cursorMarkersRef.current.clear();
    };

    return () => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
    };
  }, [sceneId, userId, userName, token, scene]);

  const handleMessage = (message: any) => {
    switch (message.type) {
      case 'active_users':
        setActiveUsers(message.users);
        break;

      case 'user_joined':
        setActiveUsers((prev) => [
          ...prev,
          {
            user_id: message.user_id,
            user_name: message.user_name,
            scene_id: sceneId,
            joined_at: Date.now() / 1000,
            last_heartbeat: Date.now() / 1000,
          },
        ]);
        break;

      case 'user_left':
        setActiveUsers((prev) =>
          prev.filter((user) => user.user_id !== message.user_id)
        );
        // Remove cursor marker
        const marker = cursorMarkersRef.current.get(message.user_id);
        if (marker) {
          scene.remove(marker);
          cursorMarkersRef.current.delete(message.user_id);
        }
        break;

      case 'cursor_update':
        updateCursorPosition(message.user_id, message.position);
        break;

      case 'annotation_created':
        if (onAnnotationCreated) {
          onAnnotationCreated(message.annotation);
        }
        break;

      case 'annotation_updated':
        if (onAnnotationUpdated) {
          onAnnotationUpdated(message.annotation_id, message.changes);
        }
        break;

      case 'annotation_deleted':
        if (onAnnotationDeleted) {
          onAnnotationDeleted(message.annotation_id);
        }
        break;

      case 'error':
        setError(message.message);
        console.error('Collaboration error:', message.message);
        break;

      default:
        console.warn('Unknown message type:', message.type);
    }
  };

  const updateCursorPosition = (userId: string, position: [number, number, number]) => {
    let marker = cursorMarkersRef.current.get(userId);

    if (!marker) {
      // Create new cursor marker
      const geometry = new THREE.SphereGeometry(0.1, 16, 16);
      const material = new THREE.MeshBasicMaterial({
        color: getUserColor(userId),
        transparent: true,
        opacity: 0.7,
      });
      marker = new THREE.Mesh(geometry, material);
      scene.add(marker);
      cursorMarkersRef.current.set(userId, marker);
    }

    // Update position
    marker.position.set(position[0], position[1], position[2]);
  };

  const getUserColor = (userId: string): number => {
    // Generate consistent color from user ID
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash) % 0xffffff;
  };

  const sendCursorUpdate = (position: [number, number, number]) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'cursor_move',
          position,
        })
      );
    }
  };

  const sendAnnotationCreate = (annotation: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'annotation_create',
          annotation,
        })
      );
    }
  };

  const sendAnnotationUpdate = (annotationId: string, changes: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'annotation_update',
          annotation_id: annotationId,
          changes,
        })
      );
    }
  };

  const sendAnnotationDelete = (annotationId: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'annotation_delete',
          annotation_id: annotationId,
        })
      );
    }
  };

  return (
    <div className="collaboration-overlay">
      {/* Connection status */}
      <div className="connection-status">
        {isConnected ? (
          <span className="status-connected">● Connected</span>
        ) : (
          <span className="status-disconnected">● Disconnected</span>
        )}
      </div>

      {/* Error message */}
      {error && (
        <div className="error-message">
          <span>⚠ {error}</span>
        </div>
      )}

      {/* Active users list */}
      <div className="active-users">
        <h3>Active Users ({activeUsers.length})</h3>
        <ul>
          {activeUsers.map((user) => (
            <li key={user.user_id}>
              <span
                className="user-indicator"
                style={{ backgroundColor: `#${getUserColor(user.user_id).toString(16).padStart(6, '0')}` }}
              />
              <span className="user-name">
                {user.user_name}
                {user.user_id === userId && ' (You)'}
              </span>
            </li>
          ))}
        </ul>
      </div>

      <style>{`
        .collaboration-overlay {
          position: fixed;
          top: 20px;
          right: 20px;
          z-index: 1000;
          background: rgba(0, 0, 0, 0.8);
          color: white;
          padding: 15px;
          border-radius: 8px;
          min-width: 200px;
          font-family: Arial, sans-serif;
        }

        .connection-status {
          margin-bottom: 10px;
          font-size: 12px;
        }

        .status-connected {
          color: #4caf50;
        }

        .status-disconnected {
          color: #f44336;
        }

        .error-message {
          background: #f44336;
          padding: 8px;
          border-radius: 4px;
          margin-bottom: 10px;
          font-size: 12px;
        }

        .active-users h3 {
          margin: 0 0 10px 0;
          font-size: 14px;
          font-weight: bold;
        }

        .active-users ul {
          list-style: none;
          padding: 0;
          margin: 0;
        }

        .active-users li {
          display: flex;
          align-items: center;
          padding: 5px 0;
          font-size: 13px;
        }

        .user-indicator {
          width: 10px;
          height: 10px;
          border-radius: 50%;
          margin-right: 8px;
          display: inline-block;
        }

        .user-name {
          flex: 1;
        }
      `}</style>
    </div>
  );
};

export default CollaborationOverlay;
