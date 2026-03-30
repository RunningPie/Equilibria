import { useEffect, useState, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import CodeMirror from '@uiw/react-codemirror';
import { sql } from '@codemirror/lang-sql';
import { oneDark } from '@codemirror/theme-one-dark';
import { Header } from '../components/Header';
import { sessionService } from '../services/session';
import { useAuthStore } from '../store/authStore';
import { toast } from '../hooks/toastState';
import { Modal } from '../components/Modal';
import type { Question, SubmitResult, NextResult } from '../types';

/**
 * SessionPage
 * Individual assessment session with CodeMirror SQL editor
 */
export function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const navigate = useNavigate();
  const user = useAuthStore((state) => state.user);
  const updateUser = useAuthStore((state) => state.updateUser);

  const [question, setQuestion] = useState<Question | null>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingNext, setIsLoadingNext] = useState(false);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  const [nextResult, setNextResult] = useState<NextResult | null>(null);
  const [attemptCount, setAttemptCount] = useState(0);
  const [error, setError] = useState('');
  const [sessionEnded, setSessionEnded] = useState(false);
  const [sessionComplete, setSessionComplete] = useState(false);

  // Progress tracking
  const [questionsServed, setQuestionsServed] = useState(0);
  const [totalQuestionsAvailable, setTotalQuestionsAvailable] = useState(0);

  // Skip modal state
  const [isSkipModalOpen, setIsSkipModalOpen] = useState(false);

  // Load current question on mount
  useEffect(() => {
    const loadQuestion = async () => {
      if (!sessionId) return;

      try {
        const currentQuestion = await sessionService.getQuestion(sessionId);
        setQuestion(currentQuestion);
        setAttemptCount(currentQuestion.attempt_count);
      } catch {
        setError('Failed to load question. Session may have ended.');
        setSessionEnded(true);
      } finally {
        setIsLoading(false);
      }
    };

    loadQuestion();
  }, [sessionId]);

  // Handle submit answer
  const handleSubmit = useCallback(async () => {
    if (!sessionId || !question || !sqlQuery.trim()) return;

    setIsSubmitting(true);
    setError('');

    const startTime = performance.now();

    try {
      const result = await sessionService.submitAnswer(sessionId, {
        question_id: question.question_id,
        user_query: sqlQuery.trim(),
        execution_time_ms: Math.round(performance.now() - startTime),
      });

      setSubmitResult(result);
      setAttemptCount(result.attempt_number);

      // Update user theta if provided
      if (result.theta_after) {
        updateUser({ theta_individu: result.theta_after });
      }

      // If no next question available, session is complete
      if (!result.next_question_available) {
        setSessionComplete(true);
      }
    } catch {
      setError('Failed to submit answer. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  }, [sessionId, question, sqlQuery, updateUser]);

  // Handle next question
  const handleNext = useCallback(async () => {
    if (!sessionId) return;

    setIsLoadingNext(true);
    setError('');

    try {
      const result = await sessionService.nextQuestion(sessionId);
      setNextResult(result);

      // Update progress tracking
      if (result.questions_served) {
        setQuestionsServed(result.questions_served);
      }
      if (result.total_questions_available) {
        setTotalQuestionsAvailable(result.total_questions_available);
      }

      // Check for stagnation - show toast warning with link to inbox
      if (result.stagnation_detected) {
        toast.warning(
          'Stagnation detected! A peer review session has been created for you.',
          10000,
          { label: 'Go to Inbox', onClick: () => navigate('/inbox') }
        );
      }

      // Check if peer session was created
      if (result.peer_session_created) {
        toast.info('You have been enrolled in a peer learning session.', 5000);
      }

      // Update user theta
      if (result.theta_after) {
        updateUser({ theta_individu: result.theta_after });
      }

      // Check if session should end (max questions reached or next chapter unlocked)
      if (result.max_questions_reached || result.next_chapter_unlocked) {
        setSessionEnded(true);
        return;
      }

      // Load next question
      const nextQuestion = await sessionService.getQuestion(sessionId);
      setQuestion(nextQuestion);
      setSqlQuery('');
      setSubmitResult(null);
      setAttemptCount(0);
    } catch {
      setError('Failed to load next question.');
      setSessionEnded(true);
    } finally {
      setIsLoadingNext(false);
    }
  }, [sessionId, updateUser, navigate]);

  // Handle skip question (move to next without retry)
  const handleSkip = useCallback(async () => {
    setIsSkipModalOpen(false);
    await handleNext();
  }, [handleNext]);

  // Handle return to dashboard (call /next first if session is complete)
  const handleReturnToDashboard = useCallback(async () => {
    if (sessionComplete && sessionId) {
      // Call /next to finalize the session in the backend
      try {
        await sessionService.nextQuestion(sessionId);
      } catch {
        // Ignore errors, just navigate to dashboard
      }
    }
    navigate('/dashboard', { replace: true });
  }, [sessionComplete, sessionId, navigate]);

  // Handle end session
  const handleEndSession = useCallback(async () => {
    if (!sessionId) return;

    try {
      await sessionService.endSession(sessionId);
      navigate('/dashboard', { replace: true });
    } catch {
      setError('Failed to end session');
    }
  }, [sessionId, navigate]);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading session...</p>
        </div>
      </div>
    );
  }

  // Session complete view (no more questions available from submit)
  if (sessionComplete) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <main className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="mb-6">
              <svg className="w-16 h-16 text-green-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Session Complete!</h1>
            <p className="text-gray-600 mb-6">
              You have answered all available questions in this module.
            </p>
            {submitResult?.theta_after && (
              <div className="bg-gray-50 rounded-lg p-6 mb-6">
                <p className="text-sm text-gray-600 mb-2">Final Theta Score</p>
                <p className="text-4xl font-bold text-blue-600">{submitResult.theta_after.toFixed(0)}</p>
              </div>
            )}
            <button
              onClick={handleReturnToDashboard}
              className="bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </main>
      </div>
    );
  }

  // Session ended view (from next endpoint - max questions or chapter unlocked)
  if (sessionEnded || !question) {
    return (
      <div className="min-h-screen bg-gray-100">
        <Header />
        <main className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="mb-6">
              <svg className="w-16 h-16 text-blue-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Session Completed</h1>

            {nextResult?.max_questions_reached && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
                <p className="text-green-800">
                  Maximum number of questions reached for this session.
                </p>
              </div>
            )}

            {nextResult?.next_chapter_unlocked && (
              <div className="bg-purple-50 border border-purple-200 rounded-lg p-4 mb-6">
                <p className="text-purple-800">
                  Congratulations! You have unlocked the next chapter.
                </p>
              </div>
            )}

            {nextResult?.stagnation_detected && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mb-6">
                <p className="text-amber-800">
                  Stagnation detected. You may benefit from peer collaboration.
                </p>
              </div>
            )}

            {nextResult?.peer_session_created && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p className="text-blue-800">
                  A peer review session has been created for you.
                </p>
              </div>
            )}

            {nextResult?.theta_after && (
              <div className="bg-gray-50 rounded-lg p-6 mb-6">
                <p className="text-sm text-gray-600 mb-2">Final Theta Score</p>
                <p className="text-4xl font-bold text-blue-600">{nextResult.theta_after.toFixed(0)}</p>
                {nextResult.theta_change !== null && (
                  <p className={`text-sm mt-2 ${nextResult.theta_change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {nextResult.theta_change >= 0 ? '+' : ''}{nextResult.theta_change.toFixed(1)} from start
                  </p>
                )}
              </div>
            )}

            <button
              onClick={handleReturnToDashboard}
              className="bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 transition-colors"
            >
              Return to Dashboard
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-6">
        {/* Session Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Assessment Session</h1>
            <p className="text-sm text-gray-600">
              Module {question.module_id} • Question {submitResult?.attempt_number ? `(Attempt ${attemptCount}/${question.max_attempts})` : ''}
            </p>
          </div>
          <button
            onClick={handleEndSession}
            className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            End Session
          </button>
        </div>

        {/* Theta Progress */}
        {user && (
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <div className="flex items-center justify-between">
              <span className="text-sm text-gray-600">Your Rating</span>
              <span className="text-lg font-semibold text-blue-600">
                {user.theta_individu.toFixed(0)}
              </span>
            </div>
            <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (user.theta_individu / 2000) * 100)}%` }}
              />
            </div>
          </div>
        )}

        {/* Progress Indicator */}
        {totalQuestionsAvailable > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-4 mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-600">Progress</span>
              <span className="text-sm font-medium text-gray-900">
                {questionsServed} / {totalQuestionsAvailable} questions
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${Math.min(100, (questionsServed / totalQuestionsAvailable) * 100)}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded-lg">
            {error}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Question Panel */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center gap-2 mb-4">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-sm font-medium rounded-full">
                Difficulty {question.current_difficulty.toFixed(1)}
              </span>
              <span className="text-sm text-gray-500">
                Attempt {attemptCount} of {question.max_attempts}
              </span>
            </div>

            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              {question.content}
            </h2>

            {/* Schema info */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Instructions</h3>
              <ul className="text-sm text-gray-600 list-disc list-inside space-y-1">
                <li>Write a SQL query that answers the question</li>
                <li>You have {question.max_attempts} attempts per question</li>
                <li>Your rating adjusts based on correctness</li>
              </ul>
            </div>
          </div>

          {/* SQL Editor Panel */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">SQL Editor</h3>
              <span className="text-xs text-gray-500">PostgreSQL syntax</span>
            </div>

            <div className="border border-gray-300 rounded-lg overflow-hidden">
              <CodeMirror
                value={sqlQuery}
                height="300px"
                extensions={[sql()]}
                theme={oneDark}
                onChange={(value) => setSqlQuery(value)}
                placeholder="-- Write your SQL query here\nSELECT * FROM ..."
                basicSetup={{
                  lineNumbers: true,
                  highlightActiveLineGutter: true,
                  highlightActiveLine: true,
                  foldGutter: false,
                }}
              />
            </div>

            {/* Submit Result Feedback */}
            {submitResult && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  submitResult.is_correct
                    ? 'bg-green-100 text-green-800'
                    : submitResult.is_final_attempt
                    ? 'bg-red-100 text-red-800'
                    : 'bg-amber-100 text-amber-800'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {submitResult.is_correct ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  <span className="font-medium">
                    {submitResult.is_correct ? 'Correct!' : 'Incorrect'}
                  </span>
                </div>
                <p className="text-sm">{submitResult.feedback}</p>

                {/* Theta update info */}
                {submitResult.theta_before !== null && submitResult.theta_after !== null && (
                  <p className="text-sm mt-2">
                    Rating: {submitResult.theta_before.toFixed(0)} →{' '}
                    <span className={submitResult.theta_after > submitResult.theta_before ? 'text-green-600' : 'text-red-600'}>
                      {submitResult.theta_after.toFixed(0)}
                    </span>
                    ({submitResult.theta_after > submitResult.theta_before ? '+' : ''}
                    {(submitResult.theta_after - submitResult.theta_before).toFixed(1)})
                  </p>
                )}
              </div>
            )}

            {/* Action Buttons */}
            <div className="mt-6 flex gap-3">
              {!submitResult ? (
                // Submit button (initial state)
                <button
                  onClick={handleSubmit}
                  disabled={isSubmitting || !sqlQuery.trim()}
                  className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Submitting...
                    </span>
                  ) : (
                    'Submit Answer'
                  )}
                </button>
              ) : !submitResult.is_correct && !submitResult.is_final_attempt ? (
                // Retry and Skip buttons (incorrect but can retry)
                <>
                  <button
                    onClick={handleSubmit}
                    disabled={isSubmitting || !sqlQuery.trim()}
                    className="flex-1 bg-amber-600 text-white py-3 px-4 rounded-lg hover:bg-amber-700 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                  >
                    {isSubmitting ? (
                      <span className="flex items-center justify-center gap-2">
                        <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Submitting...
                      </span>
                    ) : (
                      `Retry (Attempt ${attemptCount + 1}/${question.max_attempts})`
                    )}
                  </button>
                  <button
                    onClick={() => setIsSkipModalOpen(true)}
                    className="flex-1 bg-gray-200 text-gray-700 py-3 px-4 rounded-lg hover:bg-gray-300 focus:ring-2 focus:ring-gray-500 focus:ring-offset-2 transition-colors font-medium"
                  >
                    Skip Question
                  </button>
                </>
              ) : submitResult.next_question_available ? (
                // Next button (when next question is available)
                <button
                  onClick={handleNext}
                  disabled={isLoadingNext}
                  className="flex-1 bg-green-600 text-white py-3 px-4 rounded-lg hover:bg-green-700 focus:ring-2 focus:ring-green-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
                >
                  {isLoadingNext ? (
                    <span className="flex items-center justify-center gap-2">
                      <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                      </svg>
                      Loading...
                    </span>
                  ) : (
                    'Next Question →'
                  )}
                </button>
              ) : (
                // Session complete button (no more questions)
                <button
                  onClick={handleReturnToDashboard}
                  className="flex-1 bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
                >
                  Return to Dashboard
                </button>
              )}
            </div>
            {/* Skip Confirmation Modal */}
            <Modal
              isOpen={isSkipModalOpen}
              onClose={() => setIsSkipModalOpen(false)}
              title="Skip Question?"
              footer={
                <>
                  <button
                    onClick={() => setIsSkipModalOpen(false)}
                    className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleSkip}
                    className="px-4 py-2 bg-amber-600 text-white hover:bg-amber-700 rounded-lg transition-colors"
                  >
                    Yes, Skip
                  </button>
                </>
              }
            >
              <div className="space-y-4">
                <div className="flex items-center gap-3 text-amber-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                  <span className="font-medium">Warning</span>
                </div>
                <p className="text-gray-600">
                  You have not answered this question correctly. If you skip, you will <strong>not be able to return</strong> to this question later.
                </p>
                <p className="text-gray-600">
                  Are you sure you want to skip?
                </p>
              </div>
            </Modal>
          </div>
        </div>
      </main>
    </div>
  );
}

export default SessionPage;
