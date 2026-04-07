/**
 * WebSocket service for real-time collaboration
 * 
 * Handles WebSocket connection lifecycle, reconnection with exponential backoff,
 * and event-based message handling for real-time features like collaboration,
 * cursor tracking, and annotation sync.
 * 
 * Uses native WebSocket API (not Socket.IO) to match FastAPI backend.
 */

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

type EventHandler = (data: any) => void;

class WebSocketService {
  private ws: WebSocket | null = null;
  private connectionStatus: ConnectionStatus = 'disconnected';
  private statusListeners: Set<(status: ConnectionStatus) => void> = new Set();
  private eventHandlers: Map<string, Set<EventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 10;
  private baseReconnectDelay = 1000; // 1 second
  private maxReconnectDelay = 30000; // 30 seconds
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null;
  private currentSceneId: string | null = null;
  private currentToken: string | null = null;
  private currentUserId: string | null = null;
  private currentUserName: string | null = null;

  /**
   * Connect to WebSocket server
   */
  connect(sceneId: string, token: string, userId?: string, userName?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.warn('WebSocket already connected');
      return;
    }

    this.currentSceneId = sceneId;
    this.currentToken = token;
    this.currentUserId = userId || 'anonymous';
    this.currentUserName = userName || 'Anonymous User';

    this.setStatus('connecting');

    try {
      // Use native WebSocket (not Socket.IO).
      // Prefer explicit VITE_WS_URL, then VITE_WS_HOST/PORT, then current host.
      const envWsUrl = import.meta.env.VITE_WS_URL as string | undefined;
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = import.meta.env.VITE_WS_HOST || window.location.hostname;
      const wsPort = import.meta.env.VITE_WS_PORT || '8000';
      const wsBase = envWsUrl || `${wsProtocol}//${wsHost}:${wsPort}`;
      const wsUrl = `${wsBase.replace(/\/$/, '')}/ws/scenes/${sceneId}/collaborate?token=${encodeURIComponent(token)}`;

      console.log('Connecting to WebSocket:', wsUrl);

      this.ws = new WebSocket(wsUrl);
      this.setupEventHandlers();
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.setStatus('error');
      this.scheduleReconnect();
    }
  }

  /**
   * Disconnect from WebSocket server
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.reconnectAttempts = 0;
    this.currentSceneId = null;
    this.currentToken = null;
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
  private send(message: WebSocketMessage): void {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      console.error('Cannot send message: WebSocket not connected');
      return;
    }

    try {
      this.ws.send(JSON.stringify(message));
    } catch (error) {
      console.error('Failed to send WebSocket message:', error);
    }
  }

  /**
   * Send cursor movement update
   */
  sendCursorMove(position: [number, number, number]): void {
    this.send({
      type: 'cursor_move',
      position,
    });
  }

  /**
   * Send annotation created event
   */
  sendAnnotationCreated(annotation: any): void {
    this.send({
      type: 'annotation_create',
      annotation,
    });
  }

  /**
   * Send annotation updated event
   */
  sendAnnotationUpdated(annotationId: string, changes: any): void {
    this.send({
      type: 'annotation_update',
      annotation_id: annotationId,
      changes,
    });
  }

  /**
   * Send annotation deleted event
   */
  sendAnnotationDeleted(annotationId: string): void {
    this.send({
      type: 'annotation_delete',
      annotation_id: annotationId,
    });
  }

  /**
   * Setup WebSocket event handlers
   */
  private setupEventHandlers(): void {
    if (!this.ws) return;

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
      this.setStatus('connected');

      // Send join message
      this.send({
        type: 'join',
        user_id: this.currentUserId!,
        user_name: this.currentUserName!,
      });

      // Start heartbeat
      this.startHeartbeat();
    };

    this.ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      this.setStatus('disconnected');

      // Stop heartbeat
      if (this.heartbeatTimer) {
        clearInterval(this.heartbeatTimer);
        this.heartbeatTimer = null;
      }

      // Attempt reconnection if not manually disconnected
      if (event.code !== 1000) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      this.setStatus('error');
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };
  }

  /**
   * Start heartbeat to keep connection alive
   */
  private startHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
    }

    // Send heartbeat every 30 seconds
    this.heartbeatTimer = setInterval(() => {
      this.send({ type: 'heartbeat' });
    }, 30000);
  }

  /**
   * Handle incoming message
   */
  private handleMessage(message: WebSocketMessage): void {
    const { type, ...data } = message;

    // Emit to specific event handlers
    this.emitEvent(type, data);

    // Also emit generic message event
    this.emitEvent('message', message);
  }

  /**
   * Emit event to registered handlers
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

    if (this.reconnectTimer) {
      return; // Already scheduled
    }

    const delay = Math.min(
      this.baseReconnectDelay * Math.pow(2, this.reconnectAttempts),
      this.maxReconnectDelay
    );

    console.log(`Scheduling reconnection attempt ${this.reconnectAttempts + 1} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.reconnectAttempts++;
      
      if (this.currentSceneId && this.currentToken) {
        console.log('Attempting to reconnect...');
        this.connect(
          this.currentSceneId,
          this.currentToken,
          this.currentUserId || undefined,
          this.currentUserName || undefined
        );
      }
    }, delay);
  }
}

// Export singleton instance
export const websocketService = new WebSocketService();
