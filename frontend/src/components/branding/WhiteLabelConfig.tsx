/**
 * White-Label Branding Configuration Component
 * 
 * Allows organizations to customize:
 * - Logo and favicon
 * - Color scheme (primary, secondary, accent)
 * - Company name and tagline
 * - Custom domain
 * - Email templates
 * - Login/signup page branding
 */

import React, { useState, useEffect } from 'react';
import { Button } from '../common';
import { PhotoIcon, SwatchIcon, GlobeAltIcon } from '@heroicons/react/24/outline';

interface BrandingConfig {
  logo_url?: string;
  favicon_url?: string;
  company_name: string;
  tagline?: string;
  primary_color: string;
  secondary_color: string;
  accent_color: string;
  custom_domain?: string;
  hide_powered_by: boolean;
  custom_css?: string;
}

export const WhiteLabelConfig: React.FC = () => {
  const [config, setConfig] = useState<BrandingConfig>({
    company_name: '',
    primary_color: '#3b82f6',
    secondary_color: '#1e40af',
    accent_color: '#06b6d4',
    hide_powered_by: false,
  });
  const [isSaving, setIsSaving] = useState(false);
  const [previewMode, setPreviewMode] = useState(false);

  useEffect(() => {
    loadBrandingConfig();
  }, []);

  const loadBrandingConfig = async () => {
    try {
      const response = await fetch('/api/v1/branding/config', {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      if (response.ok) {
        const data = await response.json();
        setConfig(data);
      }
    } catch (error) {
      console.error('Failed to load branding config:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);

    try {
      const response = await fetch('/api/v1/branding/config', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error('Failed to save branding config');
      }

      // Apply branding immediately
      applyBranding(config);
      
      alert('Branding configuration saved successfully!');
    } catch (error) {
      console.error('Failed to save branding config:', error);
      alert('Failed to save branding configuration');
    } finally {
      setIsSaving(false);
    }
  };

  const applyBranding = (branding: BrandingConfig) => {
    // Apply CSS variables
    document.documentElement.style.setProperty('--color-primary', branding.primary_color);
    document.documentElement.style.setProperty('--color-secondary', branding.secondary_color);
    document.documentElement.style.setProperty('--color-accent', branding.accent_color);

    // Update favicon
    if (branding.favicon_url) {
      const favicon = document.querySelector("link[rel*='icon']") as HTMLLinkElement;
      if (favicon) {
        favicon.href = branding.favicon_url;
      }
    }

    // Update title
    if (branding.company_name) {
      document.title = branding.company_name;
    }

    // Apply custom CSS
    if (branding.custom_css) {
      let styleElement = document.getElementById('custom-branding-css');
      if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = 'custom-branding-css';
        document.head.appendChild(styleElement);
      }
      styleElement.textContent = branding.custom_css;
    }
  };

  const handleLogoUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('logo', file);

    try {
      const response = await fetch('/api/v1/branding/upload/logo', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setConfig({ ...config, logo_url: data.url });
    } catch (error) {
      console.error('Logo upload failed:', error);
      alert('Failed to upload logo');
    }
  };

  const handleFaviconUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('favicon', file);

    try {
      const response = await fetch('/api/v1/branding/upload/favicon', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      setConfig({ ...config, favicon_url: data.url });
    } catch (error) {
      console.error('Favicon upload failed:', error);
      alert('Failed to upload favicon');
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-text-primary mb-2">White-Label Branding</h1>
        <p className="text-text-secondary">Customize the platform with your brand identity</p>
      </div>

      {/* Logo & Favicon */}
      <div className="bg-secondary-bg rounded-xl border border-border-color p-6 space-y-6">
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <PhotoIcon className="w-6 h-6" />
          Logo & Favicon
        </h2>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Logo
            </label>
            {config.logo_url && (
              <div className="mb-3 p-4 bg-primary-bg rounded-lg border border-border-subtle">
                <img src={config.logo_url} alt="Logo" className="max-h-16 mx-auto" />
              </div>
            )}
            <input
              type="file"
              accept="image/*"
              onChange={handleLogoUpload}
              className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary text-sm"
            />
            <p className="text-xs text-text-muted mt-1">
              Recommended: PNG or SVG, max 200px height
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Favicon
            </label>
            {config.favicon_url && (
              <div className="mb-3 p-4 bg-primary-bg rounded-lg border border-border-subtle">
                <img src={config.favicon_url} alt="Favicon" className="w-8 h-8 mx-auto" />
              </div>
            )}
            <input
              type="file"
              accept="image/x-icon,image/png"
              onChange={handleFaviconUpload}
              className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary text-sm"
            />
            <p className="text-xs text-text-muted mt-1">
              Recommended: ICO or PNG, 32x32px
            </p>
          </div>
        </div>
      </div>

      {/* Company Info */}
      <div className="bg-secondary-bg rounded-xl border border-border-color p-6 space-y-4">
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <GlobeAltIcon className="w-6 h-6" />
          Company Information
        </h2>

        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Company Name
          </label>
          <input
            type="text"
            value={config.company_name}
            onChange={(e) => setConfig({ ...config, company_name: e.target.value })}
            className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary"
            placeholder="Your Company Name"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Tagline (Optional)
          </label>
          <input
            type="text"
            value={config.tagline || ''}
            onChange={(e) => setConfig({ ...config, tagline: e.target.value })}
            className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary"
            placeholder="Your company tagline"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Custom Domain (Optional)
          </label>
          <input
            type="text"
            value={config.custom_domain || ''}
            onChange={(e) => setConfig({ ...config, custom_domain: e.target.value })}
            className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary"
            placeholder="viewer.yourcompany.com"
          />
          <p className="text-xs text-text-muted mt-1">
            Contact support to configure DNS settings
          </p>
        </div>
      </div>

      {/* Color Scheme */}
      <div className="bg-secondary-bg rounded-xl border border-border-color p-6 space-y-4">
        <h2 className="text-xl font-bold text-text-primary flex items-center gap-2">
          <SwatchIcon className="w-6 h-6" />
          Color Scheme
        </h2>

        <div className="grid grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Primary Color
            </label>
            <div className="flex gap-2">
              <input
                type="color"
                value={config.primary_color}
                onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                className="w-12 h-10 rounded border border-border-subtle cursor-pointer"
              />
              <input
                type="text"
                value={config.primary_color}
                onChange={(e) => setConfig({ ...config, primary_color: e.target.value })}
                className="flex-1 px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary font-mono text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Secondary Color
            </label>
            <div className="flex gap-2">
              <input
                type="color"
                value={config.secondary_color}
                onChange={(e) => setConfig({ ...config, secondary_color: e.target.value })}
                className="w-12 h-10 rounded border border-border-subtle cursor-pointer"
              />
              <input
                type="text"
                value={config.secondary_color}
                onChange={(e) => setConfig({ ...config, secondary_color: e.target.value })}
                className="flex-1 px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary font-mono text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-text-primary mb-2">
              Accent Color
            </label>
            <div className="flex gap-2">
              <input
                type="color"
                value={config.accent_color}
                onChange={(e) => setConfig({ ...config, accent_color: e.target.value })}
                className="w-12 h-10 rounded border border-border-subtle cursor-pointer"
              />
              <input
                type="text"
                value={config.accent_color}
                onChange={(e) => setConfig({ ...config, accent_color: e.target.value })}
                className="flex-1 px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary font-mono text-sm"
              />
            </div>
          </div>
        </div>

        {/* Color Preview */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <div
            className="h-20 rounded-lg flex items-center justify-center text-white font-medium"
            style={{ backgroundColor: config.primary_color }}
          >
            Primary
          </div>
          <div
            className="h-20 rounded-lg flex items-center justify-center text-white font-medium"
            style={{ backgroundColor: config.secondary_color }}
          >
            Secondary
          </div>
          <div
            className="h-20 rounded-lg flex items-center justify-center text-white font-medium"
            style={{ backgroundColor: config.accent_color }}
          >
            Accent
          </div>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="bg-secondary-bg rounded-xl border border-border-color p-6 space-y-4">
        <h2 className="text-xl font-bold text-text-primary">Advanced Options</h2>

        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={config.hide_powered_by}
            onChange={(e) => setConfig({ ...config, hide_powered_by: e.target.checked })}
            className="w-4 h-4 rounded border-border-subtle bg-surface-base text-accent-primary"
          />
          <span className="text-sm text-text-primary">
            Hide "Powered by Spatial AI" watermark
          </span>
        </label>

        <div>
          <label className="block text-sm font-medium text-text-primary mb-2">
            Custom CSS (Advanced)
          </label>
          <textarea
            value={config.custom_css || ''}
            onChange={(e) => setConfig({ ...config, custom_css: e.target.value })}
            className="w-full px-3 py-2 bg-surface-elevated border border-border-subtle rounded-lg text-text-primary font-mono text-sm"
            rows={6}
            placeholder=".custom-class { color: red; }"
          />
          <p className="text-xs text-text-muted mt-1">
            Add custom CSS to further customize the appearance
          </p>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-4">
        <Button
          variant="primary"
          onClick={handleSave}
          disabled={isSaving}
          className="flex-1"
        >
          {isSaving ? 'Saving...' : 'Save Branding Configuration'}
        </Button>
        <Button
          variant="secondary"
          onClick={() => {
            setPreviewMode(!previewMode);
            if (!previewMode) {
              applyBranding(config);
            } else {
              window.location.reload();
            }
          }}
        >
          {previewMode ? 'Exit Preview' : 'Preview'}
        </Button>
      </div>
    </div>
  );
};
