import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';

/**
 * Public Home page - landing page for all visitors
 * Nira-inspired design with hero section and features
 */
export function HomePage() {
  return (
    <div className="min-h-screen geometric-bg flex flex-col">
      {/* Public Navigation Bar */}
      <nav className="fixed top-0 left-0 right-0 z-50 bg-secondary-bg/95 backdrop-blur-xl border-b border-border-color">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            {/* Logo and Brand */}
            <Link to="/" className="flex items-center space-x-3 group">
              <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center shadow-glow group-hover:shadow-xl transition-all duration-200">
                <span className="text-white font-bold text-xl">S</span>
              </div>
              <span className="text-text-primary font-display font-bold text-xl group-hover:text-accent-primary transition-colors duration-200">
                SPATIAL AI
              </span>
            </Link>

            {/* Navigation Links */}
            <div className="hidden md:flex items-center space-x-8">
              <a
                href="#features"
                className="text-text-secondary hover:text-text-primary font-medium transition-colors duration-200"
              >
                ABOUT
              </a>
              <a
                href="#pricing"
                className="text-text-secondary hover:text-text-primary font-medium transition-colors duration-200"
              >
                PRICING
              </a>
              <a
                href="#docs"
                className="text-text-secondary hover:text-text-primary font-medium transition-colors duration-200"
              >
                HELP CENTER
              </a>
              <a
                href="#contact"
                className="text-text-secondary hover:text-text-primary font-medium transition-colors duration-200"
              >
                CONTACT
              </a>
            </div>

            {/* Auth Buttons */}
            <div className="flex items-center space-x-4">
              <Link to="/login">
                <Button variant="secondary" size="sm">
                  LOG IN
                </Button>
              </Link>
              <Link to="/register">
                <Button variant="primary" size="sm">
                  SIGN UP
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="flex-1 pt-20">
        {/* Hero Section */}
        <div className="relative overflow-hidden">
          <div className="max-w-7xl mx-auto px-6 py-20 sm:py-32">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
              {/* Left: Text Content */}
              <div>
                <div className="mb-6">
                  <span className="text-accent-primary text-sm font-semibold tracking-wider uppercase">
                    COLLABORATION WITHOUT COMPROMISE
                  </span>
                </div>
                <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold text-text-primary mb-6 leading-tight">
                  A Billion <span className="text-accent-primary">Points</span>
                  <br />
                  in Your Pocket
                </h1>
                <p className="text-lg sm:text-xl text-text-secondary mb-10 leading-relaxed">
                  Spatial AI is a collaborative platform for rendering <span className="italic">massive 3D models in real time</span>, enabling <span className="italic">interactive, web-based visualization</span> and inspection on <span className="italic">any device</span>, including smartphones and tablets.
                </p>
                <div className="flex gap-4 flex-wrap">
                  <Link to="/register">
                    <Button variant="primary" size="lg">
                      START TRIAL
                    </Button>
                  </Link>
                  <Button
                    variant="secondary"
                    size="lg"
                    onClick={() => {
                      document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' });
                    }}
                  >
                    LEARN MORE
                  </Button>
                </div>
              </div>

              {/* Right: 3D Model Previews */}
              <div className="relative hidden lg:block">
                <div className="grid grid-cols-2 gap-4">
                  {/* Large preview top */}
                  <div className="col-span-2 aspect-video bg-secondary-bg rounded-xl border border-border-color overflow-hidden group hover:border-accent-primary transition-all duration-300">
                    <div className="w-full h-full flex items-center justify-center">
                      <svg
                        className="h-20 w-20 text-text-muted group-hover:text-accent-primary transition-colors"
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
                      className="aspect-square bg-secondary-bg rounded-xl border border-border-color overflow-hidden group hover:border-accent-primary transition-all duration-300"
                    >
                      <div className="w-full h-full flex items-center justify-center">
                        <svg
                          className="h-16 w-16 text-text-muted group-hover:text-accent-primary transition-colors"
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

        {/* Features Section */}
        <div id="features" className="py-20 bg-secondary-bg/50">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-16">
              <h2 className="text-4xl font-bold text-text-primary mb-4">
                Powerful Features
              </h2>
              <p className="text-xl text-text-secondary">
                Everything you need to work with massive 3D datasets
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {features.map((feature, index) => (
                <div
                  key={index}
                  className="bg-secondary-bg rounded-xl p-8 border border-border-color hover:border-accent-primary transition-all duration-300"
                >
                  <div className="text-accent-primary mb-4">{feature.icon}</div>
                  <h3 className="text-xl font-bold text-text-primary mb-3">
                    {feature.title}
                  </h3>
                  <p className="text-text-secondary leading-relaxed">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CTA Section */}
        <div className="py-20">
          <div className="max-w-4xl mx-auto px-6 text-center">
            <h2 className="text-4xl font-bold text-text-primary mb-6">
              Ready to get started?
            </h2>
            <p className="text-xl text-text-secondary mb-8">
              Transform your videos into interactive 3D scenes today
            </p>
            <Link to="/register">
              <Button variant="primary" size="lg">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-color bg-secondary-bg/50">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            {/* Brand */}
            <div className="col-span-1">
              <div className="flex items-center space-x-3 mb-4">
                <div className="w-10 h-10 bg-gradient-to-br from-accent-primary to-accent-secondary rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-xl">S</span>
                </div>
                <span className="text-text-primary font-display font-bold text-xl">
                  SPATIAL AI
                </span>
              </div>
              <p className="text-text-muted text-sm">
                Collaborative 3D visualization platform
              </p>
            </div>

            {/* Product */}
            <div>
              <h4 className="text-text-primary font-semibold mb-4">Product</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#features" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Features
                  </a>
                </li>
                <li>
                  <a href="#pricing" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Pricing
                  </a>
                </li>
                <li>
                  <a href="#docs" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Documentation
                  </a>
                </li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="text-text-primary font-semibold mb-4">Company</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#about" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    About
                  </a>
                </li>
                <li>
                  <a href="#contact" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Contact
                  </a>
                </li>
                <li>
                  <a href="#careers" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Careers
                  </a>
                </li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="text-text-primary font-semibold mb-4">Legal</h4>
              <ul className="space-y-2">
                <li>
                  <a href="#privacy" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#terms" className="text-text-muted hover:text-accent-primary transition-colors text-sm">
                    Terms of Service
                  </a>
                </li>
              </ul>
            </div>
          </div>

          {/* Bottom Bar */}
          <div className="pt-8 border-t border-border-color">
            <div className="flex flex-col md:flex-row justify-between items-center space-y-4 md:space-y-0">
              <p className="text-text-muted text-sm">
                © 2024 Spatial AI Platform. All rights reserved.
              </p>
              <div className="flex space-x-6">
                <a href="#twitter" className="text-text-muted hover:text-accent-primary transition-colors">
                  <span className="sr-only">Twitter</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
                  </svg>
                </a>
                <a href="#github" className="text-text-muted hover:text-accent-primary transition-colors">
                  <span className="sr-only">GitHub</span>
                  <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
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
