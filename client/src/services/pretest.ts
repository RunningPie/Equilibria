import api from './api';
import type {
  JSendResponse,
  PreTestSessionResponse,
  PreTestQuestion,
  PreTestResult,
  PreTestAnswerSubmit,
} from '../types';

const PRETEST_BASE = '/pretest';

export const pretestService = {
  /**
   * Start a new pretest session
   * POST /api/pretest/start
   */
  startPretest: async (): Promise<PreTestSessionResponse> => {
    const response = await api.post<JSendResponse<PreTestSessionResponse>>(`${PRETEST_BASE}/start`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to start pretest');
  },

  /**
   * Get current pretest question
   * GET /api/pretest/question/current
   */
  getCurrentQuestion: async (): Promise<PreTestQuestion> => {
    const response = await api.get<JSendResponse<PreTestQuestion>>(`${PRETEST_BASE}/question/current`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get question');
  },

  /**
   * Submit a pretest answer
   * POST /api/pretest/submit
   */
  submitAnswer: async (data: PreTestAnswerSubmit): Promise<PreTestResult> => {
    const response = await api.post<JSendResponse<PreTestResult>>(`${PRETEST_BASE}/submit`, data);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to submit answer');
  },
};

export default pretestService;
