import api from './api';
import type {
  JSendResponse,
  UserLoginRequest,
  UserRegisterRequest,
  UserUpdateRequest,
  LoginResponse,
  LogoutResponse,
  User,
} from '../types';

const AUTH_BASE = '/auth';

export const authService = {
  /**
   * Login user with NIM and password
   * POST /api/v1/auth/login
   */
  login: async (data: UserLoginRequest): Promise<LoginResponse> => {
    const response = await api.post<JSendResponse<LoginResponse>>(`${AUTH_BASE}/login`, data);
    if (response.data.status === 'success' && response.data.data) {
      // Store token in localStorage
      localStorage.setItem('access_token', response.data.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
      return response.data.data;
    }
    throw new Error(response.data.message || 'Login failed');
  },

  /**
   * Register new user
   * POST /api/v1/auth/register
   */
  register: async (data: UserRegisterRequest): Promise<LoginResponse> => {
    const response = await api.post<JSendResponse<LoginResponse>>(`${AUTH_BASE}/register`, data);
    if (response.data.status === 'success' && response.data.data) {
      // Store token in localStorage
      localStorage.setItem('access_token', response.data.data.access_token);
      localStorage.setItem('user', JSON.stringify(response.data.data.user));
      return response.data.data;
    }
    throw new Error(response.data.message || 'Registration failed');
  },

  /**
   * Logout current user
   * POST /api/v1/auth/logout
   */
  logout: async (): Promise<void> => {
    try {
      await api.post<JSendResponse<LogoutResponse>>(`${AUTH_BASE}/logout`);
    } finally {
      // Always clear local storage
      localStorage.removeItem('access_token');
      localStorage.removeItem('user');
    }
  },

  /**
   * Get current user profile
   * GET /api/v1/auth/me
   */
  getMe: async (): Promise<User> => {
    const response = await api.get<JSendResponse<User>>(`${AUTH_BASE}/me`);
    if (response.data.status === 'success' && response.data.data) {
      // Update stored user data
      localStorage.setItem('user', JSON.stringify(response.data.data));
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get user profile');
  },

  /**
   * Update current user profile
   * PUT /api/v1/auth/me
   */
  updateMe: async (data: UserUpdateRequest): Promise<User> => {
    const response = await api.put<JSendResponse<User>>(`${AUTH_BASE}/me`, data);
    if (response.data.status === 'success' && response.data.data) {
      // Update stored user data
      localStorage.setItem('user', JSON.stringify(response.data.data));
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to update profile');
  },

  /**
   * Check if user is authenticated (token exists)
   */
  isAuthenticated: (): boolean => {
    return !!localStorage.getItem('access_token');
  },

  /**
   * Get stored token
   */
  getToken: (): string | null => {
    return localStorage.getItem('access_token');
  },

  /**
   * Get stored user
   */
  getStoredUser: (): User | null => {
    const userStr = localStorage.getItem('user');
    if (userStr) {
      try {
        return JSON.parse(userStr) as User;
      } catch {
        return null;
      }
    }
    return null;
  },
};

export default authService;
