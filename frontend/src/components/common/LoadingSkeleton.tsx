import React from 'react';

interface LoadingSkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular';
  width?: string | number;
  height?: string | number;
  count?: number;
}

/**
 * LoadingSkeleton component - animated loading placeholder
 * 
 * Features:
 * - Multiple variants (text, circular, rectangular)
 * - Customizable size
 * - Smooth animation
 * - Multiple skeleton support
 */
export function LoadingSkeleton({
  className = '',
  variant = 'text',
  width,
  height,
  count = 1,
}: LoadingSkeletonProps) {
  const baseClasses = 'animate-pulse bg-hover-bg';
  
  const variantClasses = {
    text: 'rounded h-4',
    circular: 'rounded-full',
    rectangular: 'rounded-lg',
  };

  const style: React.CSSProperties = {};
  if (width) style.width = typeof width === 'number' ? `${width}px` : width;
  if (height) style.height = typeof height === 'number' ? `${height}px` : height;

  const skeletons = Array.from({ length: count }, (_, i) => (
    <div
      key={i}
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  ));

  return count > 1 ? (
    <div className="space-y-2">{skeletons}</div>
  ) : (
    <>{skeletons}</>
  );
}

/**
 * SceneCardSkeleton - Loading skeleton for scene cards
 */
export function SceneCardSkeleton() {
  return (
    <div className="bg-secondary-bg rounded-xl border border-border-color overflow-hidden">
      <LoadingSkeleton variant="rectangular" height={192} />
      <div className="p-4 space-y-3">
        <LoadingSkeleton width="75%" />
        <LoadingSkeleton width="50%" />
        <LoadingSkeleton width="66%" />
      </div>
    </div>
  );
}

/**
 * TableRowSkeleton - Loading skeleton for table rows
 */
export function TableRowSkeleton({ columns = 4 }: { columns?: number }) {
  return (
    <tr>
      {Array.from({ length: columns }, (_, i) => (
        <td key={i} className="px-4 py-3">
          <LoadingSkeleton />
        </td>
      ))}
    </tr>
  );
}

/**
 * ListItemSkeleton - Loading skeleton for list items
 */
export function ListItemSkeleton() {
  return (
    <div className="flex items-center gap-3 p-4 bg-secondary-bg rounded-lg border border-border-color">
      <LoadingSkeleton variant="circular" width={40} height={40} />
      <div className="flex-1 space-y-2">
        <LoadingSkeleton width="60%" />
        <LoadingSkeleton width="40%" />
      </div>
    </div>
  );
}
