import api from './api';
import type { JSendResponse, Module } from '../types';

const MODULES_BASE = '/modules';

export interface ModuleWithStatus extends Module {
  is_locked: boolean;
  difficulty_range: [number, number];
  unlock_theta_threshold: number;
}

export const modulesService = {
  /**
   * Get all modules with user progress status
   * GET /api/modules
   */
  listModules: async (): Promise<ModuleWithStatus[]> => {
    const response = await api.get<JSendResponse<ModuleWithStatus[]>>(MODULES_BASE);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get modules');
  },
};

export default modulesService;
