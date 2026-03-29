import { useState } from 'react';
import { useGetScenesQuery } from '../store/api/sceneApi';
import { useGetActiveUsersQuery } from '../store/api/collaborationApi';
import { UsersIcon, ClockIcon } from '@heroicons/react/24/outline';

export function CollaborationPage() {
  const [selectedSceneId, setSelectedSceneId] = useState<string>('');
  
  const { data: scenes = [] } = useGetScenesQuery();
  const { data: activeUsersData } = useGetActiveUsersQuery(selectedSceneId, {
    skip: !selectedSceneId,
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className="min-h-screen p-8">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Collaboration</h1>
        <p className="text-text-secondary">
          View active users and collaborate on scenes in real-time
        </p>
      </div>

      <div className="bg-secondary-bg border border-border-color rounded-xl p-6 mb-6">
        <label className="block text-sm font-medium text-text-primary mb-2">
          Select Scene
        </label>
        <select
          value={selectedSceneId}
          onChange={(e) => setSelectedSceneId(e.target.value)}
          className="w-full px-4 py-2 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
        >
          <option value="">Choose a scene...</option>
          {scenes.map((scene) => (
            <option key={scene.sceneId} value={scene.sceneId}>
              {scene.name}
            </option>
          ))}
        </select>
      </div>

      {selectedSceneId && activeUsersData && (
        <div>
          <div className="flex items-center gap-3 mb-6">
            <UsersIcon className="w-6 h-6 text-accent-primary" />
            <h2 className="text-xl font-bold text-text-primary">
              Active Users ({activeUsersData.count})
            </h2>
          </div>

          {activeUsersData.active_users.length === 0 ? (
            <div className="text-center py-12 bg-secondary-bg border border-border-color rounded-xl">
              <UsersIcon className="w-16 h-16 text-text-muted mx-auto mb-4" />
              <p className="text-text-secondary">No active users in this scene</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {activeUsersData.active_users.map((user) => (
                <div
                  key={user.user_id}
                  className="bg-secondary-bg border border-border-color rounded-xl p-6"
                >
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-accent-primary/20 rounded-full flex items-center justify-center">
                        <span className="text-accent-primary font-bold text-lg">
                          {user.user_name.charAt(0).toUpperCase()}
                        </span>
                      </div>
                      <div>
                        <p className="text-text-primary font-medium">{user.user_name}</p>
                        <div className="flex items-center gap-1 mt-1">
                          <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                          <span className="text-xs text-text-muted">Active</span>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <ClockIcon className="w-4 h-4 text-text-muted" />
                      <span className="text-text-secondary">
                        Joined {formatTimestamp(user.joined_at)}
                      </span>
                    </div>

                    {user.cursor_position && (
                      <div className="p-3 bg-primary-bg rounded-lg">
                        <p className="text-xs text-text-muted mb-1">Cursor Position</p>
                        <p className="text-xs text-text-primary font-mono">
                          [{user.cursor_position.map(v => v.toFixed(2)).join(', ')}]
                        </p>
                      </div>
                    )}

                    <div className="text-xs text-text-muted">
                      Last seen {formatTimestamp(user.last_heartbeat)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {!selectedSceneId && (
        <div className="text-center py-12 bg-secondary-bg border border-border-color rounded-xl">
          <UsersIcon className="w-16 h-16 text-text-muted mx-auto mb-4" />
          <p className="text-text-secondary">Select a scene to view active collaborators</p>
        </div>
      )}
    </div>
  );
}
