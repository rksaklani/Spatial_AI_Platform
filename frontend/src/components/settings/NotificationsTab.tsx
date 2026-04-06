/**
 * NotificationsTab Component
 * 
 * Notification preferences settings tab
 * Requirements: 31.5
 */

import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { updateNotificationSettings } from '../../store/slices/preferencesSlice';

export function NotificationsTab() {
  const dispatch = useAppDispatch();
  const settings = useAppSelector((state) => state.preferences.notificationSettings);

  return (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-medium text-text-primary mb-4">Notification Preferences</h3>
        <p className="text-sm text-text-secondary mb-6">
          Choose which notifications you want to receive
        </p>

        <div className="space-y-4 max-w-2xl">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.processingComplete}
              onChange={(e) => dispatch(updateNotificationSettings({ 
                processingComplete: e.target.checked 
              }))}
              className="mt-1 w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <div>
              <p className="text-sm font-medium text-text-primary">Processing Complete</p>
              <p className="text-xs text-text-secondary mt-1">
                Get notified when scene processing is complete
              </p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.mentions}
              onChange={(e) => dispatch(updateNotificationSettings({ 
                mentions: e.target.checked 
              }))}
              className="mt-1 w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <div>
              <p className="text-sm font-medium text-text-primary">Mentions</p>
              <p className="text-xs text-text-secondary mt-1">
                Get notified when someone mentions you in annotations
              </p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.collaborationUpdates}
              onChange={(e) => dispatch(updateNotificationSettings({ 
                collaborationUpdates: e.target.checked 
              }))}
              className="mt-1 w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <div>
              <p className="text-sm font-medium text-text-primary">Collaboration Updates</p>
              <p className="text-xs text-text-secondary mt-1">
                Get notified about changes in shared scenes
              </p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={settings.email}
              onChange={(e) => dispatch(updateNotificationSettings({ 
                email: e.target.checked 
              }))}
              className="mt-1 w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <div>
              <p className="text-sm font-medium text-text-primary">Email Notifications</p>
              <p className="text-xs text-text-secondary mt-1">
                Receive notifications via email
              </p>
            </div>
          </label>
        </div>
      </div>
    </div>
  );
}
