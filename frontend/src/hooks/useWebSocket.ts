/**
 * React hook for WebSocket connection management
 * 
 * Provides easy integration of WebSocket functionality into React components
 * with automatic cleanup and connection status tracking.
 */

import { useEffect, useState, useCallback } from 'react';
import { websocketService } from '../services/websocket.service';
import type { ConnectionStatus, EventHandler } from '../types/websocket.types';

interface UseWebSocketOptions {
  sceneId: string;
  token: string;
  autoConnect?: boolean;
}

interface UseWebSocketReturn {
  status: ConnectionStatus;
  isConnected: boolean;
  connect: () => void;
  disconnect: () => void;
  send: (type: string, payload: any) => void;
  on: (eventType: string, handler: EventHandler) => () => void;
  sendCursorMove: (position: [number, number, number], cameraPosition: [number, number, number]) => void;
  sendAnnotationCreated: (annotation: any) => void;
  sendAnnotationUpdated: (annotationId: string, changes: any) => void;
  sendAnnotationDeleted: (annotationId: string) => void;
}

/**
 * Hook for managing WebSocket connection in React components
 */
export function useWebSocket(options: UseWebSocketOptions): UseWebSocketReturn {
  const { sceneId, token, autoConnect = true } = options;
  const [status, setStatus] = useState<ConnectionStatus>(websocketService.getStatus());

  const connect = useCallback(() => {
    websocketService.connect(sceneId, token);
  }, [sceneId, token]);

  const disconnect = useCallback(() => {
    websocketService.disconnect();
  }, []);

  const send = useCallback((type: string, payload: any) => {
    websocketService.send(type, payload);
  }, []);

  const on = useCallback((eventType: string, handler: EventHandler) => {
    return websocketService.on(eventType, handler);
  }, []);

  const sendCursorMove = useCallback(
    (position: [number, number, number], cameraPosition: [number, number, number]) => {
      websocketService.sendCursorMove(position, cameraPosition);
    },
    []
  );

  const sendAnnotationCreated = useCallback((annotation: any) => {
    websocketService.sendAnnotationCreated(annotation);
  }, []);

  const sendAnnotationUpdated = useCallback((annotationId: string, changes: any) => {
    websocketService.sendAnnotationUpdated(annotationId, changes);
  }, []);

  const sendAnnotationDeleted = useCallback((annotationId: string) => {
    websocketService.sendAnnotationDeleted(annotationId);
  }, []);

  // Subscribe to status changes
  useEffect(() => {
    const unsubscribe = websocketService.onStatusChange(setStatus);
    return unsubscribe;
  }, []);

  // Auto-connect on mount if enabled
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    // Cleanup on unmount
    return () => {
      if (autoConnect) {
        disconnect();
      }
    };
  }, [autoConnect, connect, disconnect]);

  return {
    status,
    isConnected: status === 'connected',
    connect,
    disconnect,
    send,
    on,
    sendCursorMove,
    sendAnnotationCreated,
    sendAnnotationUpdated,
    sendAnnotationDeleted,
  };
}
