import { Link } from 'react-router-dom';

export function PublicFooter() {
  return (
    <footer className="border-t border-border-color bg-secondary-bg/50 backdrop-blur-sm mt-auto shadow-glass">
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
                <Link to="/#features" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                  Features
                </Link>
              </li>
              <li>
                <Link to="/pricing" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                  Pricing
                </Link>
              </li>
              <li>
                <Link to="/help" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                  Documentation
                </Link>
              </li>
            </ul>
          </div>

          {/* Company */}
          <div>
            <h4 className="text-text-primary font-semibold mb-3 sm:mb-4 text-sm sm:text-base">Company</h4>
            <ul className="space-y-2">
              <li>
                <Link to="/about" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                  About
                </Link>
              </li>
              <li>
                <Link to="/contact" className="text-text-muted hover:text-accent-primary transition-colors text-xs sm:text-sm">
                  Contact
                </Link>
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
  );
}
