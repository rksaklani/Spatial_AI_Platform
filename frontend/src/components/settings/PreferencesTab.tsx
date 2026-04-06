/**
 * PreferencesTab Component
 * 
 * User preferences settings tab
 * Requirements: 29.3, 31.4, 31.6
 */

import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { setTheme, setLanguage, updateViewerSettings } from '../../store/slices/preferencesSlice';
import { Dropdown } from '../common';

export function PreferencesTab() {
  const dispatch = useAppDispatch();
  const preferences = useAppSelector((state) => state.preferences);

  return (
    <div className="space-y-8">
      {/* Appearance */}
      <div>
        <h3 className="text-lg font-medium text-text-primary mb-4">Appearance</h3>
        <div className="space-y-4 max-w-2xl">
          <Dropdown
            label="Theme"
            value={preferences.theme}
            onChange={(value) => dispatch(setTheme(value as 'light' | 'dark'))}
            options={[
              { value: 'dark', label: 'Dark' },
              { value: 'light', label: 'Light' },
            ]}
          />

          <Dropdown
            label="Language"
            value={preferences.language}
            onChange={(value) => dispatch(setLanguage(value))}
            options={[
              { value: 'en', label: 'English' },
              { value: 'es', label: 'Español' },
              { value: 'fr', label: 'Français' },
              { value: 'de', label: 'Deutsch' },
            ]}
          />
        </div>
      </div>

      {/* Viewer Settings */}
      <div className="pt-8 border-t border-border-subtle">
        <h3 className="text-lg font-medium text-text-primary mb-4">3D Viewer</h3>
        <div className="space-y-4 max-w-2xl">
          <Dropdown
            label="Default Rendering Mode"
            value={preferences.viewerSettings.defaultRenderingMode}
            onChange={(value) => dispatch(updateViewerSettings({ 
              defaultRenderingMode: value as 'client' | 'server' 
            }))}
            options={[
              { value: 'client', label: 'Client-side' },
              { value: 'server', label: 'Server-side' },
            ]}
          />

          <Dropdown
            label="Quality"
            value={preferences.viewerSettings.quality}
            onChange={(value) => dispatch(updateViewerSettings({ 
              quality: value as 'low' | 'medium' | 'high' 
            }))}
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
            ]}
          />

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.viewerSettings.showFps}
              onChange={(e) => dispatch(updateViewerSettings({ showFps: e.target.checked }))}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Show FPS counter</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.viewerSettings.showCoordinates}
              onChange={(e) => dispatch(updateViewerSettings({ showCoordinates: e.target.checked }))}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Show coordinates</span>
          </label>

          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={preferences.viewerSettings.autoRotate}
              onChange={(e) => dispatch(updateViewerSettings({ autoRotate: e.target.checked }))}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Auto-rotate on load</span>
          </label>
        </div>
      </div>
    </div>
  );
}
