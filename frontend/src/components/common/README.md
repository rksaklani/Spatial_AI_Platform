# Common UI Components

This directory contains reusable UI components used throughout the application.

## Button Component

A versatile button component with multiple variants, sizes, and states.

### Import

```tsx
import { Button } from '@/components/common';
// or
import { Button } from '@/components/common/Button';
```

### Variants

#### Primary
Accent background with white text. Use for primary actions.

```tsx
<Button variant="primary">Upload Video</Button>
```

#### Secondary
Outlined with accent border. Use for secondary actions.

```tsx
<Button variant="secondary">Browse Scenes</Button>
```

#### Ghost
Minimal style with hover effect. Use for tertiary actions.

```tsx
<Button variant="ghost">Cancel</Button>
```

#### Icon
Icon-only button with minimal padding. Use for toolbar actions.

```tsx
<Button variant="icon" aria-label="Settings">
  <SettingsIcon />
</Button>
```

### Sizes

- `sm`: Small (text-sm, px-4 py-2)
- `md`: Medium (text-base, px-6 py-3) - Default
- `lg`: Large (text-lg, px-8 py-4)

```tsx
<Button size="sm">Small</Button>
<Button size="md">Medium</Button>
<Button size="lg">Large</Button>
```

### States

#### Loading
Shows a spinner and disables the button.

```tsx
<Button loading>Processing...</Button>
```

#### Disabled
Reduces opacity and disables interaction.

```tsx
<Button disabled>Unavailable</Button>
```

### With Icons

Add an icon before the text using the `icon` prop.

```tsx
<Button icon={<UploadIcon />}>Upload</Button>
```

### Props

```typescript
interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'icon';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  children?: React.ReactNode;
}
```

### Examples

See `Button.stories.tsx` for comprehensive examples of all variants and states.

### Accessibility

- All buttons support keyboard navigation (Tab, Enter, Space)
- Icon buttons should include `aria-label` for screen readers
- Focus states are visible with ring outline
- Disabled state prevents interaction and reduces opacity

### Design Reference

Based on the UI Design Guide (ui-design-guide.md):
- Uses Tailwind design tokens from `tailwind.config.js`
- Follows the dark-first design aesthetic
- Includes hover animations and transitions
- Maintains WCAG 2.1 AA contrast ratios

---

## Card Component

A standard card component with dark theme styling and hover effects.

### Import

```tsx
import { Card } from '@/components/common';
// or
import { Card } from '@/components/common/Card';
```

### Basic Usage

```tsx
<Card>
  <div className="p-6">
    <h3 className="text-lg font-semibold text-text-primary">Card Title</h3>
    <p className="text-text-secondary">Card content goes here</p>
  </div>
</Card>
```

### Features

- **Dark background** with `bg-secondary-bg`
- **Border** with subtle `border-border-color`
- **Rounded corners** with `rounded-xl`
- **Shadow** with `shadow-lg`
- **Hover effects** (optional):
  - Border color changes to accent
  - Shadow increases to `shadow-2xl`
  - Translates up by 1px (`-translate-y-1`)
- **Smooth transitions** (300ms)

### Props

```typescript
interface CardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  hover?: boolean; // Default: true
}
```

### Examples

#### Scene Card

```tsx
<Card onClick={() => navigate(`/scenes/${sceneId}`)}>
  <div className="aspect-video bg-primary-bg">
    <img src={thumbnail} alt={name} className="w-full h-full object-cover" />
  </div>
  <div className="p-4">
    <h3 className="text-lg font-semibold text-text-primary">{sceneName}</h3>
    <p className="text-sm text-text-secondary">{description}</p>
    <span className="text-xs text-text-muted">{createdAt}</span>
  </div>
</Card>
```

#### Static Card (No Hover)

```tsx
<Card hover={false}>
  <div className="p-6">
    <p className="text-text-secondary">This card doesn't have hover effects</p>
  </div>
</Card>
```

### Use Cases

- Scene cards in dashboard grid
- Content cards with thumbnails
- Information panels
- List items with rich content

---

## GlassCard Component

A glassmorphism card with semi-transparent background and backdrop blur.

### Import

```tsx
import { GlassCard } from '@/components/common';
// or
import { GlassCard } from '@/components/common/GlassCard';
```

### Basic Usage

```tsx
<GlassCard className="p-6">
  <h3 className="text-lg font-semibold text-text-primary">Glass Card</h3>
  <p className="text-text-secondary">Semi-transparent with blur effect</p>
</GlassCard>
```

### Features

- **Semi-transparent background** with `bg-glass-bg` (rgba(26, 26, 26, 0.8))
- **Backdrop blur** for glassmorphism effect
- **Subtle border** with `border-border-color`
- **Glass shadow** with `shadow-glass`
- **Configurable blur intensity** (sm, md, lg, xl)
- **Smooth transitions** (300ms)

### Props

```typescript
interface GlassCardProps {
  children: React.ReactNode;
  className?: string;
  onClick?: () => void;
  blur?: 'sm' | 'md' | 'lg' | 'xl'; // Default: 'xl'
}
```

### Blur Levels

```tsx
<GlassCard blur="sm">Light blur</GlassCard>
<GlassCard blur="md">Medium blur</GlassCard>
<GlassCard blur="lg">Large blur</GlassCard>
<GlassCard blur="xl">Extra large blur (default)</GlassCard>
```

### Examples

#### Floating Toolbar

```tsx
<div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
  <GlassCard className="px-6 py-4">
    <div className="flex items-center space-x-6">
      <button>📷 Camera</button>
      <button>📍 Annotate</button>
      <button>👥 Collaborate</button>
    </div>
  </GlassCard>
</div>
```

#### Modal Overlay

```tsx
<div className="fixed inset-0 flex items-center justify-center">
  <GlassCard className="max-w-md w-full p-6">
    <h2 className="text-2xl font-bold text-text-primary mb-4">Modal Title</h2>
    <p className="text-text-secondary">Modal content</p>
  </GlassCard>
</div>
```

#### Settings Panel

```tsx
<GlassCard blur="lg" className="p-6">
  <h3 className="text-lg font-semibold text-text-primary mb-4">Settings</h3>
  <div className="space-y-4">
    {/* Settings controls */}
  </div>
</GlassCard>
```

### Use Cases

- Floating toolbars in 3D viewer
- Modal dialogs and overlays
- Side panels and drawers
- Notification cards
- Tooltips and popovers
- Any UI element that needs to float over content

### Design Reference

Based on the UI Design Guide (ui-design-guide.md):
- Glassmorphism effect for depth and hierarchy
- Perfect for overlays and floating elements
- Works best over complex backgrounds (like 3D scenes or geometric patterns)
- Maintains readability while showing content underneath

---

## Component Stories

See `Card.stories.tsx` for comprehensive examples of all card variants and real-world use cases including:
- Standard cards with various content types
- Glass cards with different blur levels
- Floating toolbars
- Modal examples
- Scene card implementations
