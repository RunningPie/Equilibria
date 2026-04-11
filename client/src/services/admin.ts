import api from './api';
import type { JSendResponse, User, UserListResponse, AdminUserCreateRequest, AdminUserUpdateRequest, LogsResponse } from '../types';

export const adminService = {
  // User management
  async getUsers(page: number = 1, pageSize: number = 20, sortby?: 'nim' | 'name'): Promise<UserListResponse> {
    const params = new URLSearchParams();
    params.append('page', page.toString());
    params.append('page_size', pageSize.toString());
    if (sortby) params.append('sortby', sortby);
    const response = await api.get<JSendResponse<UserListResponse>>(`/admin/users?${params.toString()}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch users');
  },

  async getUser(userId: string): Promise<User> {
    const response = await api.get<JSendResponse<User>>(`/admin/users/${userId}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch user');
  },

  async createUser(userData: AdminUserCreateRequest): Promise<User> {
    const response = await api.post<JSendResponse<User>>('/admin/users', userData);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to create user');
  },

  async updateUser(userId: string, userData: AdminUserUpdateRequest): Promise<User> {
    const response = await api.put<JSendResponse<User>>(`/admin/users/${userId}`, userData);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to update user');
  },

  async deleteUser(userId: string): Promise<{ message: string; deleted_user_id: string; is_deleted: boolean; deleted_at: string }> {
    const response = await api.delete<JSendResponse<{ message: string; deleted_user_id: string; is_deleted: boolean; deleted_at: string }>>(`/admin/users/${userId}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to delete user');
  },

  // Logs
  async getSyslogs(date?: string, limit?: number): Promise<LogsResponse> {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (limit) params.append('limit', limit.toString());
    const response = await api.get<JSendResponse<LogsResponse>>(`/admin/logs/syslogs?${params.toString()}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch syslogs');
  },

  async getAsslogs(date?: string, limit?: number): Promise<LogsResponse> {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (limit) params.append('limit', limit.toString());
    const response = await api.get<JSendResponse<LogsResponse>>(`/admin/logs/asslogs?${params.toString()}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch asslogs');
  },
};
