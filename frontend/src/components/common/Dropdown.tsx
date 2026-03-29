import { ChevronDownIcon } from '@heroicons/react/24/outline';

interface DropdownProps {
  value: string | number;
  onChange: (value: string) => void;
  options: Array<{ value: string | number; label: string }>;
  placeholder?: string;
  className?: string;
  label?: string;
  required?: boolean;
  disabled?: boolean;
}

/**
 * Dropdown component - Attractive select dropdown with glassmorphism
 * 
 * Features:
 * - Orange-blue gradient styling
 * - Glassmorphism effect
 * - Responsive design
 * - Custom chevron icon
 */
export function Dropdown({
  value,
  onChange,
  options,
  placeholder = 'Select an option',
  className = '',
  label,
  required = false,
  disabled = false,
}: DropdownProps) {
  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label className="block text-xs sm:text-sm font-medium text-text-primary mb-2">
          {label}
          {required && <span className="text-accent-primary ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          required={required}
          disabled={disabled}
          className="w-full px-3 sm:px-4 py-2 sm:py-3 bg-secondary-bg/70 backdrop-blur-sm border border-border-color rounded-lg text-text-primary text-sm sm:text-base appearance-none cursor-pointer transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent-primary focus:border-accent-primary hover:border-accent-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {placeholder && (
            <option value="" disabled>
              {placeholder}
            </option>
          )}
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDownIcon className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 sm:w-5 sm:h-5 text-accent-primary pointer-events-none" />
      </div>
    </div>
  );
}
