import { useState } from 'react';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from './store';
import { LoginForm } from './components/LoginForm';
import { GaussianViewer } from './components/GaussianViewer';
import { AdaptiveRenderer } from './components/AdaptiveRenderer';
import './App.css';

type Page = 'home' | 'login' | 'viewer' | 'adaptive';

function App() {
  const [currentPage, setCurrentPage] = useState<Page>('home');
  const [sceneId, setSceneId] = useState('demo');

  return (
    <Provider store={store}>
      <PersistGate loading={<LoadingScreen />} persistor={persistor}>
        {currentPage === 'home' && (
          <HomePage 
            onNavigate={(page, id) => {
              setCurrentPage(page);
              if (id) setSceneId(id);
            }} 
          />
        )}
        {currentPage === 'login' && (
          <LoginPage onBack={() => setCurrentPage('home')} />
        )}
        {currentPage === 'viewer' && (
          <ViewerPage sceneId={sceneId} onBack={() => setCurrentPage('home')} />
        )}
        {currentPage === 'adaptive' && (
          <AdaptiveViewerPage sceneId={sceneId} onBack={() => setCurrentPage('home')} />
        )}
      </PersistGate>
    </Provider>
  );
}

// Loading screen component
function LoadingScreen() {
  return (
    <div style={{ 
      display: 'flex', 
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100vh',
      background: '#1a1a1a',
      color: 'white',
      fontSize: '1.5rem',
    }}>
      Loading...
    </div>
  );
}

// Home page component
interface HomePageProps {
  onNavigate: (page: Page, sceneId?: string) => void;
}

function HomePage({ onNavigate }: HomePageProps) {
  return (
    <div style={{ 
      display: 'flex', 
      flexDirection: 'column',
      alignItems: 'center', 
      justifyContent: 'center', 
      height: '100vh',
      background: '#1a1a1a',
      color: 'white',
      fontFamily: 'system-ui, -apple-system, sans-serif',
      padding: '2rem',
    }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '1rem', textAlign: 'center' }}>
        Ultimate Spatial AI Platform
      </h1>
      <p style={{ fontSize: '1.2rem', marginBottom: '2rem', opacity: 0.8, textAlign: 'center' }}>
        Transform phone videos and 3D files into streamable, interactive 3D scenes
      </p>
      <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
        <button 
          onClick={() => onNavigate('login')}
          style={{ 
            padding: '12px 24px', 
            background: '#646cff', 
            color: 'white', 
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            cursor: 'pointer',
          }}
        >
          Login
        </button>
        <button 
          onClick={() => onNavigate('viewer', 'demo')}
          style={{ 
            padding: '12px 24px', 
            background: '#535bf2', 
            color: 'white', 
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            cursor: 'pointer',
          }}
        >
          View Demo Scene
        </button>
        <button 
          onClick={() => onNavigate('adaptive', 'demo')}
          style={{ 
            padding: '12px 24px', 
            background: '#42b883', 
            color: 'white', 
            border: 'none',
            borderRadius: '8px',
            fontSize: '1rem',
            cursor: 'pointer',
          }}
        >
          Adaptive Viewer Demo
        </button>
      </div>
      <div style={{ marginTop: '3rem', opacity: 0.6, fontSize: '0.9rem', maxWidth: '600px' }}>
        <p style={{ fontWeight: 'bold', marginBottom: '0.5rem' }}>Features:</p>
        <ul style={{ textAlign: 'left', marginTop: '0.5rem', lineHeight: '1.8' }}>
          <li>Real-time 3D Gaussian Splatting rendering</li>
          <li>Intelligent tile streaming with LOD</li>
          <li>Adaptive client/server-side rendering</li>
          <li>BIM element visualization</li>
          <li>Animated model playback</li>
          <li>2D overlay support</li>
          <li>Touch controls for mobile</li>
          <li>Browser compatibility (Chrome, Safari, Firefox, Edge)</li>
        </ul>
      </div>
    </div>
  );
}

// Login page component
interface LoginPageProps {
  onBack: () => void;
}

function LoginPage({ onBack }: LoginPageProps) {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <button
        onClick={onBack}
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          padding: '8px 16px',
          background: '#646cff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          zIndex: 1000,
        }}
      >
        ← Back
      </button>
      <LoginForm />
    </div>
  );
}

// Viewer page component
interface ViewerPageProps {
  sceneId: string;
  onBack: () => void;
}

function ViewerPage({ sceneId, onBack }: ViewerPageProps) {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <button
        onClick={onBack}
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          padding: '8px 16px',
          background: '#646cff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          zIndex: 1000,
        }}
      >
        ← Back
      </button>
      <GaussianViewer 
        sceneId={sceneId}
        onError={(error) => console.error('Viewer error:', error)}
        onLoadProgress={(progress) => console.log('Load progress:', progress)}
        onFpsUpdate={(fps) => console.log('FPS:', fps)}
        enableBIMVisualization={true}
        enable2DOverlays={true}
        enableAnimations={true}
      />
    </div>
  );
}

// Adaptive viewer page component
interface AdaptiveViewerPageProps {
  sceneId: string;
  onBack: () => void;
}

function AdaptiveViewerPage({ sceneId, onBack }: AdaptiveViewerPageProps) {
  return (
    <div style={{ width: '100vw', height: '100vh', position: 'relative' }}>
      <button
        onClick={onBack}
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          padding: '8px 16px',
          background: '#646cff',
          color: 'white',
          border: 'none',
          borderRadius: '5px',
          cursor: 'pointer',
          zIndex: 1000,
        }}
      >
        ← Back
      </button>
      <AdaptiveRenderer 
        sceneId={sceneId}
        onError={(error) => console.error('Renderer error:', error)}
        onModeChange={(mode) => console.log('Render mode:', mode)}
      />
    </div>
  );
}

export default App;
