/**
 * PreferencesTab Component
 * 
 * User preferences settings tab
 * Requirements: 29.3, 31.4, 31.6
 */

import { useAppSelector, useAppDispatch } from '../../store/hooks';
import { setTheme, setLanguage, updateViewerSettings } from '../../store/slices/preferencesSlice';

export function PreferencesTab() {
  const dispatch = useAppDispatch();
  const preferences = useAppSelector((state) => state.preferences);

  return (
    <div className="space-y-8">
      {/* Appearance */}
      <div>
        <h3 className="text-lg font-medium text-text-primary mb-4">Appearance</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Theme
            </label>
            <select
              value={preferences.theme}
              onChange={(e) => dispatch(setTheme(e.target.value as 'light' | 'dark'))}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="dark">Dark</option>
              <option value="light">Light</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Language
            </label>
            <select
              value={preferences.language}
              onChange={(e) => dispatch(setLanguage(e.target.value))}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="en">English</option>
              <option value="es">Español</option>
              <option value="fr">Français</option>
              <option value="de">Deutsch</option>
            </select>
          </div>
        </div>
      </div>

      {/* Viewer Settings */}
      <div className="pt-8 border-t border-border-subtle">
        <h3 className="text-lg font-medium text-text-primary mb-4">3D Viewer</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Default Rendering Mode
            </label>
            <select
              value={preferences.viewerSettings.defaultRenderingMode}
              onChange={(e) => dispatch(updateViewerSettings({ 
                defaultRenderingMode: e.target.value as 'client' | 'server' 
              }))}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="client">Client-side</option>
              <option value="server">Server-side</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-secondary mb-2">
              Quality
            </label>
            <select
              value={preferences.viewerSettings.quality}
              onChange={(e) => dispatch(updateViewerSettings({ 
                quality: e.target.value as 'low' | 'medium' | 'high' 
              }))}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
            </select>
          </div>

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
