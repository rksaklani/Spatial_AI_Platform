import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { GlassCard } from './GlassCard';

describe('GlassCard Component', () => {
  describe('Rendering', () => {
    it('renders children correctly', () => {
      render(
        <GlassCard>
          <div data-testid="glass-content">Glass Content</div>
        </GlassCard>
      );
      const content = screen.getByTestId('glass-content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveTextContent('Glass Content');
    });

    it('applies base glassmorphism styles', () => {
      render(<GlassCard>Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('bg-glass-bg');
      expect(card).toHaveClass('rounded-xl');
      expect(card).toHaveClass('border');
      expect(card).toHaveClass('border-border-color');
      expect(card).toHaveClass('shadow-glass');
    });

    it('applies custom className', () => {
      render(<GlassCard className="custom-glass">Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('custom-glass');
    });
  });

  describe('Blur Levels', () => {
    it('applies xl blur by default', () => {
      render(<GlassCard>Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('backdrop-blur-xl');
    });

    it('applies sm blur when specified', () => {
      render(<GlassCard blur="sm">Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('backdrop-blur-sm');
    });

    it('applies md blur when specified', () => {
      render(<GlassCard blur="md">Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('backdrop-blur-md');
    });

    it('applies lg blur when specified', () => {
      render(<GlassCard blur="lg">Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('backdrop-blur-lg');
    });

    it('applies xl blur when specified', () => {
      render(<GlassCard blur="xl">Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('backdrop-blur-xl');
    });
  });

  describe('Interactions', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = vi.fn();
      render(<GlassCard onClick={handleClick}>Click Me</GlassCard>);
      const card = screen.getByText('Click Me').parentElement;
      fireEvent.click(card!);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies cursor-pointer and hover styles when onClick is provided', () => {
      const handleClick = vi.fn();
      render(<GlassCard onClick={handleClick}>Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('cursor-pointer');
      expect(card).toHaveClass('hover:border-accent-primary/50');
    });

    it('does not apply cursor-pointer when onClick is not provided', () => {
      render(<GlassCard>Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).not.toHaveClass('cursor-pointer');
    });
  });

  describe('Transitions', () => {
    it('has transition classes', () => {
      render(<GlassCard>Content</GlassCard>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('transition-all');
      expect(card).toHaveClass('duration-300');
    });
  });

  describe('Use Cases', () => {
    it('works as overlay container', () => {
      render(
        <GlassCard className="absolute top-0 left-0">
          <div>Overlay Content</div>
        </GlassCard>
      );
      const card = screen.getByText('Overlay Content').parentElement;
      expect(card).toHaveClass('absolute');
      expect(card).toHaveClass('bg-glass-bg');
      expect(card).toHaveClass('backdrop-blur-xl');
    });

    it('works as modal container', () => {
      render(
        <GlassCard className="p-6">
          <h2>Modal Title</h2>
          <p>Modal content goes here</p>
          <button>Close</button>
        </GlassCard>
      );
      expect(screen.getByText('Modal Title')).toBeInTheDocument();
      expect(screen.getByText('Modal content goes here')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /close/i })).toBeInTheDocument();
    });

    it('works as floating toolbar', () => {
      render(
        <GlassCard className="fixed bottom-8">
          <div className="flex space-x-4">
            <button>Tool 1</button>
            <button>Tool 2</button>
          </div>
        </GlassCard>
      );
      expect(screen.getByRole('button', { name: /tool 1/i })).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /tool 2/i })).toBeInTheDocument();
    });
  });
});
