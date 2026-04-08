import { useEffect, useState } from 'react';
import { Header } from '../components/Header';
import { Modal } from '../components/Modal';
import { collaborationService } from '../services/collaboration';
import type { PeerSessionInboxItem, PeerSessionRequest, PeerSessionDetail } from '../types';

type Tab = 'reviews' | 'requests';

interface ReviewModalProps {
  sessionId: string | null;
  onClose: () => void;
  onSubmit: (content: string) => Promise<void>;
  isSubmitting: boolean;
}

function ReviewModal({ sessionId, onClose, onSubmit, isSubmitting }: ReviewModalProps) {
  const [content, setContent] = useState('');
  const [detail, setDetail] = useState<PeerSessionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(() => !!sessionId);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    collaborationService.getReviewTask(sessionId)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load details');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, [sessionId]);

  if (!sessionId) return null;

  const handleSubmit = () => {
    if (content.trim()) {
      onSubmit(content.trim());
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-gray-900">Write Review</h2>
            <button onClick={onClose} className="text-gray-500 hover:text-gray-700 cursor-pointer">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="p-6 space-y-4">
          {isLoading ? (
            <div className="text-center py-8">
              <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : error ? (
            <div className="text-red-600">{error}</div>
          ) : detail ? (
            <>
              <div className="bg-gray-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Question</h3>
                <p className="text-gray-700">{detail.question.content}</p>
                <div className="flex gap-2 mt-2">
                  {detail.question.topic_tags.map((tag) => (
                    <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>

              <div className="bg-yellow-50 rounded-lg p-4">
                <h3 className="font-semibold text-gray-900 mb-2">Requester&apos;s Query</h3>
                <code className="text-sm text-gray-700 block bg-yellow-100 p-3 rounded">
                  {detail.requester_query || 'No query provided'}
                </code>
              </div>

              <div>
                <label className="block font-semibold text-gray-900 mb-2">
                  Your Review / Feedback
                </label>
                <textarea
                  value={content}
                  onChange={(e) => setContent(e.target.value)}
                  className="w-full border border-gray-300 rounded-lg p-3 min-h-[150px] focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  placeholder="Provide constructive feedback about the query..."
                />
              </div>
            </>
          ) : null}
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !content.trim()}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors cursor-pointer"
          >
            {isSubmitting ? 'Submitting...' : 'Submit Review'}
          </button>
        </div>
      </div>
    </div>
  );
}

interface RatingModalProps {
  request: PeerSessionRequest | null;
  onClose: () => void;
  onRate: (isHelpful: boolean) => Promise<void>;
  isSubmitting: boolean;
}

interface ViewDetailModalProps {
  sessionId: string | null;
  onClose: () => void;
}

function ViewDetailModal({ sessionId, onClose }: ViewDetailModalProps) {
  const [detail, setDetail] = useState<PeerSessionDetail | null>(null);
  const [isLoading, setIsLoading] = useState(() => !!sessionId);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    collaborationService.getReviewTask(sessionId)
      .then((data) => {
        if (!cancelled) setDetail(data);
      })
      .catch(() => {
        if (!cancelled) setError('Failed to load details');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => { cancelled = true; };
  }, [sessionId]);

  return (
    <Modal
      isOpen={!!sessionId}
      onClose={onClose}
      title="Request Details"
      footer={
        <button
          onClick={onClose}
          className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
        >
          Close
        </button>
      }
    >
      <div className="space-y-4">
        {isLoading ? (
          <div className="text-center py-8">
            <svg className="animate-spin h-8 w-8 text-blue-600 mx-auto" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        ) : error ? (
          <div className="text-red-600">{error}</div>
        ) : detail ? (
          <>
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Question</h3>
              <p className="text-gray-700">{detail.question.content}</p>
              <div className="flex gap-2 mt-2">
                {detail.question.topic_tags.map((tag) => (
                  <span key={tag} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                    {tag}
                  </span>
                ))}
              </div>
            </div>

            <div className="bg-yellow-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Requester&apos;s Query</h3>
              <code className="text-sm text-gray-700 block bg-yellow-100 p-3 rounded">
                {detail.requester_query || 'No query provided'}
              </code>
            </div>
          </>
        ) : null}
      </div>
    </Modal>
  );
}

function RatingModal({ request, onClose, onRate, isSubmitting }: RatingModalProps) {
  if (!request) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg max-w-lg w-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-xl font-bold text-gray-900">Rate Feedback</h2>
        </div>

        <div className="p-6 space-y-4">
          <div className="bg-gray-50 rounded-lg p-4">
            <h3 className="font-semibold text-gray-900 mb-2">Question Preview</h3>
            <p className="text-gray-700">{request.question_preview}</p>
          </div>

          {request.review_content && (
            <div className="bg-green-50 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-2">Review You Received</h3>
              <p className="text-gray-700 text-sm">{request.review_content}</p>
            </div>
          )}

          <p className="text-gray-600">Was this feedback helpful to you?</p>
        </div>

        <div className="p-6 border-t border-gray-200 flex justify-end gap-3">
          <button
            onClick={onClose}
            className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            onClick={() => onRate(false)}
            disabled={isSubmitting}
            className="px-4 py-2 bg-red-100 text-red-700 rounded-lg hover:bg-red-200 disabled:opacity-50 transition-colors flex items-center gap-2 cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14H5.236a2 2 0 01-1.789-2.894l3.5-7A2 2 0 018.736 3h4.018a2 2 0 01.485.06l3.76.94m-7 10v5a2 2 0 002 2h2m-2-5h.01M12 14h.01M16 14h.01" />
            </svg>
            Not Helpful
          </button>
          <button
            onClick={() => onRate(true)}
            disabled={isSubmitting}
            className="px-4 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 disabled:opacity-50 transition-colors flex items-center gap-2 cursor-pointer"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.018a2 2 0 01-.485-.06l-3.76-.94m7-10v-5a2 2 0 00-2-2h-2m2 5h.01M12 14h.01M16 14h.01" />
            </svg>
            Helpful
          </button>
        </div>
      </div>
    </div>
  );
}

export function PeerHubPage() {
  const [activeTab, setActiveTab] = useState<Tab>('reviews');
  const [inboxItems, setInboxItems] = useState<PeerSessionInboxItem[]>([]);
  const [requests, setRequests] = useState<PeerSessionRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');

  const [reviewModalSession, setReviewModalSession] = useState<string | null>(null);
  const [ratingModalRequest, setRatingModalRequest] = useState<PeerSessionRequest | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [viewDetailSessionId, setViewDetailSessionId] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setIsLoading(true);
      setError('');
      const [inboxData, requestsData] = await Promise.all([
        collaborationService.getInbox(),
        collaborationService.getRequests(),
      ]);
      setInboxItems(inboxData);
      setRequests(requestsData);
    } catch {
      setError('Failed to load collaboration data');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSubmitReview = async (content: string) => {
    if (!reviewModalSession) return;
    setIsSubmitting(true);
    try {
      await collaborationService.submitReview(reviewModalSession, content);
      setReviewModalSession(null);
      fetchData();
    } catch {
      setError('Failed to submit review');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleRate = async (isHelpful: boolean) => {
    if (!ratingModalRequest) return;
    setIsSubmitting(true);
    try {
      await collaborationService.rateFeedback(ratingModalRequest.session_id, isHelpful);
      setRatingModalRequest(null);
      fetchData();
    } catch {
      setError('Failed to rate feedback');
    } finally {
      setIsSubmitting(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'PENDING_REVIEW':
        return 'bg-yellow-100 text-yellow-800';
      case 'WAITING_CONFIRMATION':
        return 'bg-blue-100 text-blue-800';
      case 'COMPLETED':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />
      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-md p-6">
          {/* Header */}
          <div className="flex items-center gap-3 mb-6">
            <svg className="w-8 h-8 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            <h1 className="text-2xl font-bold text-gray-900">Peer Hub</h1>
          </div>

          {/* Tabs */}
          <div className="flex border-b border-gray-200 mb-6">
            <button
              onClick={() => setActiveTab('reviews')}
              className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors cursor-pointer ${
                activeTab === 'reviews'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              Reviews to Give ({inboxItems.length})
            </button>
            <button
              onClick={() => setActiveTab('requests')}
              className={`px-4 py-3 font-medium text-sm border-b-2 transition-colors cursor-pointer ${
                activeTab === 'requests'
                  ? 'border-purple-600 text-purple-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700'
              }`}
            >
              My Requests ({requests.length})
            </button>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
              <p className="text-red-800">{error}</p>
            </div>
          )}

          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <svg className="animate-spin h-8 w-8 text-blue-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
            </div>
          ) : activeTab === 'reviews' ? (
            inboxItems.length === 0 ? (
              <div className="text-center py-12">
                <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <p className="text-gray-600">No reviews pending</p>
                <p className="text-sm text-gray-500 mt-2">
                  When peers need feedback on their work, you&apos;ll see requests here.
                </p>
              </div>
            ) : (
              <div className="space-y-4">
                {inboxItems.map((item) => (
                  <div
                    key={item.session_id}
                    onClick={() => setViewDetailSessionId(item.session_id)}
                    className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 hover:shadow-md transition-all cursor-pointer"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(item.status)}`}>
                          {item.status.replace('_', ' ')}
                        </span>
                        <h3 className="font-semibold text-gray-900 mt-2">{item.question_preview}</h3>
                        <p className="text-xs text-gray-500 mt-2">
                          Created: {new Date(item.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      {item.status === 'PENDING_REVIEW' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setReviewModalSession(item.session_id);
                          }}
                          className="bg-purple-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-purple-700 transition-colors ml-4 cursor-pointer"
                        >
                          Write Review
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )
          ) : requests.length === 0 ? (
            <div className="text-center py-12">
              <svg className="w-16 h-16 text-gray-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
              <p className="text-gray-600">No requests yet</p>
              <p className="text-sm text-gray-500 mt-2">
                Requests you make for peer feedback will appear here.
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {requests.map((request) => (
                <div
                  key={request.session_id}
                  onClick={() => setViewDetailSessionId(request.session_id)}
                  className="border border-gray-200 rounded-lg p-4 hover:bg-gray-50 hover:shadow-md transition-all cursor-pointer"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <span className={`px-2 py-1 rounded text-xs font-medium ${getStatusColor(request.status)}`}>
                        {request.status.replace('_', ' ')}
                      </span>
                      <h3 className="font-semibold text-gray-900 mt-2">{request.question_preview}</h3>
                      <p className="text-xs text-gray-500 mt-2">
                        Created: {new Date(request.created_at).toLocaleDateString()}
                      </p>
                      {request.review_content && (
                        <div className="mt-3 p-3 bg-gray-50 rounded text-sm text-gray-700">
                          <span className="font-medium">Feedback received:</span> {request.review_content}
                        </div>
                      )}
                    </div>
                    {request.status === 'WAITING_CONFIRMATION' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setRatingModalRequest(request);
                        }}
                        className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 transition-colors ml-4 cursor-pointer"
                      >
                        Rate
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>

      <ReviewModal
        sessionId={reviewModalSession}
        onClose={() => setReviewModalSession(null)}
        onSubmit={handleSubmitReview}
        isSubmitting={isSubmitting}
      />

      <RatingModal
        request={ratingModalRequest}
        onClose={() => setRatingModalRequest(null)}
        onRate={handleRate}
        isSubmitting={isSubmitting}
      />

      <ViewDetailModal
        sessionId={viewDetailSessionId}
        onClose={() => setViewDetailSessionId(null)}
      />
    </div>
  );
}

export default PeerHubPage;
