import { useEffect, useState } from 'react';
import { useGetSceneJobsQuery } from '../../store/api/sceneApi';
import { TrainingProgressDisplay } from '../TrainingProgressDisplay';
import { useSceneProgress } from '../../hooks/useSceneProgress';
import { useAppSelector } from '../../store/hooks';

interface ProcessingStage {
  name: string;
  label: string;
  icon: string;
}

const PROCESSING_STAGES: ProcessingStage[] = [
  { name: 'uploading', label: 'Uploading', icon: '📤' },
  { name: 'extracting_frames', label: 'Extracting Frames', icon: '🎬' },
  { name: 'estimating_poses', label: 'Estimating Poses', icon: '📐' },
  { name: 'generating_depth', label: 'Estimating Depth', icon: '🗺️' },
  { name: 'training', label: 'Training (Gaussian Splatting)', icon: '🏗️' },
  { name: 'tiling', label: 'Generating Tiles', icon: '🧩' },
];

const FINAL_STAGE_INDEX = PROCESSING_STAGES.length;

function normalizeProcessingStep(step?: string | null): string {
  if (!step) return 'uploading';

  if (['pending', 'queued'].includes(step)) return 'uploading';

  // Video pipeline steps
  if (['initializing', 'downloading', 'filtering_frames', 'uploading_frames', 'uploading_depth', 'uploading'].includes(step)) {
    return 'uploading';
  }
  if (step === 'extracting_frames') return 'extracting_frames';
  if (step === 'pose_estimation') return 'estimating_poses';
  if (step === 'depth_estimation') return 'generating_depth';

  // Gaussian splatting + import steps
  if (['training', 'loading', 'optimizing', 'generating_lod', 'converting', 'parsing', 'saving', 'starting'].includes(step)) {
    return 'training';
  }

  // Tiling/optimization steps
  if (['building_octree', 'pruning', 'merging', 'saving_metadata', 'tiling'].includes(step)) {
    return 'tiling';
  }

  // Scene-level queued statuses sometimes leak into current_step
  if (['queued_reconstruction', 'queued_tiling'].includes(step)) {
    return 'training';
  }

  return step;
}

interface ProcessingProgressProps {
  sceneId: string;
  onComplete?: () => void;
  onError?: (error: string) => void;
}

