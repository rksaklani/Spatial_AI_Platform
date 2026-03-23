import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Card } from './Card';

describe('Card Component', () => {
  describe('Rendering', () => {
    it('renders children correctly', () => {
      render(
        <Card>
          <div data-testid="card-content">Card Content</div>
        </Card>
      );
      const content = screen.getByTestId('card-content');
      expect(content).toBeInTheDocument();
      expect(content).toHaveTextContent('Card Content');
    });

    it('applies base styles', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('bg-secondary-bg');
      expect(card).toHaveClass('rounded-xl');
      expect(card).toHaveClass('border');
      expect(card).toHaveClass('border-border-color');
      expect(card).toHaveClass('shadow-lg');
    });

    it('applies custom className', () => {
      render(<Card className="custom-class">Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('custom-class');
    });
  });

  describe('Hover Effects', () => {
    it('applies hover styles by default', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('hover:border-accent-primary');
      expect(card).toHaveClass('hover:shadow-2xl');
      expect(card).toHaveClass('hover:-translate-y-1');
    });

    it('does not apply hover styles when hover is false', () => {
      render(<Card hover={false}>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).not.toHaveClass('hover:border-accent-primary');
      expect(card).not.toHaveClass('hover:shadow-2xl');
      expect(card).not.toHaveClass('hover:-translate-y-1');
    });

    it('has transition classes', () => {
      render(<Card>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('transition-all');
      expect(card).toHaveClass('duration-300');
    });
  });

  describe('Interactions', () => {
    it('calls onClick handler when clicked', () => {
      const handleClick = vi.fn();
      render(<Card onClick={handleClick}>Click Me</Card>);
      const card = screen.getByText('Click Me').parentElement;
      fireEvent.click(card!);
      expect(handleClick).toHaveBeenCalledTimes(1);
    });

    it('applies cursor-pointer when onClick is provided', () => {
      const handleClick = vi.fn();
      render(<Card onClick={handleClick}>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('cursor-pointer');
    });

    it('applies cursor-pointer when hover is enabled', () => {
      render(<Card hover={true}>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).toHaveClass('cursor-pointer');
    });

    it('does not apply cursor-pointer when hover is disabled and no onClick', () => {
      render(<Card hover={false}>Content</Card>);
      const card = screen.getByText('Content').parentElement;
      expect(card).not.toHaveClass('cursor-pointer');
    });
  });

  describe('Complex Content', () => {
    it('renders complex nested content', () => {
      render(
        <Card>
          <div className="p-4">
            <h3>Title</h3>
            <p>Description</p>
            <button>Action</button>
          </div>
        </Card>
      );
      expect(screen.getByText('Title')).toBeInTheDocument();
      expect(screen.getByText('Description')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /action/i })).toBeInTheDocument();
    });
  });
});
