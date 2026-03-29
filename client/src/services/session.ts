import api from './api';
import type {
  JSendResponse,
  SessionStartRequest,
  SessionStartResult,
  Question,
  SessionStatus,
  SubmitRequest,
  SubmitResult,
  NextResult,
  ActiveSessionCheck,
} from '../types';

const SESSION_BASE = '/session';

export const sessionService = {
  /**
   * Start a new assessment session
   * POST /api/v1/session/start
   */
  startSession: async (data: SessionStartRequest): Promise<SessionStartResult> => {
    const response = await api.post<JSendResponse<SessionStartResult>>(`${SESSION_BASE}/start`, data);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to start session');
  },

  /**
   * Get current question for a session
   * GET /api/v1/session/{id}/question
   */
  getQuestion: async (sessionId: string): Promise<Question> => {
    const response = await api.get<JSendResponse<Question>>(`${SESSION_BASE}/${sessionId}/question`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get question');
  },

  /**
   * Get session status
   * GET /api/v1/session/{id}
   */
  getSessionStatus: async (sessionId: string): Promise<SessionStatus> => {
    const response = await api.get<JSendResponse<SessionStatus>>(`${SESSION_BASE}/${sessionId}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get session status');
  },

  /**
   * Submit an answer attempt
   * POST /api/v1/session/{id}/submit
   */
  submitAnswer: async (sessionId: string, data: SubmitRequest): Promise<SubmitResult> => {
    const response = await api.post<JSendResponse<SubmitResult>>(`${SESSION_BASE}/${sessionId}/submit`, data);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to submit answer');
  },

  /**
   * Advance to next question (triggers Elo update)
   * POST /api/v1/session/{id}/next
   */
  nextQuestion: async (sessionId: string): Promise<NextResult> => {
    const response = await api.post<JSendResponse<NextResult>>(`${SESSION_BASE}/${sessionId}/next`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to get next question');
  },

  /**
   * End a session
   * POST /api/v1/session/{id}/end
   */
  endSession: async (sessionId: string): Promise<SessionStatus> => {
    const response = await api.post<JSendResponse<SessionStatus>>(`${SESSION_BASE}/${sessionId}/end`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to end session');
  },

  /**
   * Check for active session
   * GET /api/v1/session/active
   */
  getActiveSession: async (): Promise<ActiveSessionCheck | null> => {
    const response = await api.get<JSendResponse<ActiveSessionCheck | null>>(`${SESSION_BASE}/active`);
    if (response.data.status === 'success') {
      return response.data.data; // Can be null if no active session
    }
    throw new Error(response.data.message || 'Failed to check active session');
  },
};

export default sessionService;
