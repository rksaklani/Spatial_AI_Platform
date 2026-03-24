/**
 * TourList Component
 * 
 * Displays available guided tours for a scene
 * Requirements: 11.4
 */

import { Button } from '../common';

interface CameraKeyframe {
  position: [number, number, number];
  rotation: [number, number, number, number];
  timestamp: number;
}

interface Narration {
  timestamp: number;
  text: string;
}

interface GuidedTour {
  id: string;
  scene_id: string;
  user_id: string;
  name: string;
  camera_path: CameraKeyframe[];
  narration: Narration[];
  duration: number;
  created_at: string;
}

interface TourListProps {
  tours: GuidedTour[];
  currentUserId: string;
  onPlay: (tourId: string) => void;
  onEdit: (tourId: string) => void;
  onDelete: (tourId: string) => void;
  onCreate: () => void;
  loading?: boolean;
}

export function TourList({
  tours,
  currentUserId,
  onPlay,
  onEdit,
  onDelete,
  onCreate,
  loading = false,
}: TourListProps) {
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="absolute top-4 left-4 z-10 w-80">
      <div className="bg-surface-elevated/95 backdrop-blur-sm border border-border-subtle rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="px-4 py-3 border-b border-border-subtle">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-text-primary">
              Guided Tours
            </h3>
            <Button
              variant="primary"
              size="sm"
              onClick={onCreate}
              aria-label="Create new tour"
            >
              <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New
            </Button>
          </div>
        </div>

        {/* Tour List */}
        <div className="max-h-96 overflow-y-auto">
          {loading ? (
            <div className="px-4 py-8 text-center">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
              <p className="mt-2 text-sm text-text-secondary">Loading tours...</p>
            </div>
          ) : tours.length === 0 ? (
            <div className="px-4 py-8 text-center">
              <svg className="w-12 h-12 mx-auto text-text-tertiary mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              <p className="text-sm text-text-secondary">No tours yet</p>
              <p className="text-xs text-text-tertiary mt-1">Create your first guided tour</p>
            </div>
          ) : (
            <div className="divide-y divide-border-subtle">
              {tours.map((tour) => {
                const isOwner = tour.user_id === currentUserId;
                const waypointCount = tour.camera_path.length;

                return (
                  <div
                    key={tour.id}
                    className="px-4 py-3 hover:bg-surface-base/50 transition-colors"
                  >
                    {/* Tour Info */}
                    <div className="mb-2">
                      <h4 className="text-sm font-medium text-text-primary mb-1">
                        {tour.name}
                      </h4>
                      <div className="flex items-center gap-3 text-xs text-text-secondary">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                          </svg>
                          {formatDuration(tour.duration)}
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
                          </svg>
                          {waypointCount} waypoints
                        </span>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-2">
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={() => onPlay(tour.id)}
                        className="flex-1"
                      >
                        <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        Play
                      </Button>
                      {isOwner && (
                        <>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onEdit(tour.id)}
                            aria-label="Edit tour"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onDelete(tour.id)}
                            aria-label="Delete tour"
                            className="text-status-error hover:text-status-error"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
