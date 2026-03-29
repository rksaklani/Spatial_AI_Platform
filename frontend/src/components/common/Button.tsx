import React from 'react';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}

/**
 * Button component with multiple variants and states
 * 
 * Variants:
 * - primary: Accent background with white text
 * - secondary: Outlined with accent border
 * - ghost: Minimal style with hover effect
 * - icon: Icon-only button with minimal padding
 * 
 * States:
 * - loading: Shows spinner and disables interaction
 * - disabled: Reduces opacity and disables interaction
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      loading = false,
      disabled = false,
      icon,
      children,
      className = '',
      ...props
    },
    ref
  ) => {
    // Base styles
    const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent-primary focus:ring-offset-2 focus:ring-offset-primary-bg disabled:opacity-50 disabled:cursor-not-allowed';

    // Variant styles
    const variantStyles = {
      primary: 'px-6 py-3 bg-gradient-to-r from-accent-primary to-accent-secondary text-white rounded-lg hover:shadow-glow transform hover:-translate-y-0.5 active:translate-y-0 shadow-lg',
      secondary: 'px-6 py-3 border-2 border-accent-primary text-accent-primary rounded-lg hover:bg-accent-primary/10 hover:shadow-glow',
      ghost: 'px-4 py-2 text-text-secondary hover:text-accent-primary hover:bg-accent-primary/5 rounded-lg',
      icon: 'p-3 text-text-secondary hover:text-accent-primary hover:bg-accent-primary/5 rounded-lg',
    };

    // Size styles (only for non-icon variants)
    const sizeStyles = {
      sm: variant !== 'icon' ? 'text-sm px-4 py-2' : 'p-2',
      md: variant !== 'icon' ? 'text-base px-6 py-3' : 'p-3',
      lg: variant !== 'icon' ? 'text-lg px-8 py-4' : 'p-4',
    };

    // Combine styles
    const buttonClasses = `${baseStyles} ${variantStyles[variant]} ${sizeStyles[size]} ${className}`;

    // Loading spinner component
    const LoadingSpinner = () => (
      <svg
        className="animate-spin h-5 w-5 mr-2"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    );

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={disabled || loading}
        {...props}
      >
        {loading && <LoadingSpinner />}
        {!loading && icon && <span className={children ? 'mr-2' : ''}>{icon}</span>}
        {children}
      </button>
    );
  }
);

Button.displayName = 'Button';
