import { RegisterForm } from '../components/RegisterForm';

/**
 * Register page component - user registration entry point
 * Rendered within PublicLayout via router
 * 
 * Features:
 * - Uses PublicLayout (configured in router)
 * - Integrates RegisterForm component with all registration features
 * - Registration form with validation
 * - Fields: email, password, confirm password, full name
 * - Integrates with auth API
 * - Redirects to login page on success
 * 
 * Requirements: 1.2, 1.7
 */
export function RegisterPage() {
  return <RegisterForm />;
}
