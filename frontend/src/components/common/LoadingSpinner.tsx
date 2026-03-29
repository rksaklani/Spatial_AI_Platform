export interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  fullScreen?: boolean;
  variant?: 'spinner' | 'dots' | 'pulse';
}

/**
 * Loading spinner component with orange-blue gradient theme
 * 
 * Displays an animated loader for loading states
 * Can be used inline or as a fullscreen overlay
 * 
 * Variants:
 * - spinner: Rotating gradient ring
 * - dots: Bouncing dots with gradient
 * - pulse: Pulsing gradient circle
 */
export function LoadingSpinner({ 
  size = 'md', 
  fullScreen = false,
  variant = 'spinner'
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'w-8 h-8',
    md: 'w-12 h-12',
    lg: 'w-16 h-16',
  };

  const dotSizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3',
    lg: 'w-4 h-4',
  };

  const renderSpinner = () => {
    if (variant === 'dots') {
      return (
        <div className="flex space-x-2" role="status" aria-label="Loading">
          <div 
            className={`${dotSizeClasses[size]} rounded-full bg-gradient-to-r from-accent-primary to-accent-secondary animate-bounce`}
            style={{ animationDelay: '0ms' }}
          />
          <div 
            className={`${dotSizeClasses[size]} rounded-full bg-gradient-to-r from-accent-primary to-accent-secondary animate-bounce`}
            style={{ animationDelay: '150ms' }}
          />
          <div 
            className={`${dotSizeClasses[size]} rounded-full bg-gradient-to-r from-accent-primary to-accent-secondary animate-bounce`}
            style={{ animationDelay: '300ms' }}
          />
        </div>
      );
    }

    if (variant === 'pulse') {
      return (
        <div 
          className={`${sizeClasses[size]} rounded-full bg-gradient-to-r from-accent-primary to-accent-secondary animate-pulse shadow-glow`}
          role="status"
          aria-label="Loading"
        />
      );
    }

    // Default spinner variant
    return (
      <div className="relative" role="status" aria-label="Loading">
        <div 
          className={`${sizeClasses[size]} rounded-full border-4 border-transparent bg-gradient-to-r from-accent-primary to-accent-secondary animate-spin`}
          style={{
            maskImage: 'linear-gradient(transparent 50%, black 50%)',
            WebkitMaskImage: 'linear-gradient(transparent 50%, black 50%)',
          }}
        />
        <div 
          className={`${sizeClasses[size]} rounded-full border-4 border-accent-primary/20 absolute top-0 left-0`}
        />
      </div>
    );
  };

  const content = (
    <div className="flex flex-col items-center justify-center space-y-4">
      {renderSpinner()}
      {fullScreen && (
        <div className="text-center">
          <p className="text-text-primary font-medium text-lg mb-1">Loading</p>
          <p className="text-text-secondary text-sm">Please wait...</p>
        </div>
      )}
    </div>
  );

  if (fullScreen) {
    return (
      <div className="fixed inset-0 bg-primary-bg/95 backdrop-blur-sm flex items-center justify-center z-50">
        {content}
      </div>
    );
  }

  return renderSpinner();
}
