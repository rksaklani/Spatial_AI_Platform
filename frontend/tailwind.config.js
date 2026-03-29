/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Surface colors - Dark theme with orange-blue glow
        'surface-base': 'rgb(var(--color-surface-base) / <alpha-value>)',
        'surface-elevated': 'rgb(var(--color-surface-elevated) / <alpha-value>)',
        'surface-overlay': 'rgb(var(--color-surface-overlay) / <alpha-value>)',
        
        // Primary Colors - Black + Orange + Blue
        'primary-bg': '#000000',
        'secondary-bg': 'rgba(20, 20, 20, 0.8)',
        'accent-primary': '#FF6B35',      // Neon Orange
        'accent-secondary': '#4A90E2',    // Electric Blue
        'accent-coral': '#FF6B35',        // Legacy compatibility
        
        // Text Colors
        'text-primary': '#FFFFFF',
        'text-secondary': '#B0B0B0',
        'text-muted': '#707070',
        
        // UI Elements
        'border-color': 'rgba(255, 255, 255, 0.1)',
        'border-subtle': 'rgba(255, 255, 255, 0.05)',
        'hover-bg': 'rgba(255, 107, 53, 0.1)',
        'glass-bg': 'rgba(20, 20, 20, 0.6)',
      },
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'sans-serif'],
        display: ['Space Grotesk', 'Inter', 'sans-serif'],
      },
      boxShadow: {
        'glass': '0 8px 32px rgba(0, 0, 0, 0.9)',
        'glow': '0 0 30px rgba(255, 107, 53, 0.5)',
        'glow-lg': '0 0 50px rgba(255, 107, 53, 0.6)',
        'glow-blue': '0 0 30px rgba(74, 144, 226, 0.5)',
        'inner-glow': 'inset 0 0 20px rgba(255, 107, 53, 0.1)',
        'card': '0 8px 32px rgba(0, 0, 0, 0.8), inset 0 1px 0 rgba(255, 255, 255, 0.05)',
      },
      backdropBlur: {
        'xl': '24px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'slide-down': 'slideDown 0.3s ease-out',
        'in': 'fadeIn 0.3s ease-in-out',
        'slide-in-from-right': 'slideInFromRight 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideDown: {
          '0%': { transform: 'translateY(-20px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
        slideInFromRight: {
          '0%': { transform: 'translateX(100%)', opacity: '0' },
          '100%': { transform: 'translateX(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

