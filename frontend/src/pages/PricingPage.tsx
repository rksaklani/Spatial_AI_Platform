import { Link } from 'react-router-dom';
import { Button } from '../components/common/Button';
import { CheckIcon } from '@heroicons/react/24/outline';
import { PublicNav } from '../components/layout/PublicNav';
import { PublicFooter } from '../components/layout/PublicFooter';

export function PricingPage() {
  return (
    <div className="min-h-screen geometric-bg flex flex-col">
      <PublicNav />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 sm:py-16 lg:py-24 pt-24">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-text-primary mb-4">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-text-secondary">
            Choose the plan that fits your team's needs
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`bg-secondary-bg/60 backdrop-blur-md rounded-xl p-8 border ${
                plan.featured
                  ? 'border-accent-primary shadow-glow-lg scale-105'
                  : 'border-border-color shadow-glass'
              }`}
            >
              {plan.featured && (
                <div className="text-accent-primary text-sm font-semibold mb-4">
                  MOST POPULAR
                </div>
              )}
              <h3 className="text-2xl font-bold text-text-primary mb-2">{plan.name}</h3>
              <div className="mb-6">
                <span className="text-4xl font-bold text-text-primary">${plan.price}</span>
                <span className="text-text-secondary">/month</span>
              </div>
              <p className="text-text-secondary mb-6">{plan.description}</p>
              <Link to="/register">
                <Button
                  variant={plan.featured ? 'primary' : 'secondary'}
                  className="w-full mb-6"
                >
                  {plan.cta}
                </Button>
              </Link>
              <ul className="space-y-3">
                {plan.features.map((feature, i) => (
                  <li key={i} className="flex items-start text-sm">
                    <CheckIcon className="h-5 w-5 text-accent-primary mr-2 flex-shrink-0" />
                    <span className="text-text-secondary">{feature}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        <div className="bg-secondary-bg/60 backdrop-blur-md rounded-xl p-8 border border-border-color shadow-glass">
          <h2 className="text-2xl font-bold text-text-primary mb-6 text-center">
            Frequently Asked Questions
          </h2>
          <div className="space-y-6 max-w-3xl mx-auto">
            {faqs.map((faq, index) => (
              <div key={index}>
                <h3 className="text-lg font-semibold text-text-primary mb-2">{faq.question}</h3>
                <p className="text-text-secondary">{faq.answer}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
      <PublicFooter />
    </div>
  );
}

const plans = [
  {
    name: 'Starter',
    price: 0,
    description: 'Perfect for trying out Spatial AI',
    cta: 'Start Free Trial',
    featured: false,
    features: [
      '1 team member',
      '3 scenes',
      '5 GB storage',
      'Web viewer access',
      'Basic annotations',
      '15-day trial',
    ],
  },
  {
    name: 'Professional',
    price: 49,
    description: 'For small teams and projects',
    cta: 'Get Started',
    featured: true,
    features: [
      '5 team members',
      '25 scenes',
      '50 GB storage',
      'Real-time collaboration',
      'Advanced annotations',
      'Guided tours',
      'Scene comparison',
      'Priority support',
    ],
  },
  {
    name: 'Enterprise',
    price: 199,
    description: 'For large teams and organizations',
    cta: 'Contact Sales',
    featured: false,
    features: [
      'Unlimited team members',
      'Unlimited scenes',
      '500 GB storage',
      'All Professional features',
      'Custom branding',
      'SSO integration',
      'Dedicated support',
      'SLA guarantee',
    ],
  },
];

const faqs = [
  {
    question: 'Can I change plans later?',
    answer:
      'Yes, you can upgrade or downgrade your plan at any time. Changes take effect immediately, and billing is prorated.',
  },
  {
    question: 'What happens after the free trial?',
    answer:
      'After your 15-day trial ends, you can choose to upgrade to a paid plan or your account will be downgraded to the free tier with limited features.',
  },
  {
    question: 'Do you offer educational discounts?',
    answer:
      'Yes! We offer 50% discounts for educational institutions and non-profit organizations. Contact us for details.',
  },
  {
    question: 'What file formats do you support?',
    answer:
      'We support video files (MP4, MOV, AVI, WebM, MKV) for reconstruction, and 3D files (PLY, LAS, OBJ, GLTF, GLB, SPLAT, STL, FBX, DAE, E57, IFC, DXF) for direct import.',
  },
];
