import { useState } from 'react';
import { Button, Dropdown } from '../common';
import {
  useCreateShareTokenMutation,
  useGetShareTokensQuery,
  useRevokeShareTokenMutation,
} from '../../store/api/sharingApi';
import { ClipboardDocumentIcon, TrashIcon, LinkIcon } from '@heroicons/react/24/outline';

interface ShareDialogProps {
  open: boolean;
  sceneId: string;
  sceneName: string;
  onClose: () => void;
}

export function ShareDialog({ open, sceneId, sceneName, onClose }: ShareDialogProps) {
  const [expiresIn, setExpiresIn] = useState<number>(7); // days
  const [permissions, setPermissions] = useState<'view' | 'edit'>('view');
  const [copied, setCopied] = useState<string | null>(null);

  const { data: tokens = [] } = useGetShareTokensQuery(sceneId, { skip: !open });
  const [createToken, { isLoading: isCreating }] = useCreateShareTokenMutation();
  const [revokeToken] = useRevokeShareTokenMutation();

  if (!open) return null;

  const handleCreateToken = async () => {
    try {
      await createToken({
        sceneId,
        expiresInDays: expiresIn,
        permissions,
      }).unwrap();
    } catch (error) {
      console.error('Failed to create share token:', error);
    }
  };

  const handleCopyLink = (token: string) => {
    const baseUrl = window.location.origin;
    const shareUrl = `${baseUrl}/shared/${token}`;
    
    navigator.clipboard.writeText(shareUrl);
    setCopied(token);
    
    setTimeout(() => setCopied(null), 2000);
  };

  const handleRevoke = async (token: string) => {
    if (!confirm('Are you sure you want to revoke this share link?')) {
      return;
    }

    try {
      await revokeToken({ sceneId, token }).unwrap();
    } catch (error) {
      console.error('Failed to revoke token:', error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm"
        onClick={onClose}
      />

      <div className="relative bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl max-w-2xl w-full p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h2 className="text-2xl font-bold text-text-primary">Share Scene</h2>
            <p className="text-sm text-text-secondary mt-1">{sceneName}</p>
          </div>
          <button
            onClick={onClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
          >
            <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        {/* Create new share link */}
        <div className="bg-secondary-bg/70 backdrop-blur-sm rounded-lg p-4 mb-6 border border-border-color">
          <h3 className="text-sm font-medium text-text-primary mb-4">Create Share Link</h3>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <Dropdown
              label="Expires In"
              value={expiresIn}
              onChange={(value) => setExpiresIn(Number(value))}
              options={[
                { value: 1, label: '1 day' },
                { value: 7, label: '7 days' },
                { value: 30, label: '30 days' },
                { value: 90, label: '90 days' },
                { value: 365, label: '1 year' },
              ]}
            />

            <Dropdown
              label="Permissions"
              value={permissions}
              onChange={(value) => setPermissions(value as 'view' | 'edit')}
              options={[
                { value: 'view', label: 'View Only' },
                { value: 'edit', label: 'View & Edit' },
              ]}
            />
          </div>

          <Button
            variant="primary"
            onClick={handleCreateToken}
            disabled={isCreating}
            icon={<LinkIcon className="w-4 h-4" />}
            className="w-full"
          >
            {isCreating ? 'Creating...' : 'Create Share Link'}
          </Button>
        </div>

        {/* Existing share links */}
        <div>
          <h3 className="text-sm font-medium text-text-primary mb-3">
            Active Share Links ({tokens.length})
          </h3>

          {tokens.length === 0 ? (
            <div className="text-center py-8 bg-secondary-bg rounded-lg">
              <LinkIcon className="w-12 h-12 text-text-muted mx-auto mb-2" />
              <p className="text-sm text-text-secondary">No active share links</p>
            </div>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {tokens.map((token) => (
                <div
                  key={token.token}
                  className="bg-secondary-bg rounded-lg p-4 flex items-center justify-between"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs px-2 py-0.5 rounded bg-accent-primary/20 text-accent-primary font-medium">
                        {token.permissions}
                      </span>
                      {token.isExpired && (
                        <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 font-medium">
                          Expired
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-text-secondary">
                      Created {formatDate(token.createdAt)} • Expires {formatDate(token.expiresAt)}
                    </p>
                    <p className="text-xs text-text-muted mt-1 font-mono truncate">
                      {window.location.origin}/shared/{token.token}
                    </p>
                  </div>

                  <div className="flex items-center gap-2 ml-4">
                    <button
                      onClick={() => handleCopyLink(token.token)}
                      className="p-2 rounded-lg hover:bg-primary-bg transition-colors"
                      title="Copy link"
                    >
                      {copied === token.token ? (
                        <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      ) : (
                        <ClipboardDocumentIcon className="w-5 h-5 text-text-secondary" />
                      )}
                    </button>
                    <button
                      onClick={() => handleRevoke(token.token)}
                      className="p-2 rounded-lg hover:bg-red-500/20 transition-colors"
                      title="Revoke link"
                    >
                      <TrashIcon className="w-5 h-5 text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="mt-6 flex justify-end">
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </div>
  );
}
