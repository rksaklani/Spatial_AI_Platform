/**
 * Button Component Examples
 * 
 * This file demonstrates all Button variants and states.
 * Use this as a reference for implementing buttons throughout the app.
 */

import { Button } from './Button';

// Example icons (using simple emoji for demonstration)
const SearchIcon = () => <span>🔍</span>;
const UploadIcon = () => <span>📤</span>;
const SettingsIcon = () => <span>⚙️</span>;
const TrashIcon = () => <span>🗑️</span>;

export function ButtonExamples() {
  return (
    <div className="p-8 space-y-12 bg-primary-bg min-h-screen">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-display font-bold text-text-primary mb-8">
          Button Component Library
        </h1>

        {/* Primary Buttons */}
        <section className="mb-12">
          <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
            Primary Buttons
          </h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" size="sm">
              Small Primary
            </Button>
            <Button variant="primary" size="md">
              Medium Primary
            </Button>
            <Button variant="primary" size="lg">
              Large Primary
            </Button>
            <Button variant="primary" icon={<UploadIcon />}>
              With Icon
            </Button>
            <Button variant="primary" loading>
              Loading...
            </Button>
            <Button variant="primary" disabled>
              Disabled
            </Button>
          </div>
        </section>

        {/* Secondary Buttons */}
        <section className="mb-12">
          <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
            Secondary Buttons
          </h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="secondary" size="sm">
              Small Secondary
            </Button>
            <Button variant="secondary" size="md">
              Medium Secondary
            </Button>
            <Button variant="secondary" size="lg">
              Large Secondary
            </Button>
            <Button variant="secondary" icon={<SearchIcon />}>
              With Icon
            </Button>
            <Button variant="secondary" loading>
              Loading...
            </Button>
            <Button variant="secondary" disabled>
              Disabled
            </Button>
          </div>
        </section>

        {/* Ghost Buttons */}
        <section className="mb-12">
          <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
            Ghost Buttons
          </h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="ghost" size="sm">
              Small Ghost
            </Button>
            <Button variant="ghost" size="md">
              Medium Ghost
            </Button>
            <Button variant="ghost" size="lg">
              Large Ghost
            </Button>
            <Button variant="ghost" icon={<SettingsIcon />}>
              With Icon
            </Button>
            <Button variant="ghost" loading>
              Loading...
            </Button>
            <Button variant="ghost" disabled>
              Disabled
            </Button>
          </div>
        </section>

        {/* Icon Buttons */}
        <section className="mb-12">
          <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
            Icon Buttons
          </h2>
          <div className="flex flex-wrap gap-4">
            <Button variant="icon" size="sm" aria-label="Search">
              <SearchIcon />
            </Button>
            <Button variant="icon" size="md" aria-label="Upload">
              <UploadIcon />
            </Button>
            <Button variant="icon" size="lg" aria-label="Settings">
              <SettingsIcon />
            </Button>
            <Button variant="icon" aria-label="Delete" disabled>
              <TrashIcon />
            </Button>
          </div>
        </section>

        {/* Real-world Examples */}
        <section className="mb-12">
          <h2 className="text-2xl font-display font-bold text-text-primary mb-4">
            Real-world Examples
          </h2>
          <div className="space-y-6">
            {/* Upload Scene */}
            <div className="bg-secondary-bg rounded-xl p-6 border border-border-color">
              <h3 className="text-lg font-semibold text-text-primary mb-4">
                Upload Scene
              </h3>
              <div className="flex gap-3">
                <Button variant="primary" icon={<UploadIcon />}>
                  Upload Video
                </Button>
                <Button variant="secondary">
                  Browse Scenes
                </Button>
              </div>
            </div>

            {/* Scene Actions */}
            <div className="bg-secondary-bg rounded-xl p-6 border border-border-color">
              <h3 className="text-lg font-semibold text-text-primary mb-4">
                Scene Actions
              </h3>
              <div className="flex gap-3">
                <Button variant="primary">
                  View Scene
                </Button>
                <Button variant="secondary">
                  Edit Details
                </Button>
                <Button variant="ghost">
                  Share
                </Button>
                <Button variant="icon" aria-label="Delete scene">
                  <TrashIcon />
                </Button>
              </div>
            </div>

            {/* Form Actions */}
            <div className="bg-secondary-bg rounded-xl p-6 border border-border-color">
              <h3 className="text-lg font-semibold text-text-primary mb-4">
                Form Actions
              </h3>
              <div className="flex justify-end gap-3">
                <Button variant="ghost">
                  Cancel
                </Button>
                <Button variant="primary">
                  Save Changes
                </Button>
              </div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
