import api from './api';
import type { JSendResponse, ProfileStats } from '../types';

const PROFILE_BASE = '/profile';

export const profileService = {
  /**
   * Get user profile statistics
   * GET /api/profile/stats
   */
  getStats: async (): Promise<ProfileStats> => {
    const response = await api.get<JSendResponse<ProfileStats>>(`${PROFILE_BASE}/stats`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get profile stats');
  },
};

export default profileService;
