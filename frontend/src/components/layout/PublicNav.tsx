import { Link } from 'react-router-dom';
import { useState } from 'react';
import { Button } from '../common/Button';

export function PublicNav() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-secondary-bg/90 backdrop-blur-md border-b border-border-color shadow-glass">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 sm:py-4">
        <div className="flex items-center justify-between">
          {/* Logo and Brand */}
          <Link to="/" className="flex items-center space-x-2 sm:space-x-3 group">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center shadow-glow group-hover:shadow-glow-lg transition-all duration-200">
              <span className="text-white font-bold text-lg sm:text-xl">S</span>
            </div>
            <span className="text-text-primary font-display font-bold text-base sm:text-xl group-hover:text-accent-primary transition-colors duration-200">
              SPATIAL AI
            </span>
          </Link>

          {/* Desktop Navigation Links */}
          <div className="hidden lg:flex items-center space-x-6 xl:space-x-8">
            <Link
              to="/about"
              className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200"
            >
              ABOUT
            </Link>
            <Link
              to="/pricing"
              className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200"
            >
              PRICING
            </Link>
            <Link
              to="/help"
              className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200"
            >
              HELP CENTER
            </Link>
            <Link
              to="/contact"
              className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200"
            >
              CONTACT
            </Link>
          </div>

          {/* Desktop Auth Buttons */}
          <div className="hidden lg:flex items-center space-x-4">
            <Link to="/login">
              <Button variant="secondary" size="sm" className="text-xs sm:text-sm px-3 sm:px-4">
                LOG IN
              </Button>
            </Link>
            <Link to="/register">
              <Button variant="primary" size="sm" className="text-xs sm:text-sm px-3 sm:px-4">
                SIGN UP
              </Button>
            </Link>
          </div>

          {/* Mobile Hamburger Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="lg:hidden p-2 text-text-primary hover:text-accent-primary transition-colors"
            aria-label="Toggle menu"
          >
            {isMobileMenuOpen ? (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            ) : (
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            )}
          </button>
        </div>

        {/* Mobile Menu Dropdown */}
        {isMobileMenuOpen && (
          <div className="lg:hidden mt-4 pb-4 border-t border-border-color pt-4 animate-slide-down">
            <div className="flex flex-col space-y-4">
              <Link
                to="/about"
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200 py-2"
              >
                ABOUT
              </Link>
              <Link
                to="/pricing"
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200 py-2"
              >
                PRICING
              </Link>
              <Link
                to="/help"
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200 py-2"
              >
                HELP CENTER
              </Link>
              <Link
                to="/contact"
                onClick={() => setIsMobileMenuOpen(false)}
                className="text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200 py-2"
              >
                CONTACT
              </Link>

              <div className="border-t border-border-color my-2"></div>

              <Link to="/login" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="secondary" size="sm" className="w-full">
                  LOG IN
                </Button>
              </Link>
              <Link to="/register" onClick={() => setIsMobileMenuOpen(false)}>
                <Button variant="primary" size="sm" className="w-full">
                  SIGN UP
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}
