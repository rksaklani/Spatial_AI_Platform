/**
 * TypeScript types for WebSocket events and messages
 */

export type ConnectionStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: number;
}

// User collaboration types
export interface CollaborationUser {
  userId: string;
  userName: string;
  color: string;
  cursorPosition?: [number, number, number];
  cameraPosition?: [number, number, number];
  isActive: boolean;
}

// Event payload types
export interface UserJoinedPayload {
  userId: string;
  userName: string;
  color: string;
}

export interface UserLeftPayload {
  userId: string;
}

export interface CursorMovePayload {
  userId: string;
  position: [number, number, number];
  cameraPosition: [number, number, number];
}

export interface AnnotationCreatedPayload {
  annotation: {
    id: string;
    type: 'point' | 'line' | 'area' | 'text';
    position: [number, number, number];
    points?: [number, number, number][];
    text?: string;
    color: string;
    createdBy: string;
    createdAt: string;
  };
}

export interface AnnotationUpdatedPayload {
  annotationId: string;
  changes: Partial<{
    position: [number, number, number];
    points: [number, number, number][];
    text: string;
    color: string;
  }>;
}

export interface AnnotationDeletedPayload {
  annotationId: string;
}

export interface ActiveUsersPayload {
  users: CollaborationUser[];
}

export interface ErrorPayload {
  message: string;
  code?: string;
}

// Event types
export type WebSocketEventType =
  | 'active_users'
  | 'user:joined'
  | 'user:left'
  | 'cursor:move'
  | 'annotation:created'
  | 'annotation:updated'
  | 'annotation:deleted'
  | 'error';

// Event handler types
export type EventHandler<T = any> = (payload: T) => void;

export type ActiveUsersHandler = EventHandler<ActiveUsersPayload>;
export type UserJoinedHandler = EventHandler<UserJoinedPayload>;
export type UserLeftHandler = EventHandler<UserLeftPayload>;
export type CursorMoveHandler = EventHandler<CursorMovePayload>;
export type AnnotationCreatedHandler = EventHandler<AnnotationCreatedPayload>;
export type AnnotationUpdatedHandler = EventHandler<AnnotationUpdatedPayload>;
export type AnnotationDeletedHandler = EventHandler<AnnotationDeletedPayload>;
export type ErrorHandler = EventHandler<ErrorPayload>;
