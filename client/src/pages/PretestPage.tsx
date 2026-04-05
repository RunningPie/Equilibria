import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import type { AxiosError } from 'axios';
import CodeMirror from '@uiw/react-codemirror';
import { sql } from '@codemirror/lang-sql';
import { oneDark } from '@codemirror/theme-one-dark';
import { Header } from '../components/Header';
import { pretestService } from '../services/pretest';
import { extract422ErrorMessage } from '../services/api';
import { useAuthStore } from '../store/authStore';
import type { PreTestQuestion, PreTestResult } from '../types';

// Track initialization across React 18 StrictMode double-mounts
const initStarted = new Set<string>();

/**
 * PretestPage
 * Initial assessment with 5 SQL questions to determine user's starting level
 */
export function PretestPage() {
  const navigate = useNavigate();
  const updateUser = useAuthStore((state) => state.updateUser);

  const [question, setQuestion] = useState<PreTestQuestion | null>(null);
  const [sqlQuery, setSqlQuery] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [result, setResult] = useState<PreTestResult | null>(null);
  const [error, setError] = useState('');

  // Initialize pretest session
  useEffect(() => {
    // Prevent double initialization in React 18 StrictMode
    if (initStarted.has('pretest')) return;
    initStarted.add('pretest');
    
    const initPretest = async () => {
      try {
        const session = await pretestService.startPretest();

        if (session.is_completed) {
          // Already completed, go to dashboard
          updateUser({ has_completed_pretest: true });
          navigate('/dashboard', { replace: true });
          return;
        }

        // Get first question
        const currentQuestion = await pretestService.getCurrentQuestion();
        setQuestion(currentQuestion);
      } catch {
        setError('Failed to start pretest. Please try again.');
      } finally {
        setIsLoading(false);
        initStarted.delete('pretest');
      }
    };

    initPretest();
  }, []); // Empty deps - only run once

  // Handle submit
  const handleSubmit = useCallback(async () => {
    if (!question || !sqlQuery.trim()) return;

    setIsSubmitting(true);
    setError('');

    try {
      const submitResult = await pretestService.submitAnswer({
        question_id: question.question_id,
        question_number: question.question_number,
        user_query: sqlQuery.trim(),
      });

      setResult(submitResult);

      if (submitResult.has_completed_pretest) {
        // Update user in store
        if (submitResult.theta_initial) {
          updateUser({
            has_completed_pretest: true,
            theta_individu: submitResult.theta_initial,
          });
        }
        // Don't auto-redirect - let user see results and click button
      }
      // Don't auto-advance - let user see feedback and click Next
    } catch (err) {
      const axiosError = err as AxiosError;
      setError(extract422ErrorMessage(axiosError));
    } finally {
      setIsSubmitting(false);
    }
  }, [question, sqlQuery, navigate, updateUser]);

  // Handle next question
  const handleNext = useCallback(async () => {
    setIsSubmitting(true);
    try {
      const nextQuestion = await pretestService.getCurrentQuestion();
      setQuestion(nextQuestion);
      setSqlQuery('');
      setResult(null);
    } catch {
      setError('Failed to load next question');
    } finally {
      setIsSubmitting(false);
    }
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading pretest...</p>
        </div>
      </div>
    );
  }

  // Completion screen
  if (result?.has_completed_pretest) {
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
            <h1 className="text-3xl font-bold text-gray-900 mb-4">Pretest Completed!</h1>
            <p className="text-gray-600 mb-6">
              You answered {result.total_correct} out of {result.total_questions} questions correctly.
            </p>
            {result.theta_initial && (
              <div className="bg-blue-50 rounded-lg p-6 mb-6">
                <p className="text-sm text-gray-600 mb-2">Your Initial Rating</p>
                <p className="text-4xl font-bold text-blue-600">{result.theta_initial.toFixed(0)}</p>
              </div>
            )}
            <button
              onClick={() => navigate('/dashboard', { replace: true })}
              className="w-full max-w-xs mx-auto bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition-colors font-medium"
            >
              Go to Dashboard
            </button>
          </div>
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      <Header />

      <main className="max-w-6xl mx-auto px-4 py-6">
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-xl font-bold text-gray-900">Pretest Assessment</h1>
            <span className="text-sm text-gray-600">
              Question {question?.question_number ?? 1} of {question?.total_questions ?? 5}
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{
                width: `${((question?.question_number ?? 1) / (question?.total_questions ?? 5)) * 100}%`,
              }}
            />
          </div>
        </div>

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
                Q{question?.question_number ?? 1}
              </span>
              {question?.topic_tags.map((tag) => (
                <span
                  key={tag}
                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded-full"
                >
                  {tag}
                </span>
              ))}
            </div>

            <h2 className="text-lg font-semibold text-gray-800 mb-4">
              {question?.content ?? 'Loading question...'}
            </h2>

            {/* Schema hint - placeholder */}
            <div className="mt-6 p-4 bg-gray-50 rounded-lg">
              <h3 className="text-sm font-medium text-gray-700 mb-2">Database Schema Diagram</h3>
              <div className="bg-white border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
                <svg className="w-12 h-12 text-gray-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
                </svg>
                <p className="text-sm text-gray-500">Relational diagram will be displayed here</p>
                <p className="text-xs text-gray-400 mt-1">Showing table relationships for this question</p>
              </div>
            </div>
          </div>

          {/* SQL Editor Panel */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-800">Your Answer</h3>
              <span className="text-xs text-gray-500">Write SQL query below</span>
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

            {result && !result.has_completed_pretest && (
              <div
                className={`mt-4 p-4 rounded-lg ${
                  result.is_correct
                    ? 'bg-green-100 text-green-800'
                    : 'bg-amber-100 text-amber-800'
                }`}
              >
                <div className="flex items-center gap-2">
                  {result.is_correct ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                  <span className="font-medium">
                    {result.is_correct ? 'Correct!' : 'Incorrect'}
                  </span>
                </div>
                <p className="text-sm mt-1">
                  Score: {result.total_correct} / {result.total_questions}
                </p>
              </div>
            )}

            {result && !result.has_completed_pretest ? (
              <button
                onClick={handleNext}
                disabled={isSubmitting}
                className="mt-6 w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
              >
                {isSubmitting ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    Loading...
                  </span>
                ) : (
                  'Next Question'
                )}
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={isSubmitting || !sqlQuery.trim() || !!result}
                className="mt-6 w-full bg-blue-600 text-white py-3 px-4 rounded-lg hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors font-medium"
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
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

export default PretestPage;
