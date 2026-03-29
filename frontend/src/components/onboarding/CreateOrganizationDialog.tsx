/**
 * Dialog for creating a new organization
 */

import React, { useState } from 'react';
import { Modal, Button } from '../common';
import { useCreateOrganizationMutation } from '../../store/api/organizationApi';
import { useToast } from '../../hooks/useToast';

interface CreateOrganizationDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: () => void;
}

export const CreateOrganizationDialog: React.FC<CreateOrganizationDialogProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [createOrganization, { isLoading }] = useCreateOrganizationMutation();
  const { showToast } = useToast();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!name.trim()) {
      showToast('Please enter an organization name', 'error');
      return;
    }

    try {
      await createOrganization({
        name: name.trim(),
        description: description.trim() || undefined,
      }).unwrap();

      showToast('Organization created successfully!', 'success');
      setName('');
      setDescription('');
      onSuccess?.();
      onClose();
    } catch (error: any) {
      showToast(error?.data?.detail || 'Failed to create organization', 'error');
    }
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Organization">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label htmlFor="org-name" className="block text-sm font-medium text-text-primary mb-1">
            Organization Name *
          </label>
          <input
            id="org-name"
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary"
            placeholder="My Company"
            required
            maxLength={255}
          />
        </div>

        <div>
          <label htmlFor="org-description" className="block text-sm font-medium text-text-primary mb-1">
            Description (optional)
          </label>
          <textarea
            id="org-description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-primary resize-none"
            placeholder="Brief description of your organization"
            rows={3}
          />
        </div>

        <div className="bg-surface-elevated/50 border border-border-subtle rounded-lg p-3">
          <p className="text-sm text-text-secondary">
            You'll get a 15-day free trial with:
          </p>
          <ul className="mt-2 space-y-1 text-sm text-text-secondary">
            <li>• 1 seat</li>
            <li>• 3 scenes</li>
            <li>• 5 GB storage</li>
          </ul>
        </div>

        <div className="flex gap-3 justify-end pt-2">
          <Button
            type="button"
            variant="secondary"
            onClick={onClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button
            type="submit"
            variant="primary"
            disabled={isLoading || !name.trim()}
          >
            {isLoading ? 'Creating...' : 'Create Organization'}
          </Button>
        </div>
      </form>
    </Modal>
  );
};
