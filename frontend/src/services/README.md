# WebSocket Service

Real-time collaboration service for the Spatial AI Platform frontend.

## Overview

The WebSocket service provides a robust, production-ready implementation for real-time features including:

- Live cursor tracking across multiple users
- Real-time annotation synchronization
- User presence and activity tracking
- Automatic reconnection with exponential backoff
- Connection status monitoring

## Architecture

The service is built on Socket.IO client and provides:

1. **Connection Management**: Automatic connection lifecycle handling
2. **Event System**: Type-safe event emitter pattern
3. **Reconnection Logic**: Exponential backoff with configurable limits
4. **Status Tracking**: Real-time connection status updates

## Usage

### Basic Setup

```typescript
import { websocketService } from './services/websocket.service';

// Connect to a scene
websocketService.connect('scene-id', 'auth-token');

// Subscribe to connection status
const unsubscribe = websocketService.onStatusChange((status) => {
  console.log('Connection status:', status);
});

// Subscribe to events
const unsubscribeEvent = websocketService.on('user:joined', (payload) => {
  console.log('User joined:', payload);
});

// Send messages
websocketService.sendCursorMove([1, 2, 3], [4, 5, 6]);

// Cleanup
unsubscribe();
unsubscribeEvent();
websocketService.disconnect();
```

### React Hook

For React components, use the `useWebSocket` hook:

```typescript
import { useWebSocket } from './hooks/useWebSocket';

function CollaborationComponent({ sceneId, token }) {
  const { status, isConnected, on, sendCursorMove } = useWebSocket({
    sceneId,
    token,
    autoConnect: true,
  });

  useEffect(() => {
    if (!isConnected) return;

    const unsubscribe = on('user:joined', (payload) => {
      console.log('User joined:', payload);
    });

    return unsubscribe;
  }, [isConnected, on]);

  return (
    <div>
      <ConnectionStatus status={status} />
      {/* Your component content */}
    </div>
  );
}
```

## Event Types

### Incoming Events

- `active_users` - List of currently active users
- `user:joined` - New user joined the scene
- `user:left` - User left the scene
- `cursor:move` - User cursor position update
- `annotation:created` - New annotation created
- `annotation:updated` - Annotation modified
- `annotation:deleted` - Annotation removed
- `error` - Error message from server

### Outgoing Events

- `cursor_move` - Send cursor position update
- `annotation_created` - Broadcast new annotation
- `annotation_updated` - Broadcast annotation changes
- `annotation_deleted` - Broadcast annotation deletion

## Configuration

Environment variables:

```env
VITE_WS_URL=ws://localhost:8000
```

Service configuration (in `websocket.service.ts`):

```typescript
private maxReconnectAttempts = 10;
private baseReconnectDelay = 1000; // 1 second
private maxReconnectDelay = 30000; // 30 seconds
```

## Reconnection Strategy

The service implements exponential backoff for reconnection:

1. Initial delay: 1 second
2. Each attempt doubles the delay: 2s, 4s, 8s, 16s...
3. Maximum delay capped at 30 seconds
4. Maximum 10 attempts before giving up
5. Status changes to 'error' after max attempts

## Components

### ConnectionStatus

Visual indicator for connection status:

```typescript
import { ConnectionStatus } from './components/common/ConnectionStatus';

<ConnectionStatus status={status} showLabel={true} size="md" />
```

### CollaborationStatus

Complete collaboration status with user count:

```typescript
import { CollaborationStatus } from './components/collaboration/CollaborationStatus';

<CollaborationStatus sceneId={sceneId} token={token} />
```

## Testing

Unit tests are provided for both the service and hook:

```bash
npm test -- websocket.service.test.ts useWebSocket.test.ts
```

## Backend Integration

The service connects to the FastAPI backend WebSocket endpoint:

```
ws://localhost:8000/ws/scenes/{sceneId}/collaborate
```

Authentication is handled via token in the connection handshake.

## Type Safety

All events and payloads are fully typed. See `types/websocket.types.ts` for complete type definitions.

## Error Handling

The service handles various error scenarios:

- Connection failures → automatic reconnection
- Network interruptions → exponential backoff
- Authentication errors → error status
- Message send failures → console error logging

## Best Practices

1. Always unsubscribe from events when component unmounts
2. Use the React hook for component integration
3. Handle all connection states in your UI
4. Implement proper error boundaries
5. Test with network throttling and interruptions
