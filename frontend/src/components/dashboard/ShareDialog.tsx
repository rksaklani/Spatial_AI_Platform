/**
 * ShareDialog Component
 * 
 * Generate share links with expiration and permissions
 * Requirements: F4
 */

import { useState } from 'react';
import { Button, Modal } from '../common';

interface ShareDialogProps {
  sceneId: string;
  sceneName: string;
  isOpen: boolean;
  onClose: () => void;
  onShare?: (expiresIn: number, permissions: string[]) => Promise<string>;
}

export function ShareDialog({
  sceneId,
  sceneName,
  isOpen,
  onClose,
  onShare,
}: ShareDialogProps) {
  const [expiresIn, setExpiresIn] = useState<number>(7); // days
  const [permissions, setPermissions] = useState<string[]>(['view']);
  const [shareLink, setShareLink] = useState<string>('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [copied, setCopied] = useState(false);

  const handleGenerate = async () => {
    if (!onShare) return;

    setIsGenerating(true);
    try {
      const link = await onShare(expiresIn, permissions);
      setShareLink(link);
    } catch (error) {
      console.error('Failed to generate share link:', error);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopy = async () => {
    if (!shareLink) return;

    try {
      await navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error('Failed to copy link:', error);
    }
  };

  const togglePermission = (permission: string) => {
    setPermissions((prev) =>
      prev.includes(permission)
        ? prev.filter((p) => p !== permission)
        : [...prev, permission]
    );
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Share Scene">
      <div className="space-y-6">
        {/* Scene Info */}
        <div className="bg-surface-base rounded-lg p-4">
          <p className="text-sm text-text-secondary mb-1">Sharing</p>
          <p className="text-base font-medium text-text-primary">{sceneName}</p>
        </div>

        {/* Expiration */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Link Expiration
          </label>
          <select
            value={expiresIn}
            onChange={(e) => setExpiresIn(Number(e.target.value))}
            className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
          >
            <option value={1}>1 day</option>
            <option value={7}>7 days</option>
            <option value={30}>30 days</option>
            <option value={90}>90 days</option>
            <option value={365}>1 year</option>
            <option value={-1}>Never</option>
          </select>
        </div>

        {/* Permissions */}
        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Permissions
          </label>
          <div className="space-y-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={permissions.includes('view')}
                onChange={() => togglePermission('view')}
                className="w-4 h-4 text-accent-primary bg-surface-base border-border-subtle rounded focus:ring-accent-primary"
              />
              <span className="text-sm text-text-primary">View scene</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={permissions.includes('annotate')}
                onChange={() => togglePermission('annotate')}
                className="w-4 h-4 text-accent-primary bg-surface-base border-border-subtle rounded focus:ring-accent-primary"
              />
              <span className="text-sm text-text-primary">Create annotations</span>
            </label>
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={permissions.includes('download')}
                onChange={() => togglePermission('download')}
                className="w-4 h-4 text-accent-primary bg-surface-base border-border-subtle rounded focus:ring-accent-primary"
              />
              <span className="text-sm text-text-primary">Download scene data</span>
            </label>
          </div>
        </div>

        {/* Generate Button */}
        {!shareLink && (
          <Button
            variant="primary"
            onClick={handleGenerate}
            disabled={isGenerating || permissions.length === 0}
            className="w-full"
          >
            {isGenerating ? 'Generating...' : 'Generate Share Link'}
          </Button>
        )}

        {/* Share Link */}
        {shareLink && (
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Share Link
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={shareLink}
                readOnly
                className="flex-1 px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary text-sm font-mono"
              />
              <Button
                variant={copied ? 'success' : 'secondary'}
                onClick={handleCopy}
              >
                {copied ? (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                ) : (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
                  </svg>
                )}
              </Button>
            </div>
            <p className="text-xs text-text-secondary mt-2">
              {expiresIn === -1
                ? 'This link never expires'
                : `This link expires in ${expiresIn} day${expiresIn > 1 ? 's' : ''}`}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-4 border-t border-border-subtle">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            {shareLink ? 'Done' : 'Cancel'}
          </Button>
          {shareLink && (
            <Button
              variant="secondary"
              onClick={() => {
                setShareLink('');
                setCopied(false);
              }}
              className="flex-1"
            >
              Generate New Link
            </Button>
          )}
        </div>
      </div>
    </Modal>
  );
}
