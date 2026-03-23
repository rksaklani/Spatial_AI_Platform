import { Link, Outlet } from 'react-router-dom';

/**
 * PublicLayout - Centered layout for login/register pages
 * Features:
 * - Centered content with max-width constraint
 * - Branding and logo at the top
 * - Geometric background pattern
 * - Responsive design for mobile/tablet/desktop
 * 
 * Requirements: 1.1, 18.1
 */
export function PublicLayout() {
  return (
    <div className="min-h-screen geometric-bg flex flex-col">
      {/* Branding Header */}
      <header className="w-full py-6 px-4 sm:py-8 sm:px-6">
        <div className="max-w-md mx-auto">
          <Link to="/" className="flex items-center justify-center space-x-3 group">
            {/* Logo */}
            <div className="w-12 h-12 sm:w-14 sm:h-14 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-xl flex items-center justify-center shadow-glow group-hover:shadow-xl transition-all duration-300 transform group-hover:scale-105">
              <span className="text-white font-bold text-2xl sm:text-3xl">S</span>
            </div>
            {/* Brand Name */}
            <div className="flex flex-col">
              <span className="text-text-primary font-display font-bold text-xl sm:text-2xl group-hover:text-accent-primary transition-colors duration-200">
                SPATIAL AI
              </span>
              <span className="text-text-muted text-xs sm:text-sm font-medium tracking-wide">
                3D Scene Platform
              </span>
            </div>
          </Link>
        </div>
      </header>

      {/* Main Content - Centered */}
      <main className="flex-1 flex items-center justify-center px-4 py-8 sm:px-6 lg:px-8">
        <div className="w-full max-w-md">
          <Outlet />
        </div>
      </main>

      {/* Footer */}
      <footer className="w-full py-6 px-4 sm:py-8 sm:px-6">
        <div className="max-w-md mx-auto">
          <div className="flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-6 text-sm text-text-muted">
            <Link 
              to="/help" 
              className="hover:text-accent-primary transition-colors duration-200"
            >
              Help Center
            </Link>
            <span className="hidden sm:inline">•</span>
            <Link 
              to="/privacy" 
              className="hover:text-accent-primary transition-colors duration-200"
            >
              Privacy
            </Link>
            <span className="hidden sm:inline">•</span>
            <Link 
              to="/terms" 
              className="hover:text-accent-primary transition-colors duration-200"
            >
              Terms
            </Link>
          </div>
          <div className="mt-4 text-center text-xs text-text-muted">
            © 2024 Spatial AI Platform. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
}
