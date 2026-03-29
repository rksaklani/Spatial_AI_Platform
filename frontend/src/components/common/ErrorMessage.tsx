/**
 * ErrorMessage Component
 * 
 * Display user-friendly error messages with retry option
 * Requirements: 25.2, 25.3
 */

import { Button } from './Button';

interface ErrorMessageProps {
  title?: string;
  message: string;
  onRetry?: () => void;
  onDismiss?: () => void;
}

export function ErrorMessage({ 
  title = 'Error', 
  message, 
  onRetry, 
  onDismiss 
}: ErrorMessageProps) {
  return (
    <div className="bg-status-error/10 border border-status-error/20 rounded-lg p-4">
      <div className="flex gap-3">
        <div className="flex-shrink-0">
          <svg className="w-5 h-5 text-status-error" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <div className="flex-1">
          <h3 className="text-sm font-medium text-text-primary mb-1">{title}</h3>
          <p className="text-sm text-text-secondary">{message}</p>
          {(onRetry || onDismiss) && (
            <div className="flex gap-2 mt-3">
              {onRetry && (
                <Button variant="ghost" size="sm" onClick={onRetry}>
                  Try Again
                </Button>
              )}
              {onDismiss && (
                <Button variant="ghost" size="sm" onClick={onDismiss}>
                  Dismiss
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
