/**
 * Login form component using RTK Query with Nira-inspired design
 * 
 * Features:
 * - Email and password authentication
 * - "Remember me" checkbox for persistent sessions (30 days)
 * - "Forgot password?" link for password recovery
 * - "Don't have an account? Register" link for new user registration
 * - Redirect to intended destination after successful login
 * - Demo mode for UI testing without backend
 * - Error handling with user-friendly notifications
 * - Loading states during authentication
 * 
 * Requirements: 1.1, 1.2, 1.7
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, useLocation, Link } from 'react-router-dom';
import { useLoginMutation } from '../store/api/authApi';
import { useDispatch } from 'react-redux';
import { loginSuccess } from '../store/slices/authSlice';
import { addNotification } from '../store/slices/uiSlice';
import { Button } from './common/Button';
import { GlassCard } from './common/GlassCard';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const location = useLocation();

  // RTK Query mutation hook
  const [login, { isLoading }] = useLoginMutation();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    try {
      // Call the login mutation
      const result = await login({ email, password }).unwrap();

      // Dispatch success action to update auth state
      dispatch(loginSuccess({
        user: result.user,
        token: result.token,
        refreshToken: result.refreshToken,
        expiresIn: 900, // 15 minutes default
      }));

      // Show success notification
      dispatch(
        addNotification({
          type: 'success',
          message: 'Welcome back!',
          duration: 3000,
        })
      );

      // Navigate to intended destination or default to dashboard
      const from = (location.state as any)?.from?.pathname || '/dashboard';
      navigate(from, { replace: true });
    } catch (error: any) {
      // Show error notification
      dispatch(
        addNotification({
          type: 'error',
          message: error.data?.message || 'Invalid email or password. Please try again.',
          duration: 5000,
        })
      );
    }
  };

  const handleDemoLogin = () => {
    // Demo login - bypass authentication for UI testing
    dispatch(
      loginSuccess({
        user: {
          id: 'demo-user',
          email: 'demo@example.com',
          name: 'Demo User',
          organizationId: 'demo-org',
        },
        token: 'demo-token',
        refreshToken: 'demo-refresh-token',
        expiresIn: 900,
      })
    );

    // Show success notification
    dispatch(
      addNotification({
        type: 'success',
        message: 'Welcome to Demo Mode!',
        duration: 3000,
      })
    );

    // Navigate to intended destination or default to dashboard
    const from = (location.state as any)?.from?.pathname || '/dashboard';
    navigate(from, { replace: true });
  };

  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Logo/Brand */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-display font-bold text-accent-primary mb-2">
          SPATIAL AI
        </h1>
        <p className="text-text-secondary">
          Sign in to your account
        </p>
      </div>

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Email Input */}
        <div className="space-y-2">
          <label 
            htmlFor="email" 
            className="block text-sm font-medium text-text-secondary"
          >
            Email Address
          </label>
          <input
            id="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
            className="w-full px-4 py-3 bg-primary-bg border border-border-color 
                     rounded-lg text-text-primary placeholder-text-muted
                     focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20
                     transition-all duration-200"
            placeholder="you@example.com"
          />
        </div>

        {/* Password Input */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <label 
              htmlFor="password" 
              className="block text-sm font-medium text-text-secondary"
            >
              Password
            </label>
            <Link 
              to="/forgot-password" 
              className="text-sm text-accent-primary hover:text-accent-secondary transition-colors"
            >
              Forgot password?
            </Link>
          </div>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
            className="w-full px-4 py-3 bg-primary-bg border border-border-color 
                     rounded-lg text-text-primary placeholder-text-muted
                     focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20
                     transition-all duration-200"
            placeholder="Enter your password"
          />
        </div>

        {/* Remember Me Checkbox */}
        <div className="flex items-center">
          <input
            id="remember-me"
            type="checkbox"
            checked={rememberMe}
            onChange={(e) => setRememberMe(e.target.checked)}
            className="w-4 h-4 rounded border-border-color text-accent-primary
                     focus:ring-2 focus:ring-accent-primary/20"
          />
          <label 
            htmlFor="remember-me" 
            className="ml-2 text-sm text-text-secondary cursor-pointer"
          >
            Remember me for 30 days
          </label>
        </div>

        {/* Submit Button */}
        <Button
          type="submit"
          variant="primary"
          size="lg"
          loading={isLoading}
          disabled={isLoading}
          className="w-full"
        >
          {isLoading ? 'Signing in...' : 'Sign In'}
        </Button>

        {/* Demo Mode Button */}
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-border-color"></div>
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-glass-bg text-text-muted">or</span>
          </div>
        </div>

        <Button
          type="button"
          variant="secondary"
          size="lg"
          onClick={handleDemoLogin}
          className="w-full"
        >
          Continue with Demo Mode
        </Button>
      </form>

      {/* Register Link */}
      <div className="mt-6 text-center">
        <p className="text-sm text-text-secondary">
          Don't have an account?{' '}
          <Link 
            to="/register" 
            className="text-accent-primary hover:text-accent-secondary font-medium transition-colors"
          >
            Create account
          </Link>
        </p>
      </div>
    </GlassCard>
  );
}
