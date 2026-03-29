import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ToastProvider } from './contexts/ToastContext';
import './App.css';

/**
 * Root App component with routing, error boundary, and toast notifications
 * Redux Provider and PersistGate are in main.tsx
 * 
 * Requirements: 30.1, 30.2, 30.3
 */
function App() {
  return (
    <ErrorBoundary>
      <ToastProvider>
        <RouterProvider router={router} />
      </ToastProvider>
    </ErrorBoundary>
  );
}

export default App;
