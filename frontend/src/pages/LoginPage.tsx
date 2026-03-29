import { LoginForm } from '../components/LoginForm';

/**
 * Login page component - authentication entry point
 * Rendered within PublicLayout via router
 * 
 * Features:
 * - Uses PublicLayout (configured in router)
 * - Integrates LoginForm component with all authentication features
 * - "Remember me" checkbox for extended sessions
 * - "Forgot password?" link for password recovery
 * - "Don't have an account? Register" link for new users
 * - Handles login success with redirect to intended destination
 * 
 * Requirements: 1.1, 1.2, 1.7
 */
export function LoginPage() {
  return <LoginForm />;
}
