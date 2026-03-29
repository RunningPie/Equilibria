import { create, type StoreApi } from 'zustand';
import zukeeper from 'zukeeper';
import type { Question, AssessmentSession } from '../types';

interface SessionState {
  // State
  activeSession: AssessmentSession | null;
  currentQuestion: Question | null;
  attemptCount: number; // attempt ke berapa di soal aktif (1–3)
  canRetry: boolean; // attemptCount < 3 && !isCorrect
  questionStartTime: number; // Date.now() saat soal pertama kali ditampilkan
  lastSubmitResult: {
    isCorrect: boolean;
    feedback: string;
    thetaBefore: number | null;
    thetaAfter: number | null;
  } | null;

  // Actions
  startSession: (session: AssessmentSession) => void;
  setCurrentQuestion: (question: Question) => void;
  incrementAttempt: () => void;
  setCanRetry: (canRetry: boolean) => void;
  setLastSubmitResult: (result: {
    isCorrect: boolean;
    feedback: string;
    thetaBefore: number | null;
    thetaAfter: number | null;
  }) => void;
  resetQuestionTimer: () => void;
  clearSession: () => void;
  endSession: () => void;
}

export const useSessionStore = create<SessionState>()(
  zukeeper((set: StoreApi<SessionState>['setState']) => ({
    // Initial state
    activeSession: null,
    currentQuestion: null,
    attemptCount: 0,
    canRetry: true,
    questionStartTime: Date.now(),
    lastSubmitResult: null,

    // Start a new session
    startSession: (session: AssessmentSession) => {
      set({
        activeSession: session,
        currentQuestion: null,
        attemptCount: 0,
        canRetry: true,
        questionStartTime: Date.now(),
        lastSubmitResult: null,
      });
    },

    // Set current question (when loading a question)
    setCurrentQuestion: (question: Question) => {
      set({
        currentQuestion: question,
        attemptCount: question.attempt_count || 0,
        canRetry: question.attempt_count < 3,
        questionStartTime: Date.now(),
        lastSubmitResult: null,
      });
    },

    // Increment attempt counter
    incrementAttempt: () => {
      set((state: SessionState) => {
        const newAttemptCount = state.attemptCount + 1;
        return {
          attemptCount: newAttemptCount,
          canRetry: newAttemptCount < 3,
        };
      });
    },

    // Set canRetry manually
    setCanRetry: (canRetry: boolean) => {
      set({ canRetry });
    },

    // Store last submit result
    setLastSubmitResult: (result: { isCorrect: boolean; feedback: string; thetaBefore: number | null; thetaAfter: number | null; }) => {
      set({ lastSubmitResult: result });
    },

    // Reset question timer (when new question loads)
    resetQuestionTimer: () => {
      set({
        questionStartTime: Date.now(),
        attemptCount: 0,
        canRetry: true,
        lastSubmitResult: null,
      });
    },

    // Clear session state (logout or hard reset)
    clearSession: () => {
      set({
        activeSession: null,
        currentQuestion: null,
        attemptCount: 0,
        canRetry: true,
        questionStartTime: Date.now(),
        lastSubmitResult: null,
      });
    },

    // End session (mark as completed but keep for viewing)
    endSession: () => {
      set((state: SessionState) => ({
        activeSession: state.activeSession
          ? { ...state.activeSession, status: 'COMPLETED' }
          : null,
        currentQuestion: null,
        attemptCount: 0,
        canRetry: false,
        lastSubmitResult: null,
      }));
    },
  }))
);

// Selector hooks for convenience
export const useActiveSession = () => useSessionStore((state) => state.activeSession);
export const useCurrentQuestion = () => useSessionStore((state) => state.currentQuestion);
export const useAttemptCount = () => useSessionStore((state) => state.attemptCount);
export const useCanRetry = () => useSessionStore((state) => state.canRetry);
export const useQuestionStartTime = () => useSessionStore((state) => state.questionStartTime);
export const useLastSubmitResult = () => useSessionStore((state) => state.lastSubmitResult);
