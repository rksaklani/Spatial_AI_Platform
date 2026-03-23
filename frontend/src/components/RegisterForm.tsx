/**
 * Register form component using RTK Query with Nira-inspired design
 * 
 * Features:
 * - Email, password, confirm password, and full name fields
 * - Client-side validation (password match, minimum length)
 * - Integration with auth API via RTK Query
 * - Auto-login after successful registration
 * - Redirect to dashboard on success
 * - Error handling with user-friendly notifications
 * - Loading states during registration and auto-login
 * 
 * Requirements: 1.2, 1.7
 */

import { useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useRegisterMutation, useLoginMutation } from '../store/api/authApi';
import { useDispatch } from 'react-redux';
import { loginSuccess } from '../store/slices/authSlice';
import { addNotification } from '../store/slices/uiSlice';
import { Button } from './common/Button';
import { GlassCard } from './common/GlassCard';

export function RegisterForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();

  // RTK Query mutation hooks
  const [register, { isLoading: isRegistering }] = useRegisterMutation();
  const [login, { isLoading: isLoggingIn }] = useLoginMutation();
  
  const isLoading = isRegistering || isLoggingIn;

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    // Validate passwords match
    if (password !== confirmPassword) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Passwords do not match',
          duration: 5000,
        })
      );
      return;
    }

    // Validate password strength
    if (password.length < 8) {
      dispatch(
        addNotification({
          type: 'error',
          message: 'Password must be at least 8 characters long',
          duration: 5000,
        })
      );
      return;
    }

    try {
      // Step 1: Register the user
      await register({
        email,
        password,
        full_name: fullName,
      }).unwrap();

      // Step 2: Auto-login after successful registration
      const loginResult = await login({ email, password }).unwrap();

      // Step 3: Update auth state
      dispatch(loginSuccess({
        user: loginResult.user,
        token: loginResult.token,
        refreshToken: loginResult.refreshToken,
        expiresIn: 900, // 15 minutes default
      }));

      // Show success notification
      dispatch(
        addNotification({
          type: 'success',
          message: 'Welcome! Your account has been created.',
          duration: 3000,
        })
      );

      // Redirect to dashboard
      navigate('/dashboard', { replace: true });
    } catch (error: any) {
      // Show error notification
      dispatch(
        addNotification({
          type: 'error',
          message: error.data?.detail || error.data?.message || 'Registration failed. Please try again.',
          duration: 5000,
        })
      );
    }
  };

  return (
    <GlassCard className="w-full max-w-md p-8">
      {/* Logo/Brand */}
      <div className="text-center mb-8">
        <h1 className="text-3xl font-display font-bold text-accent-primary mb-2">
          SPATIAL AI
        </h1>
        <p className="text-text-secondary">
          Create your account
        </p>
      </div>

      {/* Register Form */}
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Full Name Input */}
        <div className="space-y-2">
          <label 
            htmlFor="fullName" 
            className="block text-sm font-medium text-text-secondary"
          >
            Full Name
          </label>
          <input
            id="fullName"
            type="text"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
            autoComplete="name"
            className="w-full px-4 py-3 bg-primary-bg border border-border-color 
                     rounded-lg text-text-primary placeholder-text-muted
                     focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20
                     transition-all duration-200"
            placeholder="John Doe"
          />
        </div>

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
          <label 
            htmlFor="password" 
            className="block text-sm font-medium text-text-secondary"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="new-password"
            className="w-full px-4 py-3 bg-primary-bg border border-border-color 
                     rounded-lg text-text-primary placeholder-text-muted
                     focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20
                     transition-all duration-200"
            placeholder="At least 8 characters"
          />
        </div>

        {/* Confirm Password Input */}
        <div className="space-y-2">
          <label 
            htmlFor="confirmPassword" 
            className="block text-sm font-medium text-text-secondary"
          >
            Confirm Password
          </label>
          <input
            id="confirmPassword"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            autoComplete="new-password"
            className="w-full px-4 py-3 bg-primary-bg border border-border-color 
                     rounded-lg text-text-primary placeholder-text-muted
                     focus:border-accent-primary focus:ring-2 focus:ring-accent-primary/20
                     transition-all duration-200"
            placeholder="Confirm your password"
          />
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
          {isLoading ? 'Creating account...' : 'Create Account'}
        </Button>
      </form>

      {/* Login Link */}
      <div className="mt-6 text-center">
        <p className="text-sm text-text-secondary">
          Already have an account?{' '}
          <Link 
            to="/login" 
            className="text-accent-primary hover:text-accent-secondary font-medium transition-colors"
          >
            Sign in
          </Link>
        </p>
      </div>
    </GlassCard>
  );
}
