/**
 * AnnotationToolbar Component
 * 
 * Toolbar for creating and managing annotations in the 3D viewer
 * Requirements: 9.1
 */

import { useState } from 'react';
import { Button } from '../common';

type AnnotationType = 'point' | 'line' | 'area' | 'text';
type AnnotationMode = 'view' | 'create' | 'edit';

interface AnnotationToolbarProps {
  mode: AnnotationMode;
  onModeChange: (mode: AnnotationMode) => void;
  selectedType: AnnotationType | null;
  onTypeSelect: (type: AnnotationType) => void;
  selectedAnnotationId: string | null;
  onEdit: () => void;
  onDelete: () => void;
  selectedColor: string;
  onColorChange: (color: string) => void;
  pointsCollected?: number;
}

const ANNOTATION_COLORS = [
  '#FF6B6B', // Red
  '#4ECDC4', // Teal
  '#45B7D1', // Blue
  '#FFA07A', // Orange
  '#98D8C8', // Mint
  '#F7DC6F', // Yellow
  '#BB8FCE', // Purple
  '#85C1E2', // Light Blue
];

export function AnnotationToolbar({
  mode,
  onModeChange,
  selectedType,
  onTypeSelect,
  selectedAnnotationId,
  onEdit,
  onDelete,
  selectedColor,
  onColorChange,
  pointsCollected = 0,
}: AnnotationToolbarProps) {
  const [showColorPicker, setShowColorPicker] = useState(false);

  return (
    <div className="absolute bottom-24 left-1/2 -translate-x-1/2 z-10">
      <div className="bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg shadow-lg p-3">
        <div className="flex items-center gap-3">
          {/* Mode Toggle */}
          <div className="flex gap-1 border-r border-border-subtle pr-3">
            <Button
              variant={mode === 'view' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => onModeChange('view')}
              aria-label="View mode"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            </Button>
            <Button
              variant={mode === 'create' ? 'primary' : 'ghost'}
              size="sm"
              onClick={() => onModeChange('create')}
              aria-label="Create mode"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </Button>
          </div>

          {/* Annotation Type Buttons */}
          {mode === 'create' && (
            <div className="flex gap-1 border-r border-border-subtle pr-3">
              <Button
                variant={selectedType === 'point' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => onTypeSelect('point')}
                aria-label="Point annotation"
                title="Point"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="3" strokeWidth={2} />
                </svg>
              </Button>
              <Button
                variant={selectedType === 'line' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => onTypeSelect('line')}
                aria-label="Line annotation"
                title="Line"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 20l16-16" />
                </svg>
              </Button>
              <Button
                variant={selectedType === 'area' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => onTypeSelect('area')}
                aria-label="Area annotation"
                title="Area"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5h16M4 12h16M4 19h16" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5v14h16V5" />
                </svg>
              </Button>
              <Button
                variant={selectedType === 'text' ? 'primary' : 'ghost'}
                size="sm"
                onClick={() => onTypeSelect('text')}
                aria-label="Text annotation"
                title="Text"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 8h10M7 12h4m1 8l-4-4H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-3l-4 4z" />
                </svg>
              </Button>
            </div>
          )}

          {/* Color Picker */}
          {mode === 'create' && (
            <div className="relative border-r border-border-subtle pr-3">
              <button
                onClick={() => setShowColorPicker(!showColorPicker)}
                className="w-8 h-8 rounded border-2 border-border-subtle hover:border-accent-primary transition-colors"
                style={{ backgroundColor: selectedColor }}
                aria-label="Select color"
                title="Color"
              />
              {showColorPicker && (
                <div className="absolute bottom-full mb-2 left-0 bg-surface-elevated border border-border-subtle rounded-lg shadow-lg p-2">
                  <div className="grid grid-cols-4 gap-2">
                    {ANNOTATION_COLORS.map((color) => (
                      <button
                        key={color}
                        onClick={() => {
                          onColorChange(color);
                          setShowColorPicker(false);
                        }}
                        className="w-8 h-8 rounded border-2 hover:scale-110 transition-transform"
                        style={{
                          backgroundColor: color,
                          borderColor: color === selectedColor ? '#fff' : 'transparent',
                        }}
                        aria-label={`Select ${color}`}
                      />
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Edit/Delete Buttons */}
          {selectedAnnotationId && (
            <div className="flex gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={onEdit}
                aria-label="Edit annotation"
                title="Edit"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={onDelete}
                aria-label="Delete annotation"
                title="Delete"
                className="text-status-error hover:text-status-error"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </Button>
            </div>
          )}
        </div>

        {/* Instructions */}
        {mode === 'create' && selectedType && (
          <div className="mt-2 pt-2 border-t border-border-subtle">
            <p className="text-xs text-text-secondary">
              {selectedType === 'point' && 'Click on the scene to place a point'}
              {selectedType === 'line' && `Click to add points (${pointsCollected} added), double-click to finish`}
              {selectedType === 'area' && `Click to add points (${pointsCollected} added), double-click to close polygon`}
              {selectedType === 'text' && 'Click on the scene to place text'}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
