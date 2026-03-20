/**
 * Login form component using RTK Query
 */

import { useState, type FormEvent } from 'react';
import { useLoginMutation } from '../store/api/authApi';
import { useDispatch } from 'react-redux';
import { loginSuccess } from '../store/slices/authSlice';
import { addNotification } from '../store/slices/uiSlice';

export function LoginForm() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const dispatch = useDispatch();

  // RTK Query mutation hook
  const [login, { isLoading }] = useLoginMutation();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();

    try {
      // Call the login mutation
      const result = await login({ email, password }).unwrap();

      // Dispatch success action to update auth state
      dispatch(loginSuccess(result));

      // Show success notification
      dispatch(
        addNotification({
          type: 'success',
          message: 'Login successful!',
          duration: 3000,
        })
      );
    } catch (error: any) {
      // Show error notification
      dispatch(
        addNotification({
          type: 'error',
          message: error.data?.message || 'Login failed. Please try again.',
          duration: 5000,
        })
      );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900">
      <div className="bg-gray-800 p-8 rounded-lg shadow-lg w-full max-w-md">
        <h2 className="text-2xl font-bold text-white mb-6 text-center">Login</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-300 mb-2">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your email"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-2">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your password"
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-600 text-white font-semibold py-2 px-4 rounded-lg transition-colors"
          >
            {isLoading ? 'Logging in...' : 'Login'}
          </button>
        </form>

        <p className="mt-4 text-center text-sm text-gray-400">
          Don't have an account?{' '}
          <a href="/register" className="text-blue-500 hover:text-blue-400">
            Register
          </a>
        </p>
      </div>
    </div>
  );
}
