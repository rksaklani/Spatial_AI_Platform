import { useEffect, useState } from 'react';
import { useGetSceneJobsQuery } from '../../store/api/sceneApi';

interface ProcessingStage {
  name: string;
  label: string;
  icon: string;
}

const PROCESSING_STAGES: ProcessingStage[] = [
  { name: 'upload', label: 'Uploading', icon: '📤' },
  { name: 'extract_frames', label: 'Extracting Frames', icon: '🎬' },
  { name: 'pose_estimation', label: 'Estimating Poses', icon: '📐' },
  { name: 'depth_estimation', label: 'Estimating Depth', icon: '🗺️' },
  { name: 'reconstruction', label: 'Reconstructing 3D', icon: '🏗️' },
  { name: 'tiling', label: 'Generating Tiles', icon: '🧩' },
];

interface ProcessingProgressProps {
  sceneId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function ProcessingProgress({ sceneId, onComplete, onError }: ProcessingProgressProps) {
  const { data: jobs, isLoading } = useGetSceneJobsQuery(sceneId, {
    pollingInterval: 2000, // Poll every 2 seconds
  });

  const [currentStage, setCurrentStage] = useState<string>('upload');
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!jobs || jobs.length === 0) return;

    // Get the most recent job
    const latestJob = jobs[0];

    if (latestJob.status === 'failed') {
      const errorMsg = latestJob.error || 'Processing failed';
      setError(errorMsg);
      onError?.(errorMsg);
      return;
    }

    if (latestJob.status === 'completed') {
      setProgress(100);
      setCurrentStage('completed');
      onComplete?.();
      return;
    }

    // Update current stage and progress
    if (latestJob.current_step) {
      setCurrentStage(latestJob.current_step);
    }

    if (latestJob.progress_percent !== undefined) {
      setProgress(latestJob.progress_percent);
    }
  }, [jobs, onComplete, onError]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">❌</span>
          <div className="flex-1">
            <p className="text-sm font-medium text-red-400 mb-1">Processing Failed</p>
            <p className="text-xs text-red-300">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  const currentStageIndex = PROCESSING_STAGES.findIndex(s => s.name === currentStage);
  const completedStages = currentStageIndex >= 0 ? currentStageIndex : 0;

  return (
    <div className="space-y-4">
      {/* Progress bar */}
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="text-text-secondary">Processing Scene</span>
          <span className="text-text-primary font-medium">{Math.round(progress)}%</span>
        </div>
        <div className="h-2 bg-secondary-bg rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-500 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>
      </div>

      {/* Stage indicators */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
        {PROCESSING_STAGES.map((stage, index) => {
          const isActive = stage.name === currentStage;
          const isCompleted = index < completedStages;
          const isPending = index > completedStages;

          return (
            <div
              key={stage.name}
              className={`
                flex flex-col items-center gap-2 p-3 rounded-lg border transition-all
                ${isActive ? 'bg-accent-primary/20 border-accent-primary' : ''}
                ${isCompleted ? 'bg-green-500/20 border-green-500/30' : ''}
                ${isPending ? 'bg-secondary-bg border-border-color opacity-50' : ''}
              `}
            >
              <span className="text-2xl">{stage.icon}</span>
              <span className="text-xs text-center text-text-secondary">{stage.label}</span>
              {isActive && (
                <div className="w-full h-1 bg-accent-primary rounded-full animate-pulse" />
              )}
            </div>
          );
        })}
      </div>

      {/* Current stage description */}
      {currentStageIndex >= 0 && currentStageIndex < PROCESSING_STAGES.length && (
        <div className="text-center">
          <p className="text-sm text-text-secondary">
            {PROCESSING_STAGES[currentStageIndex].label}...
          </p>
        </div>
      )}
    </div>
  );
}
