/**
 * Shared Type Definitions for AI Resume Shortlisting Assistant
 *
 * This file contains type definitions that are shared between the frontend and backend.
 * These types ensure type safety and consistency across the application.
 *
 * Contributor: shubham21155102
 */

// =============================================================================
// Candidate Types
// =============================================================================

export interface EvaluationScore {
  score: number;
  explanation: string;
}

export interface CandidateEvaluation {
  tier: string;
  summary: string;
  exact_match: EvaluationScore;
  similarity_match: EvaluationScore;
  achievement_impact: EvaluationScore;
  ownership: EvaluationScore;
}

export interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string;
  resume_filename: string;
  tier: string;
  summary: string;
  exact_match_score: number;
  similarity_match_score: number;
  achievement_impact_score: number;
  ownership_score: number;
  exact_match_explanation?: string;
  similarity_match_explanation?: string;
  achievement_impact_explanation?: string;
  ownership_explanation?: string;
  location?: string;
  skills?: string;
  education?: string;
  experience_years?: number;
  current_role?: string;
  created_at: string;
}

// =============================================================================
// Job Post Types
// =============================================================================

export interface JobPost {
  id: number;
  title: string;
  description: string;
  location?: string;
  requirements?: string;
  status: 'active' | 'inactive' | 'draft' | 'closed';
  created_at: string;
  updated_at?: string;
}

export interface CreateJobPostRequest {
  title: string;
  description: string;
  location?: string;
  requirements?: string;
  status?: string;
}

export interface UpdateJobPostRequest {
  title?: string;
  description?: string;
  location?: string;
  requirements?: string;
  status?: string;
}

// =============================================================================
// Interview Question Types
// =============================================================================

export interface InterviewQuestion {
  id: number;
  candidate_id: number;
  question: string;
  category: 'Technical' | 'Behavioral' | 'Cultural' | 'General';
  created_at: string;
}

// =============================================================================
// API Response Types
// =============================================================================

export interface ApiError {
  error: string;
  code?: string;
  details?: unknown;
}

export interface ApiResponse<T> {
  data?: T;
  error?: string;
  status: number;
}

export interface CandidatesResponse {
  candidates: Candidate[];
  count: number;
}

export interface CandidateResponse extends Candidate {}

export interface JobPostsResponse {
  job_posts: JobPost[];
  count: number;
}

export interface InterviewQuestionsResponse {
  questions: InterviewQuestion[];
}

// =============================================================================
// Statistics Types
// =============================================================================

export interface Statistics {
  total_candidates: number;
  by_tier: Record<string, number>;
  average_scores: {
    exact_match: number;
    similarity_match: number;
    achievement_impact: number;
    ownership: number;
  };
}

export interface AnalyticsData {
  by_tier: Record<string, number>;
  candidates_over_time: [string, number][];
  active_jobs: number;
  avg_scores_by_tier: Record<string, {
    exact_match: number;
    similarity_match: number;
    achievement_impact: number;
    ownership: number;
  }>;
  top_locations: [string, number][];
  recent_candidates: Candidate[];
  total_candidates: number;
}

export interface SkillGapAnalysisRequest {
  job_skills: string[];
}

export interface SkillGapAnalysisResponse {
  missing_skills: string[];
  coverage_percentage: number;
  candidate_count: number;
  found_skills: string[];
  recommendations: string[];
}

// =============================================================================
// Evaluation Request Types
// =============================================================================

export interface EvaluateRequest {
  jobDescription: string;
  resume: File;
}

export interface EvaluateResponse extends CandidateEvaluation {
  candidate_id?: number;
  extracted_info?: {
    name: string;
    email: string;
    phone: string;
    location?: string;
    skills?: string;
    education?: string;
    experience_years?: number;
    current_role?: string;
  };
}

// =============================================================================
// Filter and Pagination Types
// =============================================================================

export interface PaginationParams {
  limit?: number;
  offset?: number;
}

export interface CandidateFilters extends PaginationParams {
  tier?: string;
  search?: string;
}

export interface JobPostFilters extends PaginationParams {
  status?: string;
}

// =============================================================================
// Upload Types
// =============================================================================

export interface UploadProgress {
  loaded: number;
  total: number;
  percentage: number;
}

export interface UploadState {
  file: File | null;
  uploading: boolean;
  progress: number;
  error: string | null;
  result: CandidateEvaluation | null;
}

// =============================================================================
// WebSocket Types
// =============================================================================

export type WebSocketEventType =
  | 'task.started'
  | 'task.progress'
  | 'task.completed'
  | 'task.failed'
  | 'candidate.added'
  | 'candidate.updated';

export interface WebSocketMessage<T = unknown> {
  type: WebSocketEventType;
  data: T;
  timestamp: string;
}

export interface TaskProgressData {
  task_id: string;
  progress: number;
  status: 'processing' | 'parsing' | 'evaluating' | 'completed' | 'failed';
  message?: string;
}

// =============================================================================
// UI State Types
// =============================================================================

export type TierType = 'Tier A' | 'Tier B' | 'Tier C';

export interface SortConfig {
  key: keyof Candidate | string;
  direction: 'asc' | 'desc';
}

export interface ColumnConfig {
  key: string;
  label: string;
  sortable: boolean;
  visible: boolean;
  width?: string;
}

// =============================================================================
// Export all types as a namespace for cleaner imports
// =============================================================================

export const Types = {
  Candidate,
  JobPost,
  InterviewQuestion,
  Statistics,
  AnalyticsData,
  CandidateEvaluation,
  EvaluationScore,
} as const;
