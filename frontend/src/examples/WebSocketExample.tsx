/**
 * Example component demonstrating WebSocket service usage
 * 
 * This is a reference implementation showing how to integrate
 * real-time collaboration features into your components.
 */

import { useEffect, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';
import { ConnectionStatus } from '../components/common/ConnectionStatus';
import type {
  UserJoinedPayload,
  UserLeftPayload,
  CursorMovePayload,
  CollaborationUser,
} from '../types/websocket.types';

interface WebSocketExampleProps {
  sceneId: string;
  token: string;
}

export function WebSocketExample({ sceneId, token }: WebSocketExampleProps) {
  const { status, isConnected, on, sendCursorMove } = useWebSocket({
    sceneId,
    token,
    autoConnect: true,
  });

  const [users, setUsers] = useState<CollaborationUser[]>([]);
  const [messages, setMessages] = useState<string[]>([]);

  // Subscribe to collaboration events
  useEffect(() => {
    if (!isConnected) return;

    // Handle active users list
    const unsubscribeActiveUsers = on('active_users', (payload: { users: CollaborationUser[] }) => {
      setUsers(payload.users);
      addMessage(`Active users: ${payload.users.length}`);
    });

    // Handle user joined
    const unsubscribeUserJoined = on('user:joined', (payload: UserJoinedPayload) => {
      addMessage(`${payload.userName} joined`);
      setUsers((prev) => [
        ...prev,
        {
          userId: payload.userId,
          userName: payload.userName,
          color: payload.color,
          isActive: true,
        },
      ]);
    });

    // Handle user left
    const unsubscribeUserLeft = on('user:left', (payload: UserLeftPayload) => {
      addMessage(`User ${payload.userId} left`);
      setUsers((prev) => prev.filter((u) => u.userId !== payload.userId));
    });

    // Handle cursor movement
    const unsubscribeCursorMove = on('cursor:move', (payload: CursorMovePayload) => {
      setUsers((prev) =>
        prev.map((u) =>
          u.userId === payload.userId
            ? {
                ...u,
                cursorPosition: payload.position,
                cameraPosition: payload.cameraPosition,
              }
            : u
        )
      );
    });

    // Cleanup subscriptions
    return () => {
      unsubscribeActiveUsers();
      unsubscribeUserJoined();
      unsubscribeUserLeft();
      unsubscribeCursorMove();
    };
  }, [isConnected, on]);

  // Simulate cursor movement
  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isConnected) return;

    const rect = e.currentTarget.getBoundingClientRect();
    const x = ((e.clientX - rect.left) / rect.width) * 10 - 5;
    const y = ((e.clientY - rect.top) / rect.height) * 10 - 5;
    const z = 0;

    sendCursorMove([x, y, z], [0, 0, 5]);
  };

  const addMessage = (message: string) => {
    setMessages((prev) => [...prev.slice(-9), `${new Date().toLocaleTimeString()}: ${message}`]);
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-text-primary">WebSocket Example</h2>
        <ConnectionStatus status={status} showLabel={true} size="md" />
      </div>

      <div className="grid grid-cols-2 gap-6">
        {/* Interactive Area */}
        <div
          className="bg-secondary-bg rounded-xl border border-border-color p-8 cursor-crosshair"
          onMouseMove={handleMouseMove}
        >
          <p className="text-text-secondary text-center mb-4">
            Move your mouse here to broadcast cursor position
          </p>
          <div className="h-64 bg-primary-bg rounded-lg flex items-center justify-center">
            <span className="text-text-muted">Interactive Area</span>
          </div>
        </div>

        {/* Active Users */}
        <div className="bg-secondary-bg rounded-xl border border-border-color p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-4">
            Active Users ({users.length})
          </h3>
          <div className="space-y-2">
            {users.map((user) => (
              <div
                key={user.userId}
                className="flex items-center gap-3 p-3 bg-primary-bg rounded-lg"
              >
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: user.color }}
                />
                <span className="text-text-primary">{user.userName}</span>
                {user.cursorPosition && (
                  <span className="text-text-muted text-sm ml-auto">
                    [{user.cursorPosition.map((v) => v.toFixed(1)).join(', ')}]
                  </span>
                )}
              </div>
            ))}
            {users.length === 0 && (
              <p className="text-text-muted text-center py-8">No active users</p>
            )}
          </div>
        </div>
      </div>

      {/* Event Log */}
      <div className="bg-secondary-bg rounded-xl border border-border-color p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-4">Event Log</h3>
        <div className="space-y-1 font-mono text-sm">
          {messages.map((msg, i) => (
            <div key={i} className="text-text-secondary">
              {msg}
            </div>
          ))}
          {messages.length === 0 && (
            <p className="text-text-muted text-center py-4">No events yet</p>
          )}
        </div>
      </div>
    </div>
  );
}
