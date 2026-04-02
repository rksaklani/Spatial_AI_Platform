/**
 * Password Protected Share Dialog Component
 * 
 * Allows users to create password-protected public share links
 */

import React, { useState } from 'react';
import { Modal, Button } from '../common';
import { LockClosedIcon, ClipboardDocumentIcon, CheckIcon } from '@heroicons/react/24/outline';

interface PasswordProtectedShareDialogProps {
  isOpen: boolean;
  onClose: () => void;
  sceneId: string;
  sceneName: string;
}

export const PasswordProtectedShareDialog: React.FC<PasswordProtectedShareDialogProps> = ({
  isOpen,
  onClose,
  sceneId,
  sceneName,
}) => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [expiresIn, setExpiresIn] = useState<number>(7); // days
  const [shareLink, setShareLink] = useState<string>('');
  const [copied, setCopied] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);

  const handleGenerateLink = async () => {
    if (password !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }

    if (password.length < 6) {
      alert('Password must be at least 6 characters');
      return;
    }

    setIsGenerating(true);

    try {
      const response = await fetch(`/api/v1/scenes/${sceneId}/share/protected`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify({
          password,
          expires_in_days: expiresIn,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to create protected share link');
      }

      const data = await response.json();
      setShareLink(data.share_url);
    } catch (error) {
      console.error('Failed to generate share link:', error);
      alert('Failed to generate share link');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(shareLink);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleReset = () => {
    setPassword('');
    setConfirmPassword('');
    setShareLink('');
    setExpiresIn(7);
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Password Protected Share">
      <div className="space-y-6">
        {/* Scene Info */}
        <div className="bg-surface-elevated rounded-lg p-4">
          <p className="text-sm text-text-secondary">Scene</p>
          <p className="text-lg font-semibold text-text-primary">{sceneName}</p>
        </div>

        {!shareLink ? (
          <>
            {/* Password Input */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-text-primary mb-2">
                Password
              </label>
              <input
                type="password"
                id="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Enter password"
                minLength={6}
              />
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="confirm-password" className="block text-sm font-medium text-text-primary mb-2">
                Confirm Password
              </label>
              <input
                type="password"
                id="confirm-password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Confirm password"
                minLength={6}
              />
            </div>

            {/* Expiration */}
            <div>
              <label htmlFor="expires" className="block text-sm font-medium text-text-primary mb-2">
                Link Expires In
              </label>
              <select
                id="expires"
                value={expiresIn}
                onChange={(e) => setExpiresIn(Number(e.target.value))}
                className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
              >
                <option value={1}>1 day</option>
                <option value={7}>7 days</option>
                <option value={30}>30 days</option>
                <option value={90}>90 days</option>
                <option value={365}>1 year</option>
              </select>
            </div>

            {/* Generate Button */}
            <Button
              variant="primary"
              onClick={handleGenerateLink}
              disabled={isGenerating || !password || !confirmPassword}
              icon={<LockClosedIcon className="w-5 h-5" />}
              className="w-full"
            >
              {isGenerating ? 'Generating...' : 'Generate Protected Link'}
            </Button>
          </>
        ) : (
          <>
            {/* Success Message */}
            <div className="bg-green-500/10 border border-green-500/20 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <CheckIcon className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="text-sm font-medium text-green-400">Protected link created!</p>
                  <p className="text-xs text-text-secondary mt-1">
                    Share this link and password with your collaborators
                  </p>
                </div>
              </div>
            </div>

            {/* Share Link */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Share Link
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={shareLink}
                  readOnly
                  className="flex-1 px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary font-mono text-sm"
                />
                <Button
                  variant="secondary"
                  onClick={handleCopyLink}
                  icon={copied ? <CheckIcon className="w-5 h-5" /> : <ClipboardDocumentIcon className="w-5 h-5" />}
                >
                  {copied ? 'Copied!' : 'Copy'}
                </Button>
              </div>
            </div>

            {/* Password Display */}
            <div>
              <label className="block text-sm font-medium text-text-primary mb-2">
                Password
              </label>
              <div className="px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary font-mono">
                {password}
              </div>
              <p className="text-xs text-text-muted mt-1">
                Share this password separately for security
              </p>
            </div>

            {/* Expiration Info */}
            <div className="bg-surface-elevated/50 border border-border-subtle rounded-lg p-3">
              <p className="text-sm text-text-secondary">
                This link will expire in {expiresIn} {expiresIn === 1 ? 'day' : 'days'}
              </p>
            </div>

            {/* Create Another Button */}
            <Button
              variant="secondary"
              onClick={handleReset}
              className="w-full"
            >
              Create Another Link
            </Button>
          </>
        )}

        {/* Close Button */}
        <div className="flex gap-3 pt-4 border-t border-border-subtle">
          <Button variant="ghost" onClick={onClose} className="flex-1">
            {shareLink ? 'Done' : 'Cancel'}
          </Button>
        </div>
      </div>
    </Modal>
  );
};