export function ProcessingProgress({ sceneId, onComplete, onError }: ProcessingProgressProps) {
  const [currentStage, setCurrentStage] = useState<string>('uploading');
  const [progress, setProgress] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [isJobComplete, setIsJobComplete] = useState(false);
  
  const token = useAppSelector(state => state.auth.token);

  const { data: jobs, isLoading } = useGetSceneJobsQuery(sceneId, {
    pollingInterval: isJobComplete ? 0 : 2000, // Stop polling when complete
    skip: isJobComplete, // Skip query when complete
  });
  
  // Use the new progress hook for real-time updates
  const {
    progressPercent,
    currentIteration,
    totalIterations,
    statusMessage,
    estimatedSecondsRemaining,
    currentStep,
    isComplete: progressComplete,
    isFailed: progressFailed,
    error: progressError,
  } = useSceneProgress({
    sceneId,
    token: token || '',
    enabled: !isJobComplete,
    pollingInterval: 5000,
    enableWebSocket: true,
  });

  const latestJob = jobs?.[0];

  // Prefer latest job step first (usually freshest), then websocket/rest fallback.
  const jobStep = latestJob?.current_step as string | undefined;
  const effectiveStep =
    (jobStep && jobStep !== 'pending' ? jobStep : undefined) ||
    (currentStep && currentStep !== 'pending' ? currentStep : undefined) ||
    jobStep ||
    currentStep ||
    currentStage ||
    'pending';

  const effectiveProgress =
    progressPercent > 0
      ? progressPercent
      : (typeof latestJob?.progress_percent === 'number' ? latestJob.progress_percent : progress);

  const isTerminalComplete =
    latestJob?.status === 'completed' ||
    progressComplete ||
    effectiveStep === 'completed' ||
    effectiveProgress >= 100;

  const normalizedStep = isTerminalComplete ? 'completed' : normalizeProcessingStep(effectiveStep);

  useEffect(() => {
    if (!jobs || jobs.length === 0) return;

    // Get the most recent job
    const latestJob = jobs[0];

    if (latestJob.status === 'failed') {
      const errorMsg = latestJob.error_message || latestJob.error || 'Processing failed';
      // Only set error and call onError once
      if (error !== errorMsg) {
        setError(errorMsg);
        setIsJobComplete(true); // Stop polling
        onError?.(errorMsg);
      }
      return;
    }

    if (latestJob.status === 'completed') {
      setProgress(100);
      setCurrentStage('completed');
      setIsJobComplete(true); // Stop polling
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
  }, [jobs, onComplete, onError, error]);
  
  // Handle progress completion from WebSocket/REST
  useEffect(() => {
    if (progressComplete && !isJobComplete) {
      setIsJobComplete(true);
      onComplete?.();
    }
    if (progressFailed && !isJobComplete) {
      setIsJobComplete(true);
      if (progressError) {
        setError(progressError);
        onError?.(progressError);
      }
    }
  }, [progressComplete, progressFailed, progressError, isJobComplete, onComplete, onError]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent-primary"></div>
      </div>
    );
  }

  if (error || progressError) {
    return (
      <div className="bg-red-500/20 border border-red-500/30 rounded-lg p-4">
        <div className="flex items-start gap-3">
          <span className="text-2xl">❌</span>
          <div className="flex-1">
            <p className="text-sm font-medium text-red-400 mb-1">Processing Failed</p>
            <p className="text-xs text-red-300">{error || progressError}</p>
          </div>
        </div>
      </div>
    );
  }

  const currentStageIndex =
    normalizedStep === 'completed'
      ? FINAL_STAGE_INDEX
      : PROCESSING_STAGES.findIndex(s => s.name === normalizedStep);
  const completedStages = currentStageIndex >= 0 ? currentStageIndex : 0;
  
  const displayProgress = effectiveProgress;
  const displayStatusMessage =
    isTerminalComplete
      ? 'Processing complete'
      : effectiveStep === 'pending' || effectiveStep === 'queued'
      ? 'Queued — waiting for worker to start'
      : statusMessage || (currentStageIndex >= 0 ? PROCESSING_STAGES[currentStageIndex].label : 'Processing...');

  return (
    <div className="space-y-6">
      {/* Real-time training progress display (when training) */}
      {normalizedStep === 'training' &&
        currentIteration !== undefined &&
        totalIterations !== undefined && (
        <TrainingProgressDisplay
          progressPercent={displayProgress}
          currentIteration={currentIteration}
          totalIterations={totalIterations}
          statusMessage={displayStatusMessage}
          estimatedSecondsRemaining={estimatedSecondsRemaining}
          state={progressFailed ? 'failed' : progressComplete ? 'complete' : 'in-progress'}
        />
      )}
      
      {/* Standard progress bar for other stages */}
      {normalizedStep !== 'training' && (
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-text-secondary">Processing Scene</span>
            <span className="text-text-primary font-medium">{Math.round(isTerminalComplete ? 100 : displayProgress)}%</span>
          </div>
          <div className="h-2 bg-secondary-bg rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-accent-primary to-accent-secondary transition-all duration-500 ease-out"
              style={{ width: `${isTerminalComplete ? 100 : displayProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Stage indicators */}
      <div className="grid grid-cols-3 md:grid-cols-6 gap-2">
        {PROCESSING_STAGES.map((stage, index) => {
          const isActive = !isTerminalComplete && stage.name === normalizedStep;
          const isCompleted = isTerminalComplete || index < completedStages;
          const isPending = !isTerminalComplete && index > completedStages;

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
            {displayStatusMessage}
          </p>
        </div>
      )}

      {/* Verification: show raw step + iterations */}
      <div className="text-xs text-text-muted flex flex-wrap gap-x-4 gap-y-1 justify-center">
        <span>
          Step: <span className="font-mono text-text-secondary">{effectiveStep || 'n/a'}</span>
        </span>
        <span>
          Iterations: <span className="font-mono text-text-secondary">{currentIteration || 'n/a'} / {totalIterations || 'n/a'}</span>
        </span>
      </div>
    </div>
  );
}