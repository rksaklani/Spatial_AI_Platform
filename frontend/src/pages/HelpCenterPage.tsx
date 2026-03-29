import { useState } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { PublicNav } from '../components/layout/PublicNav';
import { PublicFooter } from '../components/layout/PublicFooter';
import { Button } from '../components/common/Button';
import { Link } from 'react-router-dom';

export function HelpCenterPage() {
  const [searchQuery, setSearchQuery] = useState('');

  const filteredArticles = articles.filter(
    (article) =>
      article.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      article.description.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="min-h-screen geometric-bg flex flex-col">
      <PublicNav />
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-12 sm:py-16 lg:py-24 pt-24">
        <div className="text-center mb-12">
          <h1 className="text-4xl sm:text-5xl font-bold text-text-primary mb-4">
            Help Center
          </h1>
          <p className="text-xl text-text-secondary mb-8">
            Find answers and learn how to use Spatial AI
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto relative">
            <MagnifyingGlassIcon className="absolute left-4 top-1/2 transform -translate-y-1/2 h-5 w-5 text-text-muted" />
            <input
              type="text"
              placeholder="Search for help..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-4 py-3 bg-secondary-bg border border-border-color rounded-lg text-text-primary placeholder-text-muted focus:outline-none focus:ring-2 focus:ring-accent-primary"
            />
          </div>
        </div>

        {/* Categories */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
          {categories.map((category, index) => (
            <div
              key={index}
              className="bg-secondary-bg rounded-xl p-6 border border-border-color hover:border-accent-primary transition-all cursor-pointer"
            >
              <div className="text-accent-primary mb-4">{category.icon}</div>
              <h3 className="text-lg font-bold text-text-primary mb-2">{category.name}</h3>
              <p className="text-text-secondary text-sm">{category.description}</p>
            </div>
          ))}
        </div>

        {/* Articles */}
        <div className="bg-secondary-bg rounded-xl p-8 border border-border-color">
          <h2 className="text-2xl font-bold text-text-primary mb-6">Popular Articles</h2>
          <div className="space-y-4">
            {filteredArticles.map((article, index) => (
              <div
                key={index}
                className="p-4 border border-border-color rounded-lg hover:border-accent-primary transition-all cursor-pointer"
              >
                <h3 className="text-lg font-semibold text-text-primary mb-2">{article.title}</h3>
                <p className="text-text-secondary text-sm">{article.description}</p>
              </div>
            ))}
            {filteredArticles.length === 0 && (
              <p className="text-text-muted text-center py-8">
                No articles found matching your search.
              </p>
            )}
          </div>
        </div>

        {/* Contact Support */}
        <div className="mt-12 text-center bg-secondary-bg rounded-xl p-8 border border-border-color">
          <h2 className="text-2xl font-bold text-text-primary mb-4">Still need help?</h2>
          <p className="text-text-secondary mb-6">
            Our support team is here to assist you
          </p>
          <Link to="/contact">
            <Button variant="primary" size="lg">
              Contact Support
            </Button>
          </Link>
        </div>
      </div>
      <PublicFooter />
    </div>
  );
}

const categories = [
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 10V3L4 14h7v7l9-11h-7z"
        />
      </svg>
    ),
    name: 'Getting Started',
    description: 'Learn the basics of Spatial AI',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
        />
      </svg>
    ),
    name: 'Uploading & Processing',
    description: 'How to upload videos and 3D files',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
        />
      </svg>
    ),
    name: 'Viewing & Navigation',
    description: 'Navigate and interact with 3D scenes',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
        />
      </svg>
    ),
    name: 'Collaboration',
    description: 'Work together with your team',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
      </svg>
    ),
    name: 'Annotations & Reports',
    description: 'Add notes and generate reports',
  },
  {
    icon: (
      <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
        />
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
        />
      </svg>
    ),
    name: 'Account & Settings',
    description: 'Manage your account and preferences',
  },
];

const articles = [
  {
    title: 'How to upload your first video',
    description: 'Step-by-step guide to uploading and processing video files for 3D reconstruction',
  },
  {
    title: 'Importing existing 3D models',
    description: 'Learn how to import PLY, LAS, OBJ, GLTF, and other 3D file formats',
  },
  {
    title: 'Navigating the 3D viewer',
    description: 'Master the controls for panning, rotating, and zooming in 3D scenes',
  },
  {
    title: 'Creating and managing organizations',
    description: 'Set up your team workspace and invite collaborators',
  },
  {
    title: 'Adding annotations to scenes',
    description: 'Mark up your 3D models with text, measurements, and custom markers',
  },
  {
    title: 'Sharing scenes with external users',
    description: 'Generate public links and control access permissions',
  },
  {
    title: 'Real-time collaboration features',
    description: 'Work together with your team using live cursors and annotations',
  },
  {
    title: 'Creating guided tours',
    description: 'Build interactive walkthroughs of your 3D scenes',
  },
  {
    title: 'Comparing multiple scenes',
    description: 'Visualize changes between different versions or time periods',
  },
  {
    title: 'Generating reports',
    description: 'Export measurements, annotations, and snapshots as PDF reports',
  },
];
