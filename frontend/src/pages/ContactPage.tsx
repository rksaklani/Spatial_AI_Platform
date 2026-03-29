import { useState } from 'react';
import { Button } from '../components/common/Button';
import { EnvelopeIcon, PhoneIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { PublicNav } from '../components/layout/PublicNav';

export function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    subject: '',
    message: '',
  });
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement actual form submission
    setSubmitted(true);
    setTimeout(() => setSubmitted(false), 3000);
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
  };

  return (
    <div className="min-h-screen geometric-bg">
      <PublicNav />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12 sm:py-16 lg:py-24 pt-24">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-text-primary mb-4">
            Contact Us
          </h1>
          <p className="text-xl text-text-secondary">
            Get in touch with our team
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Contact Information */}
          <div className="space-y-6">
            <div className="bg-secondary-bg rounded-xl p-6 border border-border-color">
              <div className="flex items-start space-x-4">
                <div className="text-accent-primary">
                  <EnvelopeIcon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-text-primary mb-1">Email</h3>
                  <p className="text-text-secondary text-sm">support@spatialai.com</p>
                  <p className="text-text-secondary text-sm">sales@spatialai.com</p>
                </div>
              </div>
            </div>

            <div className="bg-secondary-bg rounded-xl p-6 border border-border-color">
              <div className="flex items-start space-x-4">
                <div className="text-accent-primary">
                  <PhoneIcon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-text-primary mb-1">Phone</h3>
                  <p className="text-text-secondary text-sm">+1 (555) 123-4567</p>
                  <p className="text-text-muted text-xs mt-1">Mon-Fri, 9am-6pm EST</p>
                </div>
              </div>
            </div>

            <div className="bg-secondary-bg rounded-xl p-6 border border-border-color">
              <div className="flex items-start space-x-4">
                <div className="text-accent-primary">
                  <MapPinIcon className="h-6 w-6" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-text-primary mb-1">Office</h3>
                  <p className="text-text-secondary text-sm">
                    123 Innovation Drive
                    <br />
                    San Francisco, CA 94105
                    <br />
                    United States
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Contact Form */}
          <div className="lg:col-span-2">
            <div className="bg-secondary-bg rounded-xl p-8 border border-border-color">
              <h2 className="text-2xl font-bold text-text-primary mb-6">Send us a message</h2>
              
              {submitted && (
                <div className="mb-6 p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
                  <p className="text-green-400 text-sm">
                    Thank you for your message! We'll get back to you soon.
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-6">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-text-primary mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    placeholder="Your name"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-text-primary mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary"
                    placeholder="your.email@example.com"
                  />
                </div>

                <div>
                  <label htmlFor="subject" className="block text-sm font-medium text-text-primary mb-2">
                    Subject
                  </label>
                  <select
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="w-full px-4 py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
                  >
                    <option value="">Select a subject</option>
                    <option value="general">General Inquiry</option>
                    <option value="support">Technical Support</option>
                    <option value="sales">Sales Question</option>
                    <option value="billing">Billing Issue</option>
                    <option value="feature">Feature Request</option>
                    <option value="other">Other</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="message" className="block text-sm font-medium text-text-primary mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={6}
                    className="w-full px-4 py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary resize-none"
                    placeholder="Tell us how we can help..."
                  />
                </div>

                <Button type="submit" variant="primary" className="w-full">
                  Send Message
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
