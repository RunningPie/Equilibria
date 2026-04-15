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
 * Extract user-friendly error message from API error response.
 * Handles JSend format (fail/error), Pydantic validation errors, and generic errors.
 * For 4XX/5XX responses, prioritizes the 'message' field from the response body.
 */
export function extractErrorMessage(error: AxiosError): string {
  if (!error.response) {
    return error.message || 'Network error. Please check your connection.';
  }

  const status = error.response.status;
  const data = error.response.data as Record<string, unknown>;

  // For 4XX and 5XX responses, extract message from response body
  if (status >= 400 && status < 600 && data && typeof data === 'object') {
    // JSend format: status + message
    if (typeof data.message === 'string') {
      return data.message;
    }

    // Pydantic validation error format (commonly 422)
    if (Array.isArray(data.detail)) {
      const details = data.detail as PydanticErrorDetail[];
      if (details.length > 0 && typeof details[0].msg === 'string') {
        return details[0].msg;
      }
    }
  }

  // Fallback to error message or generic message
  return error.message || `Request failed with status ${status}`;
}

/**
 * @deprecated Use extractErrorMessage instead. This function only handles 422 errors.
 */
export function extract422ErrorMessage(error: AxiosError): string {
  return extractErrorMessage(error);
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
