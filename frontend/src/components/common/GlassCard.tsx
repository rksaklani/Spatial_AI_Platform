import React from 'react';

export interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  blur?: 'sm' | 'md' | 'lg' | 'xl';
}

/**
 * GlassCard component with glassmorphism effect
 * 
 * Features:
 * - Semi-transparent background with backdrop blur
 * - Subtle border for depth
 * - Glass shadow effect
 * - Perfect for overlays, modals, and floating UI elements
 * - Configurable blur intensity
 */
export const GlassCard: React.FC<GlassCardProps> = ({ 
  children, 
  className = '', 
  onClick,
  blur = 'xl'
}) => {
  const blurClasses = {
    sm: 'backdrop-blur-sm',
    md: 'backdrop-blur-md',
    lg: 'backdrop-blur-lg',
    xl: 'backdrop-blur-xl'
  };

  const baseStyles = 'bg-glass-bg rounded-xl border border-border-color shadow-glass transition-all duration-300';
  const blurStyle = blurClasses[blur];
  const clickableStyles = onClick ? 'cursor-pointer hover:border-accent-primary/50' : '';

  return (
    <div 
      className={`${baseStyles} ${blurStyle} ${clickableStyles} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default GlassCard;
