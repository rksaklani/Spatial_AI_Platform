# Layout Components

This directory contains layout components that provide the structural shell for the application.

## Components

### AppLayout

Main application layout component that wraps authenticated pages.

**Features:**
- Top navigation bar with logo, links, notifications, and user menu
- Responsive sidebar (hidden on mobile, collapsible on desktop)
- Mobile bottom navigation (visible only on mobile devices)
- Main content area with proper spacing and responsive padding
- Automatic layout adaptation based on screen size
- Renders child routes via React Router's `<Outlet />`

**Usage:**
```tsx
import { AppLayout } from './components/layout';

// In router configuration
<Route element={<AppLayout />}>
  <Route path="/dashboard" element={<DashboardPage />} />
  <Route path="/scenes" element={<ScenesPage />} />
</Route>
```

**Responsive Behavior:**
- **Desktop (≥1024px):** Shows top navigation bar + sidebar + main content
- **Tablet (768px-1023px):** Shows top navigation bar + collapsible sidebar + main content
- **Mobile (<768px):** Shows top navigation bar + main content + bottom navigation bar

**Requirements:** 18.2, 18.3, 24.1, 24.2

### NavigationBar

Top horizontal navigation bar with logo, navigation links, and user controls.

**Features:**
- Logo and organization name display
- Main navigation links (Dashboard, Scenes, Photos, Help)
- Notification bell with badge counter
- Theme toggle button (light/dark mode)
- User menu dropdown with profile, settings, and logout

**Props:**
```tsx
interface NavigationBarProps {
  organizationName?: string;      // Organization name to display
  userName?: string;               // User name for dropdown
  notificationCount?: number;      // Number of unread notifications
  onThemeToggle?: () => void;      // Theme toggle callback
  onLogout?: () => void;           // Logout callback
  isDarkMode?: boolean;            // Current theme state
}
```

**Usage:**
```tsx
import { NavigationBar } from './components/layout';

<NavigationBar
  organizationName="Spatial AI Platform"
  userName="John Doe"
  notificationCount={5}
  isDarkMode={true}
  onThemeToggle={handleThemeToggle}
  onLogout={handleLogout}
/>
```

**Design:**
- Fixed position at top of viewport
- Dark background with glassmorphism effect
- Coral accent colors for interactive elements
- Smooth animations and transitions
- Responsive design (hides nav links on mobile)

**Accessibility:**
- Proper ARIA labels for icon buttons
- Keyboard navigation support
- Focus indicators
- Screen reader friendly

## Design Reference

See `.kiro/specs/frontend-ui-integration/ui-design-guide.md` for detailed design specifications.

## Requirements

- **30.1**: Navigation bar with logo and organization name
- **30.4**: Notification bell with badge
- **43.1**: Theme toggle button


### Sidebar

Vertical sidebar navigation for desktop and tablet views.

**Features:**
- Logo and branding
- Main navigation links with icons and active states
- Notifications button with badge counter
- Theme toggle button
- Settings link
- User profile display
- Logout button
- Collapsible on desktop (icon-only mode)
- Hidden on mobile (replaced by bottom navigation)

**Props:**
```tsx
interface SidebarProps {
  isCollapsed?: boolean;    // Whether sidebar is in collapsed state
  onToggle?: () => void;    // Callback for collapse/expand toggle
}
```

**Requirements:** 30.2, 30.5, 30.6

### PublicLayout

Layout component for public pages (login, register) with centered content and branding.

## Responsive Design

The layout components use the `useMediaQuery` hook to detect screen size and adapt the layout accordingly:

```tsx
import { useIsMobile, useIsTablet, useIsDesktop } from '../../hooks/useMediaQuery';

// In component
const isMobile = useIsMobile();    // true for screens < 768px
const isTablet = useIsTablet();    // true for screens 768px-1023px
const isDesktop = useIsDesktop();  // true for screens ≥ 1024px
```

**Breakpoints:**
- Mobile: < 768px
- Tablet: 768px - 1023px
- Desktop: ≥ 1024px

## Mobile Bottom Navigation

On mobile devices, the sidebar is replaced with a bottom navigation bar that includes:
- Home (Dashboard)
- Scenes
- Photos
- Settings

**Features:**
- Fixed at bottom of screen
- 44px minimum touch targets for accessibility
- Active state highlighting
- Icon + label for each navigation item

**Requirements:** 18.2, 24.2, 24.5

## Accessibility

All layout components follow accessibility best practices:
- Minimum 44px touch targets on mobile
- Keyboard navigation support
- ARIA labels for interactive elements
- Semantic HTML structure
- Focus indicators for keyboard navigation
- Screen reader friendly
