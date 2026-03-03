/**
 * Zod Validation Schemas for AI Resume Shortlisting Assistant
 *
 * This file contains runtime validation schemas using Zod.
 * These schemas validate API responses and ensure data integrity.
 *
 * Contributor: shubham21155102
 */

import { z } from 'zod';

// =============================================================================
// Base Schemas
// =============================================================================

/**
 * Schema for evaluation score with explanation
 */
export const EvaluationScoreSchema = z.object({
  score: z.number().min(0).max(100),
  explanation: z.string(),
});

/**
 * Schema for candidate evaluation result
 */
export const CandidateEvaluationSchema = z.object({
  tier: z.enum(['Tier A', 'Tier B', 'Tier C']),
  summary: z.string(),
  exact_match: z.object({
    score: z.number().min(0).max(100),
    explanation: z.string(),
  }),
  similarity_match: z.object({
    score: z.number().min(0).max(100),
    explanation: z.string(),
  }),
  achievement_impact: z.object({
    score: z.number().min(0).max(100),
    explanation: z.string(),
  }),
  ownership: z.object({
    score: z.number().min(0).max(100),
    explanation: z.string(),
  }),
  candidate_id: z.number().optional(),
  extracted_info: z.object({
    name: z.string(),
    email: z.string().email(),
    phone: z.string(),
    location: z.string().optional(),
    skills: z.string().optional(),
    education: z.string().optional(),
    experience_years: z.number().optional(),
    current_role: z.string().optional(),
  }).optional(),
});

// =============================================================================
// Candidate Schemas
// =============================================================================

/**
 * Schema for a single candidate
 */
export const CandidateSchema = z.object({
  id: z.number(),
  name: z.string(),
  email: z.string().email(),
  phone: z.string(),
  resume_filename: z.string(),
  tier: z.enum(['Tier A', 'Tier B', 'Tier C']),
  summary: z.string(),
  exact_match_score: z.number().min(0).max(100),
  similarity_match_score: z.number().min(0).max(100),
  achievement_impact_score: z.number().min(0).max(100),
  ownership_score: z.number().min(0).max(100),
  exact_match_explanation: z.string().optional(),
  similarity_match_explanation: z.string().optional(),
  achievement_impact_explanation: z.string().optional(),
  ownership_explanation: z.string().optional(),
  location: z.string().optional(),
  skills: z.string().optional(),
  education: z.string().optional(),
  experience_years: z.number().optional(),
  current_role: z.string().optional(),
  created_at: z.string(),
});

/**
 * Schema for candidates list response
 */
export const CandidatesResponseSchema = z.object({
  candidates: z.array(CandidateSchema),
  count: z.number(),
});

// =============================================================================
// Job Post Schemas
// =============================================================================

/**
 * Schema for job post status
 */
const JobPostStatusSchema = z.enum(['active', 'inactive', 'draft', 'closed']);

/**
 * Schema for creating a job post
 */
export const CreateJobPostSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  description: z.string().min(1, 'Description is required'),
  location: z.string().optional(),
  requirements: z.string().optional(),
  status: JobPostStatusSchema.optional(),
});

/**
 * Schema for updating a job post (all fields optional)
 */
export const UpdateJobPostSchema = z.object({
  title: z.string().min(1).optional(),
  description: z.string().min(1).optional(),
  location: z.string().optional(),
  requirements: z.string().optional(),
  status: JobPostStatusSchema.optional(),
});

/**
 * Schema for a single job post
 */
export const JobPostSchema = z.object({
  id: z.number(),
  title: z.string(),
  description: z.string(),
  location: z.string().optional(),
  requirements: z.string().optional(),
  status: JobPostStatusSchema,
  created_at: z.string(),
  updated_at: z.string().optional(),
});

/**
 * Schema for job posts list response
 */
export const JobPostsResponseSchema = z.object({
  job_posts: z.array(JobPostSchema),
  count: z.number(),
});

// =============================================================================
// Interview Question Schemas
// =============================================================================

/**
 * Schema for interview question category
 */
const QuestionCategorySchema = z.enum(['Technical', 'Behavioral', 'Cultural', 'General']);

/**
 * Schema for a single interview question
 */
export const InterviewQuestionSchema = z.object({
  id: z.number(),
  candidate_id: z.number(),
  question: z.string(),
  category: QuestionCategorySchema,
  created_at: z.string(),
});

/**
 * Schema for interview questions list response
 */
export const InterviewQuestionsResponseSchema = z.object({
  questions: z.array(InterviewQuestionSchema),
});

// =============================================================================
// Statistics Schemas
// =============================================================================

/**
 * Schema for average scores
 */
const AverageScoresSchema = z.object({
  exact_match: z.number(),
  similarity_match: z.number(),
  achievement_impact: z.number(),
  ownership: z.number(),
});

/**
 * Schema for statistics response
 */
export const StatisticsSchema = z.object({
  total_candidates: z.number(),
  by_tier: z.record(z.string(), z.number()),
  average_scores: AverageScoresSchema,
});

