import { useEffect, useRef, useState, useCallback } from 'react';

interface ActiveUser {
  user_id: string;
  user_name: string;
  scene_id: string;
  joined_at: number;
  last_heartbeat: number;
  cursor_position?: [number, number, number];
}

interface UseCollaborationOptions {
  sceneId: string;
  userId: string;
  userName: string;
  token: string;
  onAnnotationCreated?: (annotation: any) => void;
  onAnnotationUpdated?: (annotationId: string, changes: any) => void;
  onAnnotationDeleted?: (annotationId: string) => void;
}

interface UseCollaborationReturn {
  activeUsers: ActiveUser[];
  isConnected: boolean;
  error: string | null;
  sendCursorUpdate: (position: [number, number, number]) => void;
  sendAnnotationCreate: (annotation: any) => void;
  sendAnnotationUpdate: (annotationId: string, changes: any) => void;
  sendAnnotationDelete: (annotationId: string) => void;
}

export const useCollaboration = ({
  sceneId,
  userId,
  userName,
  token,
  onAnnotationCreated,
  onAnnotationUpdated,
  onAnnotationDeleted,
}: UseCollaborationOptions): UseCollaborationReturn => {
  const [activeUsers, setActiveUsers] = useState<ActiveUser[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const heartbeatIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 5;

  const connect = useCallback(() => {
    // Determine WebSocket protocol
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/v1/scenes/${sceneId}/collaborate?token=${token}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      setError(null);
      reconnectAttemptsRef.current = 0;

      // Send join message
      ws.send(
        JSON.stringify({
          type: 'join',
          user_id: userId,
          user_name: userName,
        })
      );

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
        heartbeatIntervalRef.current = null;
      }

      // Attempt reconnection
      if (reconnectAttemptsRef.current < maxReconnectAttempts) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current), 30000);
        console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current + 1}/${maxReconnectAttempts})`);
        
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttemptsRef.current++;
          connect();
        }, delay);
      } else {
        setError('Failed to reconnect after multiple attempts');
      }
    };
  }, [sceneId, userId, userName, token]);

  useEffect(() => {
    connect();

    return () => {
      // Cleanup
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
      if (heartbeatIntervalRef.current) {
        clearInterval(heartbeatIntervalRef.current);
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [connect]);

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
        setActiveUsers((prev) => prev.filter((user) => user.user_id !== message.user_id));
        break;

      case 'cursor_update':
        setActiveUsers((prev) =>
          prev.map((user) =>
            user.user_id === message.user_id
              ? { ...user, cursor_position: message.position }
              : user
          )
        );
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

  const sendCursorUpdate = useCallback((position: [number, number, number]) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'cursor_move',
          position,
        })
      );
    }
  }, []);

  const sendAnnotationCreate = useCallback((annotation: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'annotation_create',
          annotation,
        })
      );
    }
  }, []);

  const sendAnnotationUpdate = useCallback((annotationId: string, changes: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'annotation_update',
          annotation_id: annotationId,
          changes,
        })
      );
    }
  }, []);

  const sendAnnotationDelete = useCallback((annotationId: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: 'annotation_delete',
          annotation_id: annotationId,
        })
      );
    }
  }, []);

  return {
    activeUsers,
    isConnected,
    error,
    sendCursorUpdate,
    sendAnnotationCreate,
    sendAnnotationUpdate,
    sendAnnotationDelete,
  };
};

export default useCollaboration;
