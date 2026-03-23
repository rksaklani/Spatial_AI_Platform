import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean;
}

/**
 * Standard Card component with dark theme styling
 * 
 * Features:
 * - Dark background with border
 * - Optional hover effects with elevation and border color change
 * - Rounded corners
 * - Smooth transitions
 */
export const Card: React.FC<CardProps> = ({ 
  children, 
  className = '', 
  onClick,
  hover = true 
}) => {
  const baseStyles = 'bg-secondary-bg rounded-xl border border-border-color shadow-lg transition-all duration-300';
  const hoverStyles = hover 
    ? 'hover:border-accent-primary hover:shadow-2xl hover:-translate-y-1 cursor-pointer' 
    : '';
  const clickableStyles = onClick ? 'cursor-pointer' : '';

  return (
    <div 
      className={`${baseStyles} ${hoverStyles} ${clickableStyles} ${className}`}
      onClick={onClick}
    >
      {children}
    </div>
  );
};

export default Card;
