/**
 * ProfileTab Component
 * 
 * User profile settings tab
 * Requirements: 31.2, 31.3, 31.7
 */

import { useState } from 'react';
import { useAppSelector } from '../../store/hooks';
import { Button } from '../common';

export function ProfileTab() {
  const user = useAppSelector((state) => state.auth.user);
  
  const [name, setName] = useState(user?.name || '');
  const [email, setEmail] = useState(user?.email || '');
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [isSavingProfile, setIsSavingProfile] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  const handleSaveProfile = async () => {
    setIsSavingProfile(true);
    try {
      // TODO: Implement with user API
      console.log('Save profile:', { name, email });
      await new Promise(resolve => setTimeout(resolve, 1000));
    } finally {
      setIsSavingProfile(false);
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      alert('Passwords do not match');
      return;
    }
    
    setIsChangingPassword(true);
    try {
      // TODO: Implement with user API
      console.log('Change password');
      await new Promise(resolve => setTimeout(resolve, 1000));
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } finally {
      setIsChangingPassword(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Profile Information */}
      <div>
        <h3 className="text-lg font-medium text-text-primary mb-4">Profile Information</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Full Name
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>

          <Button
            variant="primary"
            onClick={handleSaveProfile}
            disabled={isSavingProfile}
          >
            {isSavingProfile ? 'Saving...' : 'Save Changes'}
          </Button>
        </div>
      </div>

      {/* Change Password */}
      <div className="pt-8 border-t border-border-subtle">
        <h3 className="text-lg font-medium text-text-primary mb-4">Change Password</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>

          <Button
            variant="primary"
            onClick={handleChangePassword}
            disabled={isChangingPassword || !currentPassword || !newPassword || !confirmPassword}
          >
            {isChangingPassword ? 'Changing...' : 'Change Password'}
          </Button>
        </div>
      </div>
    </div>
  );
}
