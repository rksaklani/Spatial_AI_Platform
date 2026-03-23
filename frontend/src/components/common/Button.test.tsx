import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Button } from './Button';

describe('Button Component', () => {
  describe('Variants', () => {
    it('renders primary variant correctly', () => {
      render(<Button variant="primary">Primary Button</Button>);
      const button = screen.getByRole('button', { name: /primary button/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('bg-accent-primary');
    });

    it('renders secondary variant correctly', () => {
      render(<Button variant="secondary">Secondary Button</Button>);
      const button = screen.getByRole('button', { name: /secondary button/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('border-accent-primary');
    });

    it('renders ghost variant correctly', () => {
      render(<Button variant="ghost">Ghost Button</Button>);
      const button = screen.getByRole('button', { name: /ghost button/i });
      expect(button).toBeInTheDocument();
      expect(button).toHaveClass('text-text-secondary');
    });

    it('renders icon variant correctly', () => {
      render(
        <Button variant="icon" aria-label="Icon button">
          <span>🔍</span>
        </Button>
      );
      const button = screen.getByRole('button', { name: /icon button/i });
      expect(button).toBeInTheDocument();
    });
  });

  describe('Sizes', () => {
    it('renders small size correctly', () => {
      render(<Button size="sm">Small</Button>);
      const button = screen.getByRole('button', { name: /small/i });
      expect(button).toHaveClass('text-sm');
    });

    it('renders medium size correctly (default)', () => {
      render(<Button size="md">Medium</Button>);
      const button = screen.getByRole('button', { name: /medium/i });
      expect(button).toHaveClass('text-base');
    });

    it('renders large size correctly', () => {
      render(<Button size="lg">Large</Button>);
      const button = screen.getByRole('button', { name: /large/i });
      expect(button).toHaveClass('text-lg');
    });
  });

  describe('States', () => {
    it('shows loading spinner when loading prop is true', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
      // Check for spinner SVG
      const spinner = button.querySelector('svg.animate-spin');
      expect(spinner).toBeInTheDocument();
    });

    it('disables button when disabled prop is true', () => {
      render(<Button disabled>Disabled</Button>);
      const button = screen.getByRole('button', { name: /disabled/i });
      expect(button).toBeDisabled();
      expect(button).toHaveClass('disabled:opacity-50');
    });

    it('disables button when loading', () => {
      render(<Button loading>Loading</Button>);
      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });
  });

  describe('Icons', () => {
    it('renders icon before text', () => {
      render(
        <Button icon={<span data-testid="icon">🔍</span>}>
          Search
        </Button>
      );
      const icon = screen.getByTestId('icon');
      const button = screen.getByRole('button', { name: /search/i });
      expect(button).toContainElement(icon);
    });

    it('does not show icon when loading', () => {
      render(
        <Button loading icon={<span data-testid="icon">🔍</span>}>
          Loading
        </Button>
      );
      const icon = screen.queryByTestId('icon');
      expect(icon).not.toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick}>Click Me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      fireEvent.click(button);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('does not call onClick when disabled', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick} disabled>Click Me</Button>);
      const button = screen.getByRole('button', { name: /click me/i });
      fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });

    it('does not call onClick when loading', () => {
      const handleClick = vi.fn();
      render(<Button onClick={handleClick} loading>Click Me</Button>);
      const button = screen.getByRole('button');
      fireEvent.click(button);
      expect(handleClick).not.toHaveBeenCalled();
    });
  });

  describe('Accessibility', () => {
    it('supports aria-label for icon buttons', () => {
      render(
        <Button variant="icon" aria-label="Search">
          <span>🔍</span>
        </Button>
      );
      const button = screen.getByRole('button', { name: /search/i });
      expect(button).toBeInTheDocument();
    });

    it('has focus ring styles', () => {
      render(<Button>Focus Me</Button>);
      const button = screen.getByRole('button', { name: /focus me/i });
      expect(button).toHaveClass('focus:ring-2');
      expect(button).toHaveClass('focus:ring-accent-primary');
    });
  });

  describe('Hover Animations', () => {
    it('has hover transform for primary variant', () => {
      render(<Button variant="primary">Hover Me</Button>);
      const button = screen.getByRole('button', { name: /hover me/i });
      expect(button).toHaveClass('hover:-translate-y-0.5');
    });

    it('has transition classes', () => {
      render(<Button>Button</Button>);
      const button = screen.getByRole('button', { name: /button/i });
      expect(button).toHaveClass('transition-all');
      expect(button).toHaveClass('duration-200');
    });
  });
});
