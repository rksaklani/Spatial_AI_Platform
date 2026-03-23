import { RouterProvider } from 'react-router-dom';
import { router } from './router';
import './App.css';

/**
 * Root App component with routing
 * Redux Provider and PersistGate are in main.tsx
 * 
 * Requirements: 30.1, 30.2, 30.3
 */
function App() {
  return <RouterProvider router={router} />;
}

export default App;
