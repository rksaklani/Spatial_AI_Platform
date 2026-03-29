/**
 * WebSocket service for real-time collaboration
 * 
 * Handles WebSocket connection lifecycle, reconnection with exponential backoff,
 * and event-based message handling for real-time features like collaboration,
 * cursor tracking, and annotation sync.
 */

import { io, Socket } from 'socket.io-client';

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
}

// Collaboration events
export interface UserJoinedEvent {
  type: 'user:joined';
  payload: {
    userId: string;
    userName: string;
    color: string;
  };
}

export interface UserLeftEvent {
  type: 'user:left';
  payload: {
    userId: string;
  };
}

export interface CursorMoveEvent {
  type: 'cursor:move';
  payload: {
    userId: string;
    position: [number, number, number];
    cameraPosition: [number, number, number];
  };
}

export interface AnnotationCreatedEvent {
  type: 'annotation:created';
  payload: {
    annotation: any;
  };
}

export interface AnnotationUpdatedEvent {
  type: 'annotation:updated';
  payload: {
    annotationId: string;
    changes: any;
  };
}

export interface AnnotationDeletedEvent {
  type: 'annotation:deleted';
  payload: {
    annotationId: string;
  };
}

type EventHandler = (data: any) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private connectionStatus: ConnectionStatus = 'disconnected';
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseReconnectDelay = 1000; // 1 second
  private maxReconnectDelay = 30000; // 30 seconds
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;

  /**
   * Connect to WebSocket server
   */
  connect(sceneId: string, token: string): void {
    if (this.socket?.connected) {
      console.warn('WebSocket already connected');
      return;
    }

    this.setStatus('connecting');

    const wsUrl = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

    this.socket = io(wsUrl, {
      path: `/ws/scenes/${sceneId}/collaborate`,
      auth: {
        token,
      },
      transports: ['websocket'],
      reconnection: false, // We handle reconnection manually
    });

    this.setupEventHandlers();
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }

    this.reconnectAttempts = 0;
    this.setStatus('disconnected');
  }

  /**
   * Get current connection status
   */
  getStatus(): ConnectionStatus {
    return this.connectionStatus;
  }

  /**
   * Subscribe to connection status changes
   */
  onStatusChange(listener: (status: ConnectionStatus) => void): () => void {
    this.statusListeners.add(listener);
    
    // Return unsubscribe function
    return () => {
      this.statusListeners.delete(listener);
    };
  }

  /**
   * Subscribe to specific event type
   */
  on(eventType: string, handler: EventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, new Set());
    }
    
    this.eventHandlers.get(eventType)!.add(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        handlers.delete(handler);
        if (handlers.size === 0) {
          this.eventHandlers.delete(eventType);
        }
      }
    };
  }

  /**
   * Send message to server
   */
  send(type: string, payload: any): void {
    if (!this.socket?.connected) {
      console.error('Cannot send message: WebSocket not connected');
      return;
    }

    this.socket.emit('message', {
      type,
      payload,
      timestamp: Date.now(),
    });
  }

  /**
   * Send cursor movement update
   */
  sendCursorMove(position: [number, number, number], cameraPosition: [number, number, number]): void {
    this.send('cursor_move', { position, cameraPosition });
  }

  /**
   * Send annotation created event
   */
  sendAnnotationCreated(annotation: any): void {
    this.send('annotation_created', { annotation });
  }

  /**
   * Send annotation updated event
   */
  sendAnnotationUpdated(annotationId: string, changes: any): void {
    this.send('annotation_updated', { annotation_id: annotationId, changes });
  }

  /**
   * Send annotation deleted event
   */
  sendAnnotationDeleted(annotationId: string): void {
    this.send('annotation_deleted', { annotation_id: annotationId });
  }

  /**
   * Setup socket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.socket) return;

    // Connection events
    this.socket.on('connect', () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.setStatus('connected');
    });

    this.socket.on('disconnect', (reason) => {
      console.log('WebSocket disconnected:', reason);
      this.setStatus('disconnected');

      // Attempt reconnection if not manually disconnected
      if (reason !== 'io client disconnect') {
        this.scheduleReconnect();
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
      this.setStatus('error');
      this.scheduleReconnect();
    });

    // Message events
    this.socket.on('message', (message: WebSocketMessage) => {
      this.handleMessage(message);
    });

    // Specific event types from backend
    this.socket.on('active_users', (data) => {
      this.emitEvent('active_users', data);
    });

    this.socket.on('user_joined', (data) => {
      this.emitEvent('user:joined', data);
    });

    this.socket.on('user_left', (data) => {
      this.emitEvent('user:left', data);
    });

    this.socket.on('cursor_update', (data) => {
      this.emitEvent('cursor:move', data);
    });

    this.socket.on('annotation_created', (data) => {
      this.emitEvent('annotation:created', data);
    });

    this.socket.on('annotation_updated', (data) => {
      this.emitEvent('annotation:updated', data);
    });

    this.socket.on('annotation_deleted', (data) => {
      this.emitEvent('annotation:deleted', data);
    });

    this.socket.on('error', (data) => {
      console.error('WebSocket error:', data);
      this.emitEvent('error', data);
    });
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    this.emitEvent(message.type, message.payload);
  }

  /**
   * Emit event to all registered handlers
   */
  private emitEvent(eventType: string, data: any): void {
    const handlers = this.eventHandlers.get(eventType);
    if (handlers) {
      handlers.forEach(handler => {
        try {
          handler(data);
        } catch (error) {
          console.error(`Error in event handler for ${eventType}:`, error);
        }
      });
    }
  }

  /**
   * Update connection status and notify listeners
   */
  private setStatus(status: ConnectionStatus): void {
    if (this.connectionStatus !== status) {
      this.connectionStatus = status;
      this.statusListeners.forEach(listener => {
        try {
          listener(status);
        } catch (error) {
          console.error('Error in status listener:', error);
        }
      });
    }
  }

  /**
   * Schedule reconnection with exponential backoff
   */
  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('Max reconnection attempts reached');
      this.setStatus('error');
      return;
    }

    // Calculate delay with exponential backoff
    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    this.reconnectAttempts++;
    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      if (this.socket && !this.socket.connected) {
        console.log('Attempting to reconnect...');
        this.socket.connect();
      }
    }, delay);
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
