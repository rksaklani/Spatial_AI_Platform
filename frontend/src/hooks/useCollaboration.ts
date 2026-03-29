/**
 * Hook for managing real-time collaboration in 3D viewer
 * Handles WebSocket connection, user tracking, and cursor synchronization
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { websocketService, ConnectionStatus } from '../services/websocket.service';
import { useAppSelector } from '../store/hooks';

export interface CollaborationUser {
  userId: string;
  userName: string;
  color: string;
  cursorPosition: [number, number, number] | null;
  cameraPosition: [number, number, number] | null;
  lastUpdate: number;
}

interface UseCollaborationProps {
  sceneId: string;
  enabled: boolean;
  onAnnotationCreated?: (annotation: any) => void;
  onAnnotationUpdated?: (annotationId: string, changes: any) => void;
  onAnnotationDeleted?: (annotationId: string) => void;
}

export function useCollaboration({
  sceneId,
  enabled,
  onAnnotationCreated,
  onAnnotationUpdated,
  onAnnotationDeleted,
}: UseCollaborationProps) {
  const token = useAppSelector((state) => state.auth.token);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>('disconnected');
  const [activeUsers, setActiveUsers] = useState<Map<string, CollaborationUser>>(new Map());
  const cursorThrottleRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const lastCursorSendRef = useRef<number>(0);
  const CURSOR_THROTTLE_MS = 100; // Send cursor updates max every 100ms

  // Connect to WebSocket when enabled
  useEffect(() => {
    if (!enabled || !sceneId || !token) {
      return;
    }

    console.log('Connecting to collaboration WebSocket for scene:', sceneId);
    websocketService.connect(sceneId, token);

    // Subscribe to status changes
    const unsubscribeStatus = websocketService.onStatusChange((status) => {
      setConnectionStatus(status);
      console.log('Collaboration connection status:', status);
    });

    // Cleanup on unmount
    return () => {
      unsubscribeStatus();
      websocketService.disconnect();
      setActiveUsers(new Map());
    };
  }, [enabled, sceneId, token]);

  // Handle user:joined event
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('user:joined', (data: any) => {
      console.log('User joined:', data);
      setActiveUsers((prev) => {
        const next = new Map(prev);
        next.set(data.user_id, {
          userId: data.user_id,
          userName: data.user_name || 'Anonymous',
          color: data.color || '#4ECDC4',
          cursorPosition: null,
          cameraPosition: null,
          lastUpdate: Date.now(),
        });
        return next;
      });
    });

    return unsubscribe;
  }, [enabled]);

  // Handle user:left event
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('user:left', (data: any) => {
      console.log('User left:', data);
      setActiveUsers((prev) => {
        const next = new Map(prev);
        next.delete(data.user_id);
        return next;
      });
    });

    return unsubscribe;
  }, [enabled]);

  // Handle cursor:move event
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('cursor:move', (data: any) => {
      setActiveUsers((prev) => {
        const user = prev.get(data.user_id);
        if (!user) return prev;

        const next = new Map(prev);
        next.set(data.user_id, {
          ...user,
          cursorPosition: data.position || null,
          cameraPosition: data.camera_position || null,
          lastUpdate: Date.now(),
        });
        return next;
      });
    });

    return unsubscribe;
  }, [enabled]);

  // Handle annotation:created event
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('annotation:created', (data: any) => {
      console.log('Annotation created by another user:', data);
      onAnnotationCreated?.(data.annotation);
    });

    return unsubscribe;
  }, [enabled, onAnnotationCreated]);

  // Handle annotation:updated event
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('annotation:updated', (data: any) => {
      console.log('Annotation updated by another user:', data);
      onAnnotationUpdated?.(data.annotation_id, data.changes);
    });

    return unsubscribe;
  }, [enabled, onAnnotationUpdated]);

  // Handle annotation:deleted event
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('annotation:deleted', (data: any) => {
      console.log('Annotation deleted by another user:', data);
      onAnnotationDeleted?.(data.annotation_id);
    });

    return unsubscribe;
  }, [enabled, onAnnotationDeleted]);

  // Handle active_users event (initial user list)
  useEffect(() => {
    if (!enabled) return;

    const unsubscribe = websocketService.on('active_users', (data: any) => {
      console.log('Active users:', data);
      if (data.users && Array.isArray(data.users)) {
        const usersMap = new Map<string, CollaborationUser>();
        data.users.forEach((user: any) => {
          usersMap.set(user.user_id, {
            userId: user.user_id,
            userName: user.user_name || 'Anonymous',
            color: user.color || '#4ECDC4',
            cursorPosition: null,
            cameraPosition: null,
            lastUpdate: Date.now(),
          });
        });
        setActiveUsers(usersMap);
      }
    });

    return unsubscribe;
  }, [enabled]);

  // Send cursor position update (throttled)
  const sendCursorPosition = useCallback(
    (position: [number, number, number], cameraPosition: [number, number, number]) => {
      if (!enabled || connectionStatus !== 'connected') return;

      const now = Date.now();
      const timeSinceLastSend = now - lastCursorSendRef.current;

      if (timeSinceLastSend < CURSOR_THROTTLE_MS) {
        // Throttle: schedule update for later
        if (cursorThrottleRef.current) {
          clearTimeout(cursorThrottleRef.current);
        }

        cursorThrottleRef.current = setTimeout(() => {
          websocketService.sendCursorMove(position, cameraPosition);
          lastCursorSendRef.current = Date.now();
        }, CURSOR_THROTTLE_MS - timeSinceLastSend);
      } else {
        // Send immediately
        websocketService.sendCursorMove(position, cameraPosition);
        lastCursorSendRef.current = now;
      }
    },
    [enabled, connectionStatus]
  );

  // Broadcast annotation created
  const broadcastAnnotationCreated = useCallback(
    (annotation: any) => {
      if (!enabled || connectionStatus !== 'connected') return;
      websocketService.sendAnnotationCreated(annotation);
    },
    [enabled, connectionStatus]
  );

  // Broadcast annotation updated
  const broadcastAnnotationUpdated = useCallback(
    (annotationId: string, changes: any) => {
      if (!enabled || connectionStatus !== 'connected') return;
      websocketService.sendAnnotationUpdated(annotationId, changes);
    },
    [enabled, connectionStatus]
  );

  // Broadcast annotation deleted
  const broadcastAnnotationDeleted = useCallback(
    (annotationId: string) => {
      if (!enabled || connectionStatus !== 'connected') return;
      websocketService.sendAnnotationDeleted(annotationId);
    },
    [enabled, connectionStatus]
  );

  return {
    connectionStatus,
    activeUsers: Array.from(activeUsers.values()),
    sendCursorPosition,
    broadcastAnnotationCreated,
    broadcastAnnotationUpdated,
    broadcastAnnotationDeleted,
  };
}
