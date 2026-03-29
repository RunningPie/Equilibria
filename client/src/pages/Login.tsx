import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth';
import { useAuthStore } from '../store/authStore';

/**
 * Login Page
 * Full implementation with NIM/password validation, API integration, and error handling
 */
export function Login() {
  const navigate = useNavigate();
  const login = useAuthStore((state) => state.login);

  // Form state
  const [nim, setNim] = useState('');
  const [password, setPassword] = useState('');

  // Validation errors
  const [nimError, setNimError] = useState('');
  const [passwordError, setPasswordError] = useState('');

  // API error
  const [apiError, setApiError] = useState('');

  // Loading state
  const [isLoading, setIsLoading] = useState(false);

  // Validation functions
  const validateNim = (value: string): boolean => {
    if (!value) {
      setNimError('NIM is required');
      return false;
    }
    if (!/^\d+$/.test(value)) {
      setNimError('NIM must contain only numbers');
      return false;
    }
    if (value.length < 8 || value.length > 10) {
      setNimError('NIM must be 8-10 digits');
      return false;
    }
    setNimError('');
    return true;
  };

  const validatePassword = (value: string): boolean => {
    if (!value) {
      setPasswordError('Password is required');
      return false;
    }
    if (value.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return false;
    }
    setPasswordError('');
    return true;
  };

  // Handle form submission
  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setApiError('');

    // Validate inputs
    const isNimValid = validateNim(nim);
    const isPasswordValid = validatePassword(password);

    if (!isNimValid || !isPasswordValid) {
      return;
    }

    // Submit login
    setIsLoading(true);
    try {
      const response = await authService.login({
        nim,
        password,
      });

      // Store in auth store
      login(response.access_token, response.user);

      // Redirect to dashboard
      navigate('/dashboard', { replace: true });
    } catch (error) {
      if (error instanceof Error) {
        setApiError(error.message || 'Invalid NIM or password');
      } else {
        setApiError('An error occurred. Please try again.');
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-lg shadow-md p-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Equilibria</h1>
          <p className="text-gray-600 mt-2">Sign in to your account</p>
        </div>

        {/* API Error */}
        {apiError && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {apiError}
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-6">
          {/* NIM Field */}
          <div>
            <label htmlFor="nim" className="block text-sm font-medium text-gray-700 mb-1">
              NIM
            </label>
            <input
              type="text"
              id="nim"
              value={nim}
              onChange={(e) => {
                setNim(e.target.value);
                if (nimError) validateNim(e.target.value);
              }}
              onBlur={(e) => validateNim(e.target.value)}
              placeholder="Enter your NIM (8-10 digits)"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                nimError ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isLoading}
            />
            {nimError && (
              <p className="mt-1 text-sm text-red-600">{nimError}</p>
            )}
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
              Password
            </label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                if (passwordError) validatePassword(e.target.value);
              }}
              onBlur={(e) => validatePassword(e.target.value)}
              placeholder="Enter your password (min 8 characters)"
              className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                passwordError ? 'border-red-500' : 'border-gray-300'
              }`}
              disabled={isLoading}
            />
            {passwordError && (
              <p className="mt-1 text-sm text-red-600">{passwordError}</p>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isLoading ? (
              <span className="flex items-center justify-center">
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Signing in...
              </span>
            ) : (
              'Sign In'
            )}
          </button>
        </form>

        {/* Footer */}
        <div className="mt-6 text-center text-sm text-gray-600">
          <p>
            Don't have an account?{' '}
            <span className="text-gray-400">Contact your administrator</span>
          </p>
        </div>
      </div>
    </div>
  );
}

export default Login;
