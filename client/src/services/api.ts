import axios, { type AxiosInstance, type AxiosError, type InternalAxiosRequestConfig } from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

// Pydantic error detail item
interface PydanticErrorDetail {
  type: string;
  loc: (string | number)[];
  msg: string;
  input: unknown;
  ctx?: Record<string, unknown>;
  url?: string;
}

/**
 * Extract user-friendly error message from 422 Unprocessable Entity response.
 * Handles both JSend fail format and Pydantic validation error format.
 */
export function extract422ErrorMessage(error: AxiosError): string {
  if (error.response?.status !== 422) {
    return error.message || 'An error occurred';
  }

  const data = error.response.data as Record<string, unknown>;

  // Check for JSend fail format
  if (data && typeof data === 'object') {
    if (data.status === 'fail' && typeof data.message === 'string') {
      return data.message;
    }

    // Check for Pydantic validation error format
    if (Array.isArray(data.detail)) {
      const details = data.detail as PydanticErrorDetail[];
      if (details.length > 0 && typeof details[0].msg === 'string') {
        return details[0].msg;
      }
    }
  }

  return 'Invalid input. Please check your data and try again.';
}

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 seconds timeout
  withCredentials: true, // Required for CORS with credentials
});

// Request interceptor to add JWT token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    // Don't redirect on 401 for login endpoint - let the component handle it
    const isLoginRequest = error.config?.url?.includes('/auth/login');

    if (error.response?.status === 401 && !isLoginRequest) {
      // Check if user was logged in before getting 401
      const wasLoggedIn = localStorage.getItem('auth-storage') !== null;

      // Unauthorized - clear token first
      localStorage.removeItem('auth-storage');

      // Show warning toast if user was previously logged in
      if (wasLoggedIn) {
        // Store message in sessionStorage to survive page reload
        sessionStorage.setItem('auth_expired_message', 'Your session has expired due to inactivity. Please log in again to continue.');
        window.location.href = '/login';
      } else {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
