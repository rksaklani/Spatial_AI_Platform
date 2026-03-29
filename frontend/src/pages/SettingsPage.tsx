/**
 * Settings page component - user profile and preferences
 * 
 * Requirements: 31.1
 */

import { useState } from 'react';
import { ProfileTab } from '../components/settings/ProfileTab';
import { PreferencesTab } from '../components/settings/PreferencesTab';
import { NotificationsTab } from '../components/settings/NotificationsTab';

type TabType = 'profile' | 'preferences' | 'notifications';

export function SettingsPage() {
  const [activeTab, setActiveTab] = useState<TabType>('profile');

  const tabs: Array<{ id: TabType; label: string }> = [
    { id: 'profile', label: 'Profile' },
    { id: 'preferences', label: 'Preferences' },
    { id: 'notifications', label: 'Notifications' },
  ];

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-3xl font-bold text-text-primary mb-2">Settings</h1>
        <p className="text-text-secondary">Manage your profile and preferences</p>
      </div>
      
      {/* Tabs */}
      <div className="border-b border-border-subtle mb-6">
        <div className="flex gap-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`pb-3 px-1 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-accent-primary text-accent-primary'
                  : 'border-transparent text-text-secondary hover:text-text-primary'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div className="bg-surface-elevated rounded-xl p-6 border border-border-subtle">
        {activeTab === 'profile' && <ProfileTab />}
        {activeTab === 'preferences' && <PreferencesTab />}
        {activeTab === 'notifications' && <NotificationsTab />}
      </div>
    </div>
  );
}

