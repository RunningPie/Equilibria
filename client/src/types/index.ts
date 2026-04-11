/**
 * TypeScript interfaces matching backend schemas
 * Based on technical specifications v4.3 and FastAPI backend schemas
 */

// ============================================
// JSend Response Wrapper
// ============================================
export interface JSendResponse<T> {
  status: 'success' | 'fail' | 'error';
  code: number;
  data: T | null;
  message: string | null;
}

// ============================================
// User / Authentication Types
// ============================================
export interface User {
  user_id: string;
  nim: string;
  full_name: string;
  theta_individu: number;
  theta_social: number;
  k_factor: number;
  total_attempts: number;
  status: 'ACTIVE' | 'NEEDS_PEER_REVIEW';
  has_completed_pretest: boolean;
  group_assignment: 'A' | 'B';
  stagnation_ever_detected: boolean;
  is_admin: boolean;
  is_deleted?: boolean;
  deleted_at?: string | null;
  created_at: string;
}

export interface UserLoginRequest {
  nim: string;
  password: string;
}

export interface UserRegisterRequest {
  nim: string;
  full_name: string;
  password: string;
  group_assignment?: 'A' | 'B';
}

export interface UserUpdateRequest {
  full_name?: string;
  old_password?: string;
  new_password?: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LogoutResponse {
  message: string;
}

// ============================================
// Session Types
// ============================================
export interface AssessmentSession {
  session_id: string;
  module_id: string;
  status: 'ACTIVE' | 'COMPLETED' | 'ABANDONED';
  user_theta_start: number;
  user_theta_current: number;
  questions_served: number;
  questions_completed: number;
  started_at: string;
  ended_at: string | null;
  current_question_id: string | null;
}

export interface SessionStartRequest {
  module_id: string;
}

export interface SessionStartResult {
  session_id: string;
  module_id: string;
  user_theta: number;
  status: string;
  started_at: string;
}

export interface Question {
  session_id: string;
  question_id: string;
  module_id: string;
  content: string;
  current_difficulty: number;
  attempt_count: number;
  max_attempts: number;
}

export interface SessionStatus {
  session_id: string;
  module_id: string;
  status: string;
  user_theta_start: number;
  user_theta_current: number;
  questions_served: number;
  questions_completed: number;
  started_at: string;
  ended_at: string | null;
  current_question_id: string | null;
}

// ============================================
// Query Result Type
// ============================================
export interface QueryResult {
  rows: Record<string, unknown>[];
  row_count: number;
}

// ============================================
// Submit / Next Types
// ============================================
export interface SubmitRequest {
  question_id: string;
  user_query: string;
  execution_time_ms: number;
}

export interface SubmitResult {
  is_correct: boolean;
  is_final_attempt: boolean;
  attempt_number: number;
  feedback: string;
  theta_before: number | null;
  theta_after: number | null;
  next_question_available: boolean;
  user_query_result?: QueryResult;
  error_message?: string;
}

export interface NextResult {
  session_id: string;
  question_id: string;
  module_id: string;
  content: string;
  current_difficulty: number;
  attempt_count: number;
  max_attempts: number;
  theta_before: number | null;
  theta_after: number | null;
  previous_question_id: string | null;
  theta_change: number | null;
  stagnation_detected: boolean;
  peer_session_created: boolean;
  questions_served: number;
  total_questions_available: number;
  max_questions_reached?: boolean;
  next_chapter_unlocked?: boolean;
  unlocked_module?: string;
}

// ============================================
// Module Types
// ============================================
export interface Module {
  module_id: string;
  title: string;
  description: string;
  difficulty_min: number;
  difficulty_max: number;
  unlock_theta_threshold: number;
  content_html: string;
  order_index: number;
}

export interface ModuleProgress {
  module_id: string;
  is_unlocked: boolean;
  is_completed: boolean;
  started_at: string | null;
  completed_at: string | null;
}

// ============================================
// Profile / Stats Types
// ============================================
export interface ProfileStats {
  theta_individu: number;
  theta_social: number;
  theta_display: number;
  total_attempts: number;
  k_factor: number;
  module_progress: ModuleProgress[];
  accuracy_rate: number;
}

// ============================================
// Helper Types
// ============================================
export interface ActiveSessionCheck {
  session_id: string;
  module_id: string;
  started_at: string;
}

// ============================================
// Pretest Types
// ============================================
export interface PreTestSessionResponse {
  session_id: string;
  current_question_index: number;
  total_questions: number;
  started_at: string;
  completed_at: string | null;
  is_completed: boolean;
}

export interface PreTestQuestion {
  question_id: string;
  content: string;
  question_number: number;
  total_questions: number;
  topic_tags: string[];
}

export interface PreTestResult {
  session_id: string;
  theta_initial: number | null;
  has_completed_pretest: boolean;
  total_correct: number;
  total_questions: number;
  redirect: string | null;
  is_correct: boolean;
  user_query_result?: QueryResult;
  error_message?: string;
}

export interface PreTestAnswerSubmit {
  question_id: string;
  question_number: number;
  user_query: string;
}

// For theta_display calculation
export const calculateThetaDisplay = (thetaIndividu: number, thetaSocial: number): number => {
  return 0.8 * thetaIndividu + 0.2 * thetaSocial;
};

// ============================================
// Collaboration / Peer Review Types
// ============================================
export interface PeerSessionInboxItem {
  session_id: string;
  question_preview: string;
  status: 'PENDING_REVIEW' | 'WAITING_CONFIRMATION' | 'COMPLETED';
  created_at: string;
}

export interface PeerSessionDetail {
  session_id: string;
  question: {
    content: string;
    topic_tags: string[];
  };
  requester_query: string;
  status: string;
  expires_at: string | null;
}

export interface ReviewSubmitRequest {
  review_content: string;
}

export interface ReviewSubmitResult {
  session_id: string;
  system_score: number;
  status: string;
}

export interface PeerSessionRequest {
  session_id: string;
  question_preview: string;
  status: 'PENDING_REVIEW' | 'WAITING_CONFIRMATION' | 'COMPLETED';
  created_at: string;
  review_content: string | null;
}

export interface RateRequest {
  is_helpful: boolean;
}

export interface RateResult {
  final_score: number;
  reviewer_theta_social_before: number;
  reviewer_theta_social_after: number;
}

// ============================================
// Leaderboard Types
// ============================================
export interface LeaderboardEntry {
  rank: number;
  user_id: string;
  display_name: string;
  theta_display: number;
  is_self: boolean;
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[];
  total: number;
  limit: number;
  offset: number;
}

// ============================================
// Admin Types
// ============================================
export interface AdminUserCreateRequest {
  nim: string;
  full_name: string;
  password: string;
  group_assignment?: 'A' | 'B';
  is_admin?: boolean;
}

export interface AdminUserUpdateRequest {
  full_name?: string;
  password?: string;
  group_assignment?: 'A' | 'B';
  status?: string;
  is_admin?: boolean;
  theta_individu?: number;
  theta_social?: number;
}

export interface UserListResponse {
  users: User[];
  total: number;
  page: number;
  page_size: number;
}

export interface LogEntry {
  timestamp?: string;
  level?: string;
  message: string;
  extra?: Record<string, unknown>;
}

export interface LogsResponse {
  date?: string;
  files: string[];
  logs: LogEntry[];
  total_entries: number;
}
