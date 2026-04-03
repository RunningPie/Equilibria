import api from './api';
import type { JSendResponse, LeaderboardResponse } from '../types';

const LEADERBOARD_BASE = '/leaderboard';

export const leaderboardService = {
  /**
   * Get leaderboard rankings
   * GET /api/v1/leaderboard
   */
  getLeaderboard: async (limit: number = 20, offset: number = 0): Promise<LeaderboardResponse> => {
    const response = await api.get<JSendResponse<LeaderboardResponse>>(
      `${LEADERBOARD_BASE}?limit=${limit}&offset=${offset}`
    );
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to fetch leaderboard');
  },
};

export default leaderboardService;
