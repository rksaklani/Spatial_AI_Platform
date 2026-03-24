import React, { useState, useEffect } from 'react';
import { Button } from '../common/Button';
import { useUpdateSceneMutation } from '../../store/api/sceneApi';
import type { SceneMetadata } from '../../types/scene.types';

export interface SceneEditDialogProps {
  open: boolean;
  scene: SceneMetadata | null;
  onClose: () => void;
  onSuccess?: () => void;
}

/**
 * SceneEditDialog component - modal for editing scene metadata
 * 
 * Features:
 * - Edit scene name and description
 * - Toggle public/private status
 * - Input validation
 * - API integration with error handling
 * - Glassmorphism modal design
 * 
 * Requirements: 3.7
 */
export const SceneEditDialog: React.FC<SceneEditDialogProps> = ({
  open,
  scene,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  const [errors, setErrors] = useState<{ name?: string; description?: string }>({});
  
  const [updateScene, { isLoading, error: apiError }] = useUpdateSceneMutation();

  // Initialize form with scene data when dialog opens
  useEffect(() => {
    if (scene) {
      setName(scene.name);
      setDescription(''); // SceneMetadata doesn't have description yet, will be added
      setIsPublic(false); // SceneMetadata doesn't have isPublic yet, will be added
      setErrors({});
    }
  }, [scene]);

  if (!open || !scene) return null;

  const validateForm = (): boolean => {
    const newErrors: { name?: string; description?: string } = {};

    // Validate name
    if (!name.trim()) {
      newErrors.name = 'Scene name is required';
    } else if (name.length > 255) {
      newErrors.name = 'Scene name must be less than 255 characters';
    }

    // Validate description (optional, but limit length if provided)
    if (description && description.length > 1000) {
      newErrors.description = 'Description must be less than 1000 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    try {
      await updateScene({
        sceneId: scene.sceneId,
        updates: {
          name: name.trim(),
          // description and isPublic will be added when backend supports them
        },
      }).unwrap();

      // Success
      if (onSuccess) {
        onSuccess();
      }
      handleClose();
    } catch (err) {
      // Error is handled by RTK Query and displayed below
      console.error('Failed to update scene:', err);
    }
  };

  const handleClose = () => {
    setName('');
    setDescription('');
    setIsPublic(false);
    setErrors({});
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black bg-opacity-60 backdrop-blur-sm"
        onClick={handleClose}
      />

      {/* Modal */}
      <div className="relative bg-glass-bg backdrop-blur-xl rounded-xl border border-border-color shadow-2xl max-w-lg w-full p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-text-primary">Edit Scene</h2>
          <button
            onClick={handleClose}
            className="text-text-secondary hover:text-text-primary transition-colors"
            aria-label="Close dialog"
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

        {/* Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          {/* Name field */}
          <div>
            <label htmlFor="scene-name" className="block text-sm font-medium text-text-primary mb-2">
              Scene Name <span className="text-accent-primary">*</span>
            </label>
            <input
              id="scene-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className={`w-full px-4 py-3 bg-secondary-bg border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 transition-all ${
                errors.name
                  ? 'border-red-500 focus:ring-red-500/50'
                  : 'border-border-color focus:ring-accent-primary/50'
              }`}
              placeholder="Enter scene name"
              maxLength={255}
              disabled={isLoading}
            />
            {errors.name && (
              <p className="mt-1 text-sm text-red-400">{errors.name}</p>
            )}
            <p className="mt-1 text-xs text-text-muted">
              {name.length}/255 characters
            </p>
          </div>

          {/* Description field */}
          <div>
            <label htmlFor="scene-description" className="block text-sm font-medium text-text-primary mb-2">
              Description
            </label>
            <textarea
              id="scene-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className={`w-full px-4 py-3 bg-secondary-bg border rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 transition-all resize-none ${
                errors.description
                  ? 'border-red-500 focus:ring-red-500/50'
                  : 'border-border-color focus:ring-accent-primary/50'
              }`}
              placeholder="Add a description (optional)"
              maxLength={1000}
              disabled={isLoading}
            />
            {errors.description && (
              <p className="mt-1 text-sm text-red-400">{errors.description}</p>
            )}
            <p className="mt-1 text-xs text-text-muted">
              {description.length}/1000 characters
            </p>
          </div>

          {/* Public/Private toggle */}
          <div>
            <label className="flex items-center justify-between p-4 bg-secondary-bg border border-border-color rounded-lg cursor-pointer hover:border-accent-primary/50 transition-colors">
              <div className="flex-1">
                <div className="flex items-center">
                  <svg
                    className="h-5 w-5 mr-2 text-text-secondary"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <span className="text-sm font-medium text-text-primary">
                    Make scene public
                  </span>
                </div>
                <p className="text-xs text-text-secondary mt-1 ml-7">
                  Anyone with the link can view this scene
                </p>
              </div>
              <div className="ml-4">
                <input
                  type="checkbox"
                  checked={isPublic}
                  onChange={(e) => setIsPublic(e.target.checked)}
                  className="sr-only"
                  disabled={isLoading}
                />
                <div
                  className={`relative w-11 h-6 rounded-full transition-colors ${
                    isPublic ? 'bg-accent-primary' : 'bg-hover-bg'
                  }`}
                >
                  <div
                    className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full transition-transform ${
                      isPublic ? 'translate-x-5' : 'translate-x-0'
                    }`}
                  />
                </div>
              </div>
            </label>
          </div>

          {/* API Error message */}
          {apiError && (
            <div className="p-3 bg-red-500/20 border border-red-500/30 rounded-lg">
              <p className="text-sm text-red-400">
                {'data' in apiError && typeof apiError.data === 'object' && apiError.data && 'detail' in apiError.data
                  ? String(apiError.data.detail)
                  : 'Failed to update scene. Please try again.'}
              </p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={handleClose}
              disabled={isLoading}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              disabled={isLoading}
              loading={isLoading}
              className="flex-1"
            >
              {isLoading ? 'Saving...' : 'Save Changes'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};
