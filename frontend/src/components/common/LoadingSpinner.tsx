export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
}

/**
 * Loading spinner component
 * 
 * Displays an animated spinner for loading states
 * Can be used inline or as a fullscreen overlay
 */
export function LoadingSpinner({ size = 'md', fullScreen = false }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-4 h-4 border-2',
    md: 'w-8 h-8 border-2',
    lg: 'w-12 h-12 border-3',
  };

  const spinner = (
    <div
      className={`${sizeClasses[size]} border-accent-primary border-t-transparent rounded-full animate-spin`}
      role="status"
      aria-label="Loading"
    />
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-primary-bg flex items-center justify-center z-50">
        {spinner}
      </div>
    );
  }

  return spinner;
}
