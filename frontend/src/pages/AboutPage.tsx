import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { PublicNav } from '../components/layout/PublicNav';
import { PublicFooter } from '../components/layout/PublicFooter';

export function AboutPage() {
  return (
    <div className="min-h-screen geometric-bg flex flex-col">
      <PublicNav />
      <div className="max-w-4xl mx-auto px-4 sm:px-6 py-12 sm:py-16 lg:py-24 pt-24">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-text-primary mb-4">
            About Spatial AI
          </h1>
          <p className="text-xl text-text-secondary">
            Transforming how teams visualize and collaborate on 3D data
          </p>
        </div>

        <div className="space-y-12">
          <section className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-8 border border-border-color shadow-glass">
            <h2 className="text-2xl font-bold text-text-primary mb-4">Our Mission</h2>
            <p className="text-text-secondary leading-relaxed">
              Spatial AI is built to democratize access to massive 3D datasets. We believe that powerful 3D visualization shouldn't require expensive hardware or complex software installations. Our platform enables teams to view, analyze, and collaborate on billion-point 3D models directly in their web browser, on any device.
            </p>
          </section>

          <section className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-8 border border-border-color shadow-glass">
            <h2 className="text-2xl font-bold text-text-primary mb-4">The Technology</h2>
            <p className="text-text-secondary leading-relaxed mb-4">
              At the core of Spatial AI is cutting-edge Gaussian splatting technology combined with intelligent streaming and level-of-detail management. This allows us to render photorealistic 3D scenes at 60 FPS on devices ranging from high-end workstations to smartphones.
            </p>
            <ul className="space-y-2 text-text-secondary">
              <li className="flex items-start">
                <span className="text-accent-primary mr-2">•</span>
                <span>Real-time Gaussian splatting rendering</span>
              </li>
              <li className="flex items-start">
                <span className="text-accent-primary mr-2">•</span>
                <span>Adaptive streaming based on network conditions</span>
              </li>
              <li className="flex items-start">
                <span className="text-accent-primary mr-2">•</span>
                <span>Multi-tenant architecture with enterprise-grade security</span>
              </li>
              <li className="flex items-start">
                <span className="text-accent-primary mr-2">•</span>
                <span>WebSocket-based real-time collaboration</span>
              </li>
            </ul>
          </section>

          <section className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-8 border border-border-color shadow-glass">
            <h2 className="text-2xl font-bold text-text-primary mb-4">Use Cases</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">Architecture & Construction</h3>
                <p className="text-text-secondary text-sm">
                  Review BIM models, track construction progress, and coordinate with stakeholders in real-time.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">Surveying & Inspection</h3>
                <p className="text-text-secondary text-sm">
                  Document sites with drone or terrestrial scans, measure distances, and generate reports.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">Cultural Heritage</h3>
                <p className="text-text-secondary text-sm">
                  Preserve and share historical sites and artifacts with photorealistic 3D captures.
                </p>
              </div>
              <div>
                <h3 className="text-lg font-semibold text-text-primary mb-2">Manufacturing</h3>
                <p className="text-text-secondary text-sm">
                  Inspect products, visualize assemblies, and collaborate on design reviews.
                </p>
              </div>
            </div>
          </section>

          <div className="text-center">
            <Link to="/register">
              <Button variant="primary" size="lg">
                Start Free Trial
              </Button>
            </Link>
          </div>
        </div>
      </div>
      <PublicFooter />
    </div>
  );
}
