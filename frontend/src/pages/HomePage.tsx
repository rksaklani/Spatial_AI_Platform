import { Link } from 'react-router-dom';
import { useState } from 'react';
import { Button } from '../components/common/Button';

/**
 * Public Home page - landing page for all visitors
 * Nira-inspired design with hero section and features
 */
export function HomePage() {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  return (
    <div className="min-h-screen geometric-bg flex flex-col">
      {/* Public Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-secondary-bg/80 backdrop-blur-xl border-b border-border-color shadow-glass">
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

            {/* Desktop Navigation Links - Hidden on mobile */}
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

            {/* Desktop Auth Buttons - Hidden on mobile */}
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
                // X icon when menu is open
                <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                // Hamburger icon when menu is closed
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
                {/* Navigation Links */}
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

                {/* Divider */}
                <div className="border-t border-border-color my-2"></div>

                {/* Auth Buttons */}
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

      {/* Main Content */}
      <main className="flex-1 pt-20">
        {/* Hero Section */}
        <div className="relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16 lg:py-24">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
              {/* Left: Text Content */}
              <div className="text-center lg:text-left">
                <div className="mb-4 sm:mb-6">
                  <span className="text-accent-primary text-xs sm:text-sm font-semibold tracking-wider uppercase">
                    COLLABORATION WITHOUT COMPROMISE
                  </span>
                </div>
                <h1 className="text-4xl sm:text-5xl md:text-6xl lg:text-7xl font-bold text-text-primary mb-4 sm:mb-6 leading-tight">
                  A Billion <span className="text-accent-primary">Points</span>
                  <br />
                  in Your Pocket
                </h1>
                <p className="text-base sm:text-lg md:text-xl text-text-secondary mb-8 sm:mb-10 leading-relaxed max-w-2xl mx-auto lg:mx-0">
                  Spatial AI is a collaborative platform for rendering <span className="italic">massive 3D models in real time</span>, enabling <span className="italic">interactive, web-based visualization</span> and inspection on <span className="italic">any device</span>, including smartphones and tablets.
                </p>
                <div className="flex gap-3 sm:gap-4 flex-wrap justify-center lg:justify-start">
                  <Link to="/register">
                    <Button variant="primary" size="lg" className="w-full sm:w-auto">
                      START TRIAL
                    </Button>
                  </Link>
                  <Button
                    variant="secondary"
                    size="lg"
                    className="w-full sm:w-auto"
                    onClick={() => {
                      document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    LEARN MORE
                  </Button>
                </div>
              </div>

              {/* Right: 3D Model Previews - Hidden on mobile, shown on tablet+ */}
              <div className="relative hidden md:block">
                <div className="grid grid-cols-2 gap-3 sm:gap-4">
                  {/* Large preview top */}
                  <div className="col-span-2 aspect-video bg-secondary-bg/60 backdrop-blur-md rounded-xl border border-border-color overflow-hidden group hover:border-accent-primary transition-all duration-300 shadow-glass">
                    <div className="w-full h-full flex items-center justify-center">
                      <svg
                        className="h-16 w-16 sm:h-20 sm:w-20 text-text-muted group-hover:text-accent-primary transition-colors"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                  </div>
                  {/* Two smaller previews bottom */}
                  {[1, 2].map((i) => (
                    <div
                      key={i}
                      className="aspect-square bg-secondary-bg/60 backdrop-blur-md rounded-xl border border-border-color overflow-hidden group hover:border-accent-primary transition-all duration-300 shadow-glass"
                    >
                      <div className="w-full h-full flex items-center justify-center">
                        <svg
                          className="h-12 w-12 sm:h-16 sm:w-16 text-text-muted group-hover:text-accent-primary transition-colors"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                          />
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1.5}
                            d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                          />
                        </svg>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Demos Section */}
        <div className="py-12 sm:py-16 lg:py-20">
          <div className="max-w-7xl mx-auto px-4 sm:px-6">
            <div className="text-center mb-8 sm:mb-12">
              <span className="text-accent-primary text-xs sm:text-sm font-semibold tracking-wider uppercase mb-3 block">
                SPATIAL AI IN ACTION
              </span>
              <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-3 sm:mb-4">
                Use Cases
              </h2>
              <p className="text-lg sm:text-xl text-text-secondary max-w-3xl mx-auto">
                View a selection of curated sample applications
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {demos.map((demo, index) => (
                <div
                  key={index}
                  className="bg-secondary-bg/60 backdrop-blur-md rounded-xl border border-border-color overflow-hidden group hover:border-accent-primary transition-all duration-300 shadow-glass"
                >
                  {/* Demo Icon */}
                  <div className="p-6 sm:p-8 flex items-center space-x-4">
                    <div className="text-accent-primary">{demo.icon}</div>
                    <div>
                      <h3 className="text-lg sm:text-xl font-bold text-text-primary mb-1">
                        {demo.title}
                      </h3>
                      <p className="text-xs sm:text-sm text-text-muted">{demo.category}</p>
                    </div>
                  </div>

                  {/* Demo Preview */}
                  <div className="aspect-video bg-primary-bg border-t border-b border-border-color overflow-hidden relative">
                    <div className="w-full h-full flex items-center justify-center">
                      <svg
                        className="h-16 w-16 sm:h-20 sm:w-20 text-text-muted group-hover:text-accent-primary transition-colors"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                        />
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={1.5}
                          d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                    </div>
                  </div>

                  {/* View Button */}
                  <div className="p-4 sm:p-6">
                    <button className="w-full text-center text-text-secondary hover:text-accent-primary font-medium text-sm transition-colors duration-200 flex items-center justify-center space-x-2">
                      <span>View Demo</span>
                      <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Features Section */}
        <div id="features" className="py-12 sm:py-16 lg:py-20 bg-secondary-bg/30 backdrop-blur-sm">
          <div className="max-w-7xl mx-auto px-4 sm:px-6">
            <div className="text-center mb-12 sm:mb-16">
              <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-3 sm:mb-4">
                Powerful Features
              </h2>
              <p className="text-lg sm:text-xl text-text-secondary">
                Everything you need to work with massive 3D datasets
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 sm:gap-8">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="bg-secondary-bg/60 backdrop-blur-md rounded-xl p-6 sm:p-8 border border-border-color hover:border-accent-primary transition-all duration-300 shadow-glass"
                >
                  <div className="text-accent-primary mb-4">{feature.icon}</div>
                  <h3 className="text-lg sm:text-xl font-bold text-text-primary mb-2 sm:mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-sm sm:text-base text-text-secondary leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="py-12 sm:py-16 lg:py-20">
          <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
            <h2 className="text-3xl sm:text-4xl font-bold text-text-primary mb-4 sm:mb-6">
              Ready to get started?
            </h2>
            <p className="text-lg sm:text-xl text-text-secondary mb-6 sm:mb-8">
              Transform your videos into interactive 3D scenes today
            </p>
            <Link to="/register">
              <Button variant="primary" size="lg" className="w-full sm:w-auto">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-color bg-secondary-bg/40 backdrop-blur-lg">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-8 sm:py-12">
          <div className="grid grid-cols-2 sm:grid-cols-2 lg:grid-cols-4 gap-6 sm:gap-8 mb-6 sm:mb-8">
            {/* Brand */}
            <div className="col-span-2 sm:col-span-2 lg:col-span-1">
              <div className="flex items-center space-x-2 sm:space-x-3 mb-3 sm:mb-4">
                <div className="w-8 h-8 sm:w-10 sm:h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center shadow-glow">
                  <span className="text-white font-bold text-lg sm:text-xl">S</span>
                </div>
                <span className="text-text-primary font-display font-bold text-lg sm:text-xl">
                  SPATIAL AI
                </span>
              </div>
              <p className="text-text-muted text-xs sm:text-sm">
                Collaborative 3D visualization platform
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="text-text-primary font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Product</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#features" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#docs" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Documentation
                  </a>
                </li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="text-text-primary font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Company</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#about" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    About
                  </a>
                </li>
                <li>
                  <a href="#contact" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Contact
                  </a>
                </li>
                <li>
                  <a href="#careers" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Careers
                  </a>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="text-text-primary font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Legal</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#privacy" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#terms" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                    Terms of Service
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-6 sm:pt-8 border-t border-border-color">
            <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
              <p className="text-text-muted text-xs sm:text-sm text-center sm:text-left">
                © 2024 Spatial AI Platform. All rights reserved.
              </p>
              <div className="flex space-x-4 sm:space-x-6">
                <a href="#twitter" className="text-text-muted hover:text-accent-primary transition-colors">
                  <span className="sr-only">Twitter</span>
                  <svg className="h-5 w-5 sm:h-6 sm:w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
                <a href="#github" className="text-text-muted hover:text-accent-primary transition-colors">
                  <span className="sr-only">GitHub</span>
                  <svg className="h-5 w-5 sm:h-6 sm:w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path fillRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clipRule="evenodd" />
                  </svg>
                </a>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

const demos = [
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
        />
      </svg>
    ),
    title: 'BIM & Construction',
    category: 'Architecture & Engineering',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
        />
      </svg>
    ),
    title: 'Site Documentation',
    category: 'Surveying & Inspection',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 4v16M17 4v16M3 8h4m10 0h4M3 12h18M3 16h4m10 0h4M4 20h16a1 1 0 001-1V5a1 1 0 00-1-1H4a1 1 0 00-1 1v14a1 1 0 001 1z"
        />
      </svg>
    ),
    title: 'Cultural Heritage',
    category: 'Historical Preservation',
  },
];

const features = [
  {
    icon: (
      <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
    title: 'Real-time Rendering',
    description:
      'Experience smooth, interactive 3D visualization with Gaussian splatting technology at 60 FPS.',
  },
  {
    icon: (
      <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z"
        />
      </svg>
    ),
    title: 'Any Device',
    description:
      'Access your 3D models on desktop, tablet, or smartphone with adaptive rendering.',
  },
  {
    icon: (
      <svg className="h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={1.5}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
    title: 'Collaboration',
    description:
      'Work together in real-time with annotations, guided tours, and shared viewing.',
  },
];
