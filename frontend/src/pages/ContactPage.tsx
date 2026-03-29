import { useState } from 'react';
import { Button } from '../components/common/Button';
import { EnvelopeIcon, PhoneIcon, MapPinIcon } from '@heroicons/react/24/outline';
import { PublicNav } from '../components/layout/PublicNav';
import { PublicFooter } from '../components/layout/PublicFooter';

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
    <div className="min-h-screen geometric-bg flex flex-col w-full">
      <PublicNav />
      <div className="w-full max-w-6xl mx-auto px-4 sm:px-6 py-12 sm:py-16 lg:py-24 pt-20 sm:pt-24">
        <div className="text-center mb-8 sm:mb-12">
          <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold text-text-primary mb-3 sm:mb-4">
            Contact Us
          </h1>
          <p className="text-lg sm:text-xl text-text-secondary">
            Get in touch with our team
          </p>
        </div>

        <div className="w-full grid grid-cols-1 lg:grid-cols-3 gap-4 sm:gap-6 lg:gap-8">
          {/* Contact Information */}
          <div className="space-y-4 order-2 lg:order-1 w-full">
            <div className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-border-color shadow-glass w-full">
              <div className="flex items-start space-x-3 sm:space-x-4">
                <div className="text-accent-primary flex-shrink-0">
                  <EnvelopeIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-base sm:text-lg font-semibold text-text-primary mb-1">Email</h3>
                  <p className="text-text-secondary text-xs sm:text-sm break-words">support@spatialai.com</p>
                  <p className="text-text-secondary text-xs sm:text-sm break-words">sales@spatialai.com</p>
                </div>
              </div>
            </div>

            <div className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-border-color shadow-glass w-full">
              <div className="flex items-start space-x-3 sm:space-x-4">
                <div className="text-accent-primary flex-shrink-0">
                  <PhoneIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-base sm:text-lg font-semibold text-text-primary mb-1">Phone</h3>
                  <p className="text-text-secondary text-xs sm:text-sm">+1 (555) 123-4567</p>
                  <p className="text-text-muted text-xs mt-1">Mon-Fri, 9am-6pm EST</p>
                </div>
              </div>
            </div>

            <div className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-4 sm:p-6 border border-border-color shadow-glass w-full">
              <div className="flex items-start space-x-3 sm:space-x-4">
                <div className="text-accent-primary flex-shrink-0">
                  <MapPinIcon className="h-5 w-5 sm:h-6 sm:w-6" />
                </div>
                <div className="min-w-0 flex-1">
                  <h3 className="text-base sm:text-lg font-semibold text-text-primary mb-1">Office</h3>
                  <p className="text-text-secondary text-xs sm:text-sm">
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
          <div className="lg:col-span-2 order-1 lg:order-2">
            <div className="bg-secondary-bg/70 backdrop-blur-sm rounded-xl p-6 sm:p-8 border border-border-color shadow-glass">
              <h2 className="text-xl sm:text-2xl font-bold text-text-primary mb-4 sm:mb-6">Send us a message</h2>
              
              {submitted && (
                <div className="mb-4 sm:mb-6 p-3 sm:p-4 bg-green-500/20 border border-green-500/30 rounded-lg">
                  <p className="text-green-400 text-xs sm:text-sm">
                    Thank you for your message! We'll get back to you soon.
                  </p>
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4 sm:space-y-6">
                <div>
                  <label htmlFor="name" className="block text-xs sm:text-sm font-medium text-text-primary mb-2">
                    Name
                  </label>
                  <input
                    type="text"
                    id="name"
                    name="name"
                    value={formData.name}
                    onChange={handleChange}
                    required
                    className="w-full px-3 sm:px-4 py-2 sm:py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary text-sm sm:text-base"
                    placeholder="Your name"
                  />
                </div>

                <div>
                  <label htmlFor="email" className="block text-xs sm:text-sm font-medium text-text-primary mb-2">
                    Email
                  </label>
                  <input
                    type="email"
                    id="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    className="w-full px-3 sm:px-4 py-2 sm:py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary text-sm sm:text-base"
                    placeholder="your.email@example.com"
                  />
                </div>

                <div>
                  <label htmlFor="subject" className="block text-xs sm:text-sm font-medium text-text-primary mb-2">
                    Subject
                  </label>
                  <select
                    id="subject"
                    name="subject"
                    value={formData.subject}
                    onChange={handleChange}
                    required
                    className="w-full px-3 sm:px-4 py-2 sm:py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary text-sm sm:text-base"
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
                  <label htmlFor="message" className="block text-xs sm:text-sm font-medium text-text-primary mb-2">
                    Message
                  </label>
                  <textarea
                    id="message"
                    name="message"
                    value={formData.message}
                    onChange={handleChange}
                    required
                    rows={5}
                    className="w-full px-3 sm:px-4 py-2 sm:py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary resize-none text-sm sm:text-base"
                    placeholder="Tell us how we can help..."
                  />
                </div>

                <Button type="submit" variant="primary" className="w-full text-sm sm:text-base">
                  Send Message
                </Button>
              </form>
            </div>
          </div>
        </div>
      </div>
      <PublicFooter />
    </div>
  );
}
