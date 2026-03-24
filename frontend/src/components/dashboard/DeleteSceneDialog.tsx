import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import type { SceneMetadata } from '../../types/scene.types';

export interface DeleteSceneDialogProps {
  open: boolean;
  scene: SceneMetadata | null;
  onClose: () => void;
  onConfirm: (sceneId: string) => Promise<void>;
}

/**
 * DeleteSceneDialog component - confirmation dialog for scene deletion
 * 
 * Features:
 * - Scene name verification for safety
 * - Clear warning message
 * - Disabled confirm button until name matches
 * - Loading state during deletion
 * 
 * Requirements: 3.8 - Delete scenes with confirmation dialog
 */
export const DeleteSceneDialog: React.FC<DeleteSceneDialogProps> = ({
  open,
  scene,
  onClose,
  onConfirm,
}) => {
  const [nameInput, setNameInput] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);

  // Reset state when dialog opens/closes
  React.useEffect(() => {
    if (open) {
      setNameInput('');
      setIsDeleting(false);
    }
  }, [open]);

  if (!scene) return null;

  const isNameMatch = nameInput === scene.name;

  const handleConfirm = async () => {
    if (!isNameMatch || isDeleting) return;

    setIsDeleting(true);
    try {
      await onConfirm(scene.sceneId);
      onClose();
    } catch (error) {
      console.error('Delete failed:', error);
      setIsDeleting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && isNameMatch && !isDeleting) {
      handleConfirm();
    }
  };

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="Delete Scene"
      size="md"
      closeOnBackdrop={!isDeleting}
      footer={
        <div className="flex gap-3 justify-end">
          <Button
            variant="secondary"
            onClick={onClose}
            disabled={isDeleting}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleConfirm}
            disabled={!isNameMatch || isDeleting}
            loading={isDeleting}
          >
            Delete Scene
          </Button>
        </div>
      }
    >
      <div className="space-y-4">
        {/* Warning message */}
        <div className="flex items-start gap-3 p-4 bg-red-500/10 border border-red-500/30 rounded-lg">
          <svg
            className="h-6 w-6 text-red-400 flex-shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div>
            <h3 className="text-red-400 font-semibold mb-1">
              This action cannot be undone
            </h3>
            <p className="text-text-secondary text-sm">
              This will permanently delete the scene, including all associated data,
              annotations, and processing results.
            </p>
          </div>
        </div>

        {/* Scene info */}
        <div className="space-y-2">
          <p className="text-text-primary">
            You are about to delete:
          </p>
          <div className="p-3 bg-hover-bg rounded-lg border border-border-color">
            <p className="text-text-primary font-semibold">{scene.name}</p>
            <p className="text-text-muted text-sm mt-1">
              Scene ID: {scene.sceneId}
            </p>
          </div>
        </div>

        {/* Name verification */}
        <div className="space-y-2">
          <label htmlFor="scene-name-input" className="block text-text-primary text-sm">
            To confirm, type the scene name:{' '}
            <span className="font-semibold text-accent-primary">{scene.name}</span>
          </label>
          <input
            id="scene-name-input"
            type="text"
            value={nameInput}
            onChange={(e) => setNameInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter scene name"
            disabled={isDeleting}
            className="
              w-full px-4 py-2 
              bg-primary-bg border border-border-color rounded-lg
              text-text-primary placeholder-text-muted
              focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-transparent
              disabled:opacity-50 disabled:cursor-not-allowed
              transition-all duration-200
            "
            autoFocus
          />
          {nameInput && !isNameMatch && (
            <p className="text-red-400 text-sm">
              Scene name does not match
            </p>
          )}
        </div>
      </div>
    </Modal>
  );
};
