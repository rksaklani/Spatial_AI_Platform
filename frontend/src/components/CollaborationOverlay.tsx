import React, { useEffect, useState, useRef, useCallback } from 'react';
import * as THREE from 'three';
import { websocketService, ConnectionStatus } from '../services/websocket.service';

interface ActiveUser {
  userId: string;
  userName: string;
  color: string;
  cursor_position?: [number, number, number];
}

interface CollaborationOverlayProps {
  sceneId: string;
  userId: string;
  userName: string;
  token: string;
  scene: THREE.Scene;
  camera: THREE.Camera;
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
  camera,
  onAnnotationCreated,
  onAnnotationUpdated,
  onAnnotationDeleted,
}) => {
  const [activeUsers, setActiveUsers] = useState<Map<string, ActiveUser>>(new Map());
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const cursorMarkersRef = useRef<Map<string, THREE.Group>>(new Map());
  const cursorUpdateIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Handle user:joined event
  const handleUserJoined = useCallback((data: any) => {
    console.log('User joined:', data);
    const newUser: ActiveUser = {
      userId: data.user_id,
      userName: data.user_name,
      color: data.color || generateUserColor(data.user_id),
    };
    
    setActiveUsers((prev) => {
      const updated = new Map(prev);
      updated.set(newUser.userId, newUser);
      return updated;
    });
  }, []);

  // Handle user:left event
  const handleUserLeft = useCallback((data: any) => {
    console.log('User left:', data);
    const userIdToRemove = data.user_id;
    
    setActiveUsers((prev) => {
      const updated = new Map(prev);
      updated.delete(userIdToRemove);
      return updated;
    });
    
    // Remove cursor marker from scene
    const marker = cursorMarkersRef.current.get(userIdToRemove);
    if (marker) {
      scene.remove(marker);
      cursorMarkersRef.current.delete(userIdToRemove);
    }
  }, [scene]);

  // Handle cursor:move event
  const handleCursorMove = useCallback((data: any) => {
    const { user_id, position } = data;
    
    // Don't update our own cursor
    if (user_id === userId) return;
    
    // Update user's cursor position in state
    setActiveUsers((prev) => {
      const updated = new Map(prev);
      const user = updated.get(user_id);
      if (user) {
        updated.set(user_id, { ...user, cursor_position: position });
      }
      return updated;
    });
    
    // Update 3D cursor marker
    updateCursorMarker(user_id, position);
  }, [userId]);

  // Handle annotation:created event
  const handleAnnotationCreated = useCallback((data: any) => {
    console.log('Annotation created:', data);
    if (onAnnotationCreated) {
      onAnnotationCreated(data.annotation);
    }
  }, [onAnnotationCreated]);

  // Handle annotation:updated event
  const handleAnnotationUpdated = useCallback((data: any) => {
    console.log('Annotation updated:', data);
    if (onAnnotationUpdated) {
      onAnnotationUpdated(data.annotation_id, data.changes);
    }
  }, [onAnnotationUpdated]);

  // Handle annotation:deleted event
  const handleAnnotationDeleted = useCallback((data: any) => {
    console.log('Annotation deleted:', data);
    if (onAnnotationDeleted) {
      onAnnotationDeleted(data.annotation_id);
    }
  }, [onAnnotationDeleted]);

  // Handle active_users event (initial user list)
  const handleActiveUsers = useCallback((data: any) => {
    console.log('Active users:', data);
    const usersMap = new Map<string, ActiveUser>();
    
    if (data.users && Array.isArray(data.users)) {
      data.users.forEach((user: any) => {
        usersMap.set(user.user_id, {
          userId: user.user_id,
          userName: user.user_name,
          color: user.color || generateUserColor(user.user_id),
          cursor_position: user.cursor_position,
        });
      });
    }
    
    setActiveUsers(usersMap);
  }, []);

  // Handle connection status changes
  const handleStatusChange = useCallback((status: ConnectionStatus) => {
    setConnectionStatus(status);
    if (status === 'error') {
      setError('Connection error. Retrying...');
    } else if (status === 'connected') {
      setError(null);
    }
  }, []);

  // Handle WebSocket errors
  const handleError = useCallback((data: any) => {
    console.error('WebSocket error:', data);
    setError(data.message || 'An error occurred');
  }, []);

  useEffect(() => {
    // Connect to WebSocket
    websocketService.connect(sceneId, token);

    // Subscribe to connection status changes
    const unsubscribeStatus = websocketService.onStatusChange(handleStatusChange);

    // Subscribe to collaboration events
    const unsubscribeUserJoined = websocketService.on('user:joined', handleUserJoined);
    const unsubscribeUserLeft = websocketService.on('user:left', handleUserLeft);
    const unsubscribeCursorMove = websocketService.on('cursor:move', handleCursorMove);
    const unsubscribeAnnotationCreated = websocketService.on('annotation:created', handleAnnotationCreated);
    const unsubscribeAnnotationUpdated = websocketService.on('annotation:updated', handleAnnotationUpdated);
    const unsubscribeAnnotationDeleted = websocketService.on('annotation:deleted', handleAnnotationDeleted);
    const unsubscribeActiveUsers = websocketService.on('active_users', handleActiveUsers);
    const unsubscribeError = websocketService.on('error', handleError);

    // Start broadcasting local user's cursor movements
    cursorUpdateIntervalRef.current = setInterval(() => {
      if (camera && connectionStatus === 'connected') {
        const cameraPosition = camera.position.toArray() as [number, number, number];
        // For now, use camera position as cursor position
        // In a real implementation, you'd use raycasting to get the 3D point under the mouse
        websocketService.sendCursorMove(cameraPosition, cameraPosition);
      }
    }, 100); // Update every 100ms

    return () => {
      // Cleanup: unsubscribe from all events
      unsubscribeStatus();
      unsubscribeUserJoined();
      unsubscribeUserLeft();
      unsubscribeCursorMove();
      unsubscribeAnnotationCreated();
      unsubscribeAnnotationUpdated();
      unsubscribeAnnotationDeleted();
      unsubscribeActiveUsers();
      unsubscribeError();

      // Stop cursor updates
      if (cursorUpdateIntervalRef.current) {
        clearInterval(cursorUpdateIntervalRef.current);
      }

      // Clean up cursor markers
      cursorMarkersRef.current.forEach((marker) => {
        scene.remove(marker);
      });
      cursorMarkersRef.current.clear();

      // Disconnect WebSocket
      websocketService.disconnect();
    };
  }, [
    sceneId,
    token,
    camera,
    connectionStatus,
    scene,
    handleStatusChange,
    handleUserJoined,
    handleUserLeft,
    handleCursorMove,
    handleAnnotationCreated,
    handleAnnotationUpdated,
    handleAnnotationDeleted,
    handleActiveUsers,
    handleError,
  ]);

  // Update or create cursor marker in 3D scene
  const updateCursorMarker = useCallback((userId: string, position: [number, number, number]) => {
    let marker = cursorMarkersRef.current.get(userId);
    const user = activeUsers.get(userId);

    if (!marker) {
      // Create new cursor marker group (sphere + label)
      const group = new THREE.Group();
      
      // Create sphere
      const geometry = new THREE.SphereGeometry(0.15, 16, 16);
      const material = new THREE.MeshBasicMaterial({
        color: user?.color ? parseInt(user.color.replace('#', ''), 16) : generateUserColor(userId),
        transparent: true,
        opacity: 0.8,
      });
      const sphere = new THREE.Mesh(geometry, material);
      group.add(sphere);
      
      // Create label sprite (optional - can be added later)
      if (user?.userName) {
        const canvas = document.createElement('canvas');
        const context = canvas.getContext('2d');
        if (context) {
          canvas.width = 256;
          canvas.height = 64;
          context.fillStyle = 'rgba(0, 0, 0, 0.7)';
          context.fillRect(0, 0, canvas.width, canvas.height);
          context.font = '24px Arial';
          context.fillStyle = 'white';
          context.textAlign = 'center';
          context.fillText(user.userName, 128, 40);
          
          const texture = new THREE.CanvasTexture(canvas);
          const spriteMaterial = new THREE.SpriteMaterial({ map: texture });
          const sprite = new THREE.Sprite(spriteMaterial);
          sprite.scale.set(2, 0.5, 1);
          sprite.position.set(0, 0.5, 0);
          group.add(sprite);
        }
      }
      
      scene.add(group);
      cursorMarkersRef.current.set(userId, group);
      marker = group;
    }

    // Update position
    marker.position.set(position[0], position[1], position[2]);
  }, [scene, activeUsers]);

  // Generate consistent color from user ID
  const generateUserColor = (userId: string): number => {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = userId.charCodeAt(i) + ((hash << 5) - hash);
    }
    return Math.abs(hash) % 0xffffff;
  };

  const getColorHex = (userId: string): string => {
    const user = activeUsers.get(userId);
    if (user?.color) return user.color;
    return `#${generateUserColor(userId).toString(16).padStart(6, '0')}`;
  };

  const isConnected = connectionStatus === 'connected';

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
