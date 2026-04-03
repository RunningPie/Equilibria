import api from './api';
import type {
  JSendResponse,
  PeerSessionInboxItem,
  PeerSessionDetail,
  ReviewSubmitRequest,
  ReviewSubmitResult,
  PeerSessionRequest,
  RateRequest,
  RateResult,
} from '../types';

const COLLAB_BASE = '/collaboration';

export const collaborationService = {
  /**
   * Get reviewer's inbox - list pending peer review tasks
   * GET /collaboration/inbox
   */
  getInbox: async (): Promise<PeerSessionInboxItem[]> => {
    const response = await api.get<JSendResponse<PeerSessionInboxItem[]>>(`${COLLAB_BASE}/inbox`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to load inbox');
  },

  /**
   * Get review task details
   * GET /collaboration/inbox/{session_id}
   */
  getReviewTask: async (sessionId: string): Promise<PeerSessionDetail> => {
    const response = await api.get<JSendResponse<PeerSessionDetail>>(`${COLLAB_BASE}/inbox/${sessionId}`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to load task details');
  },

  /**
   * Submit review feedback
   * POST /collaboration/inbox/{session_id}/submit
   */
  submitReview: async (sessionId: string, reviewContent: string): Promise<ReviewSubmitResult> => {
    const data: ReviewSubmitRequest = { review_content: reviewContent };
    const response = await api.post<JSendResponse<ReviewSubmitResult>>(
      `${COLLAB_BASE}/inbox/${sessionId}/submit`,
      data
    );
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to submit review');
  },

  /**
   * Get requester's peer review requests
   * GET /collaboration/requests
   */
  getRequests: async (): Promise<PeerSessionRequest[]> => {
    const response = await api.get<JSendResponse<PeerSessionRequest[]>>(`${COLLAB_BASE}/requests`);
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to load requests');
  },

  /**
   * Rate peer feedback (thumbs up/down)
   * POST /collaboration/requests/{session_id}/rate
   */
  rateFeedback: async (sessionId: string, isHelpful: boolean): Promise<RateResult> => {
    const data: RateRequest = { is_helpful: isHelpful };
    const response = await api.post<JSendResponse<RateResult>>(
      `${COLLAB_BASE}/requests/${sessionId}/rate`,
      data
    );
    if (response.data.status === 'success' && response.data.data) {
      return response.data.data;
    }
    throw new Error(response.data.message || 'Failed to rate feedback');
  },
};

export default collaborationService;
