/**
 * ComparisonControls Component
 * 
 * Controls for scene comparison mode
 * Requirements: 12.5, 12.6, 12.7
 */

import { Button } from '../common';

interface ComparisonControlsProps {
  scenes: Array<{ id: string; name: string }>;
  selectedSceneA: string | null;
  selectedSceneB: string | null;
  onSceneASelect: (sceneId: string) => void;
  onSceneBSelect: (sceneId: string) => void;
  mode: 'side-by-side' | 'temporal';
  onModeChange: (mode: 'side-by-side' | 'temporal') => void;
  cameraSyncEnabled: boolean;
  onCameraSyncToggle: () => void;
  differenceVisualizationEnabled: boolean;
  onDifferenceVisualizationToggle: () => void;
}

export function ComparisonControls({
  scenes,
  selectedSceneA,
  selectedSceneB,
  onSceneASelect,
  onSceneBSelect,
  mode,
  onModeChange,
  cameraSyncEnabled,
  onCameraSyncToggle,
  differenceVisualizationEnabled,
  onDifferenceVisualizationToggle,
}: ComparisonControlsProps) {
  return (
    <div className="absolute top-4 left-1/2 -translate-x-1/2 z-10">
      <div className="bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg shadow-lg p-4 min-w-[500px]">
        {/* Scene Selectors */}
        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-2">
              Scene A
            </label>
            <select
              value={selectedSceneA || ''}
              onChange={(e) => onSceneASelect(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">Select scene...</option>
              {scenes.map((scene) => (
                <option key={scene.id} value={scene.id}>
                  {scene.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-xs font-medium text-text-secondary mb-2">
              Scene B
            </label>
            <select
              value={selectedSceneB || ''}
              onChange={(e) => onSceneBSelect(e.target.value)}
              className="w-full px-3 py-2 bg-surface-base border border-border-subtle rounded-lg text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">Select scene...</option>
              {scenes.map((scene) => (
                <option key={scene.id} value={scene.id}>
                  {scene.name}
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-text-secondary mb-2">
            Comparison Mode
          </label>
          <div className="flex gap-2">
            <Button
              variant={mode === 'side-by-side' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => onModeChange('side-by-side')}
              className="flex-1"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 4v16M15 4v16" />
              </svg>
              Side by Side
            </Button>
            <Button
              variant={mode === 'temporal' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => onModeChange('temporal')}
              className="flex-1"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Temporal
            </Button>
          </div>
        </div>

        {/* Options */}
        <div className="space-y-2">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={cameraSyncEnabled}
              onChange={onCameraSyncToggle}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Sync camera movements</span>
          </label>

          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={differenceVisualizationEnabled}
              onChange={onDifferenceVisualizationToggle}
              className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary focus:ring-2 focus:ring-accent-primary"
            />
            <span className="text-sm text-text-primary">Show differences</span>
          </label>
        </div>
      </div>
    </div>
  );
}
