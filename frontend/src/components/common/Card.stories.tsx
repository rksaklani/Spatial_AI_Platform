import React from 'react';
import { Card } from './Card';
import { GlassCard } from './GlassCard';

/**
 * Card Component Examples
 * 
 * This file demonstrates various use cases for Card and GlassCard components
 */

export default {
  title: 'Components/Cards',
};

// Standard Card Examples
export const StandardCard = () => (
  <div className="p-8 bg-primary-bg min-h-screen">
    <h2 className="text-2xl font-bold text-text-primary mb-6">Standard Cards</h2>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {/* Basic Card */}
      <Card>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-2">Basic Card</h3>
          <p className="text-text-secondary">
            A simple card with default hover effects and styling.
          </p>
        </div>
      </Card>

      {/* Card with Image */}
      <Card>
        <div className="aspect-video bg-primary-bg" />
        <div className="p-4">
          <h3 className="text-lg font-semibold text-text-primary mb-1">
            Scene Card
          </h3>
          <p className="text-sm text-text-secondary mb-3">
            Card with thumbnail and content
          </p>
          <div className="flex items-center justify-between">
            <span className="text-xs text-text-muted">2 hours ago</span>
            <button className="text-accent-primary hover:text-accent-secondary">
              View →
            </button>
          </div>
        </div>
      </Card>

      {/* Clickable Card */}
      <Card onClick={() => alert('Card clicked!')}>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Clickable Card
          </h3>
          <p className="text-text-secondary">
            Click me to trigger an action!
          </p>
        </div>
      </Card>

      {/* Card without hover */}
      <Card hover={false}>
        <div className="p-6">
          <h3 className="text-lg font-semibold text-text-primary mb-2">
            Static Card
          </h3>
          <p className="text-text-secondary">
            No hover effects on this card.
          </p>
        </div>
      </Card>
    </div>
  </div>
);

// GlassCard Examples
export const GlassmorphismCards = () => (
  <div className="p-8 bg-primary-bg geometric-bg min-h-screen">
    <h2 className="text-2xl font-bold text-text-primary mb-6">Glass Cards</h2>
    
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      {/* Default Glass Card */}
      <GlassCard className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">
          Default Glass Card
        </h3>
        <p className="text-text-secondary">
          Semi-transparent with backdrop blur for overlay effects.
        </p>
      </GlassCard>

      {/* Glass Card with different blur levels */}
      <GlassCard blur="sm" className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">
          Light Blur (sm)
        </h3>
        <p className="text-text-secondary">
          Subtle blur effect for minimal glassmorphism.
        </p>
      </GlassCard>

      <GlassCard blur="md" className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">
          Medium Blur (md)
        </h3>
        <p className="text-text-secondary">
          Moderate blur for balanced effect.
        </p>
      </GlassCard>

      <GlassCard blur="lg" className="p-6">
        <h3 className="text-lg font-semibold text-text-primary mb-2">
          Large Blur (lg)
        </h3>
        <p className="text-text-secondary">
          Strong blur for prominent glassmorphism.
        </p>
      </GlassCard>
    </div>

    {/* Floating Toolbar Example */}
    <div className="mt-12">
      <h3 className="text-xl font-bold text-text-primary mb-4">
        Floating Toolbar Example
      </h3>
      <div className="relative h-64 bg-secondary-bg rounded-xl overflow-hidden">
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-text-muted">3D Viewer Area</p>
        </div>
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2">
          <GlassCard className="px-6 py-4">
            <div className="flex items-center space-x-6">
              <button className="text-text-secondary hover:text-text-primary transition-colors">
                📷 Camera
              </button>
              <button className="text-text-secondary hover:text-text-primary transition-colors">
                📍 Annotate
              </button>
              <button className="text-text-secondary hover:text-text-primary transition-colors">
                👥 Collaborate
              </button>
              <button className="text-text-secondary hover:text-text-primary transition-colors">
                ⚙️ Settings
              </button>
            </div>
          </GlassCard>
        </div>
      </div>
    </div>

    {/* Modal Example */}
    <div className="mt-12">
      <h3 className="text-xl font-bold text-text-primary mb-4">
        Modal Example
      </h3>
      <div className="relative h-96 bg-secondary-bg rounded-xl overflow-hidden flex items-center justify-center">
        <GlassCard className="max-w-md w-full mx-4">
          <div className="p-6 border-b border-border-color">
            <h2 className="text-2xl font-display font-bold text-text-primary">
              Upload Scene
            </h2>
          </div>
          <div className="p-6">
            <p className="text-text-secondary mb-4">
              Select a video file to create a new 3D scene reconstruction.
            </p>
            <div className="space-y-4">
              <input
                type="text"
                placeholder="Scene name..."
                className="w-full px-4 py-3 bg-primary-bg border border-border-color rounded-lg text-text-primary"
              />
              <div className="flex space-x-3">
                <button className="flex-1 px-4 py-2 border-2 border-accent-primary text-accent-primary rounded-lg font-medium hover:bg-accent-primary hover:text-white transition-all">
                  Cancel
                </button>
                <button className="flex-1 px-4 py-2 bg-accent-primary text-white rounded-lg font-medium hover:bg-accent-secondary transition-all">
                  Upload
                </button>
              </div>
            </div>
          </div>
        </GlassCard>
      </div>
    </div>
  </div>
);

// Scene Card Example (Real-world use case)
export const SceneCardExample = () => (
  <div className="p-8 bg-primary-bg geometric-bg min-h-screen">
    <h2 className="text-2xl font-bold text-text-primary mb-6">Scene Cards</h2>
    
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {[
        { name: 'Office Building', status: 'completed', date: '2 hours ago' },
        { name: 'Construction Site', status: 'processing', date: '5 hours ago' },
        { name: 'Warehouse Interior', status: 'completed', date: '1 day ago' },
      ].map((scene, index) => (
        <Card key={index} onClick={() => alert(`Opening ${scene.name}`)}>
          <div className="relative aspect-video bg-primary-bg">
            <div className="absolute inset-0 flex items-center justify-center text-text-muted">
              [Thumbnail]
            </div>
            <div className="absolute top-3 right-3">
              <span className={`px-3 py-1 rounded-full text-xs font-medium border ${
                scene.status === 'completed' 
                  ? 'bg-green-500/20 text-green-400 border-green-500/30'
                  : 'bg-blue-500/20 text-blue-400 border-blue-500/30'
              }`}>
                {scene.status}
              </span>
            </div>
          </div>
          <div className="p-4">
            <h3 className="text-lg font-semibold text-text-primary mb-1">
              {scene.name}
            </h3>
            <p className="text-sm text-text-secondary mb-3">
              3D reconstruction from video
            </p>
            <div className="flex items-center justify-between">
              <span className="text-xs text-text-muted">{scene.date}</span>
              <span className="text-accent-primary hover:text-accent-secondary transition-colors">
                View →
              </span>
            </div>
          </div>
        </Card>
      ))}
    </div>
  </div>
);
