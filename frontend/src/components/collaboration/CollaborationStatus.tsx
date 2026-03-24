/**
 * Collaboration status component
 * 
 * Displays WebSocket connection status and active user count
 * for real-time collaboration features
 */

import { useEffect, useState } from 'react';
import { ConnectionStatus } from '../common/ConnectionStatus';
import { useWebSocket } from '../../hooks/useWebSocket';
import type { ActiveUsersPayload } from '../../types/websocket.types';

interface CollaborationStatusProps {
  sceneId: string;
  token: string;
}

export function CollaborationStatus({ sceneId, token }: CollaborationStatusProps) {
  const { status, isConnected, on } = useWebSocket({ sceneId, token });
  const [activeUserCount, setActiveUserCount] = useState(0);

  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to active users updates
    const unsubscribe = on('active_users', (payload: ActiveUsersPayload) => {
      setActiveUserCount(payload.users.length);
    });

    return unsubscribe;
  }, [isConnected, on]);

  return (
    <div className="flex items-center gap-4 px-4 py-2 bg-secondary-bg rounded-lg border border-border-color">
      <ConnectionStatus status={status} showLabel={true} size="md" />
      
      {isConnected && activeUserCount > 0 && (
        <div className="flex items-center gap-2 text-sm text-text-secondary">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"
            />
          </svg>
          <span>{activeUserCount} {activeUserCount === 1 ? 'user' : 'users'} online</span>
        </div>
      )}
    </div>
  );
}