/**
 * Schema for tier-specific average scores
 */
const TierAverageScoresSchema = z.object({
  exact_match: z.number(),
  similarity_match: z.number(),
  achievement_impact: z.number(),
  ownership: z.number(),
});

/**
 * Schema for analytics response
 */
export const AnalyticsSchema = z.object({
  by_tier: z.record(z.string(), z.number()),
  candidates_over_time: z.tuple([z.string(), z.number()]).array(),
  active_jobs: z.number(),
  avg_scores_by_tier: z.record(z.string(), TierAverageScoresSchema),
  top_locations: z.tuple([z.string(), z.number()]).array(),
  recent_candidates: z.array(CandidateSchema),
  total_candidates: z.number(),
});

// =============================================================================
// Skill Gap Analysis Schemas
// =============================================================================

/**
 * Schema for skill gap analysis request
 */
export const SkillGapAnalysisRequestSchema = z.object({
  job_skills: z.array(z.string()).min(1, 'At least one skill is required'),
});

/**
 * Schema for skill gap analysis response
 */
export const SkillGapAnalysisResponseSchema = z.object({
  missing_skills: z.array(z.string()),
  coverage_percentage: z.number(),
  candidate_count: z.number(),
  found_skills: z.array(z.string()),
  recommendations: z.array(z.string()),
});

// =============================================================================
// API Error Schemas
// =============================================================================

/**
 * Schema for API error response
 */
export const ApiErrorSchema = z.object({
  error: z.string(),
  code: z.string().optional(),
  details: z.unknown().optional(),
});

// =============================================================================
// Health Check Schema
// =============================================================================

/**
 * Schema for health check response
 */
export const HealthCheckSchema = z.object({
  status: z.string(),
  message: z.string().optional(),
});

// =============================================================================
// Pagination Schemas
// =============================================================================

/**
 * Schema for pagination parameters
 */
export const PaginationParamsSchema = z.object({
  limit: z.coerce.number().min(1).max(100).optional().default(50),
  offset: z.coerce.number().min(0).optional().default(0),
});

/**
 * Schema for candidate filter parameters
 */
export const CandidateFiltersSchema = PaginationParamsSchema.extend({
  tier: z.enum(['Tier A', 'Tier B', 'Tier C']).optional(),
  search: z.string().optional(),
});

/**
 * Schema for job post filter parameters
 */
export const JobPostFiltersSchema = PaginationParamsSchema.extend({
  status: JobPostStatusSchema.optional(),
});

// =============================================================================
// Type Inference from Schemas
// =============================================================================

/**
 * Infer TypeScript types from Zod schemas
 */
export type EvaluationScore = z.infer<typeof EvaluationScoreSchema>;
export type CandidateEvaluation = z.infer<typeof CandidateEvaluationSchema>;
export type Candidate = z.infer<typeof CandidateSchema>;
export type CandidatesResponse = z.infer<typeof CandidatesResponseSchema>;
export type CreateJobPost = z.infer<typeof CreateJobPostSchema>;
export type UpdateJobPost = z.infer<typeof UpdateJobPostSchema>;
export type JobPost = z.infer<typeof JobPostSchema>;
export type JobPostsResponse = z.infer<typeof JobPostsResponseSchema>;
export type InterviewQuestion = z.infer<typeof InterviewQuestionSchema>;
export type InterviewQuestionsResponse = z.infer<typeof InterviewQuestionsResponseSchema>;
export type Statistics = z.infer<typeof StatisticsSchema>;
export type AnalyticsData = z.infer<typeof AnalyticsSchema>;
export type SkillGapAnalysisRequest = z.infer<typeof SkillGapAnalysisRequestSchema>;
export type SkillGapAnalysisResponse = z.infer<typeof SkillGapAnalysisResponseSchema>;
export type ApiError = z.infer<typeof ApiErrorSchema>;
export type HealthCheck = z.infer<typeof HealthCheckSchema>;
export type PaginationParams = z.infer<typeof PaginationParamsSchema>;
export type CandidateFilters = z.infer<typeof CandidateFiltersSchema>;
export type JobPostFilters = z.infer<typeof JobPostFiltersSchema>;

// =============================================================================
// Validation Helper Functions
// =============================================================================

/**
 * Safely parse data with a schema, returning null if validation fails
 */
export function safeParse<T>(
  schema: z.ZodSchema<T>,
  data: unknown
): { success: true; data: T } | { success: false; error: z.ZodError } {
  const result = schema.safeParse(data);
  if (result.success) {
    return { success: true, data: result.data };
  }
  return { success: false, error: result.error };
}

/**
 * Validate data with a schema, throwing an error if validation fails
 */
export function validate<T>(schema: z.ZodSchema<T>, data: unknown): T {
  return schema.parse(data);
}

/**
 * Format Zod error for display
 */
export function formatZodError(error: z.ZodError): string {
  return error.errors
    .map((e) => `${e.path.join('.')}: ${e.message}`)
    .join(', ');
}
