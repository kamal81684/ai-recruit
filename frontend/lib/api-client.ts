/**
 * Centralized API Client for AI Resume Shortlisting Assistant
 *
 * This module provides a unified HTTP client with:
 * - Automatic retry with exponential backoff
 * - Request cancellation support
 * - Type-safe responses with Zod validation
 * - Standardized error handling
 * - Request/response interceptors
 * - Progress tracking for file uploads
 *
 * Contributor: shubham21155102
 */

import { z } from 'zod';
import {
  CandidateEvaluationSchema,
  CandidatesResponseSchema,
  CandidateSchema,
  JobPostsResponseSchema,
  JobPostSchema,
  InterviewQuestionsResponseSchema,
  StatisticsSchema,
  AnalyticsSchema,
  SkillGapAnalysisResponseSchema,
  type Candidate,
  type CandidateEvaluation,
  type JobPost,
  type InterviewQuestion,
  type Statistics,
  type AnalyticsData,
  type SkillGapAnalysisRequest,
  type SkillGapAnalysisResponse,
} from './schemas';

// =============================================================================
// Configuration
// =============================================================================

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

const DEFAULT_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // Base delay in ms
  maxRetryDelay: 10000, // Max delay in ms
  timeout: 60000, // Request timeout in ms
};

// =============================================================================
// Error Types
// =============================================================================

export class ApiError extends Error {
  constructor(
    public message: string,
    public status: number,
    public code?: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class NetworkError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'NetworkError';
  }
}

export class ValidationError extends Error {
  constructor(public validationErrors: string[]) {
    super('Validation failed');
    this.name = 'ValidationError';
    this.message = validationErrors.join(', ');
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message);
    this.name = 'TimeoutError';
  }
}

// =============================================================================
// Retry Logic
// =============================================================================

function calculateRetryDelay(attempt: number): number {
  const delay = DEFAULT_CONFIG.retryDelay * Math.pow(2, attempt);
  return Math.min(delay, DEFAULT_CONFIG.maxRetryDelay);
}

function shouldRetry(status: number, attempt: number): boolean {
  // Retry on network errors and 5xx errors
  return (
    attempt < DEFAULT_CONFIG.maxRetries &&
    (status >= 500 || status === 429 || status === 0)
  );
}

// =============================================================================
// Request Wrapper
// =============================================================================

interface RequestOptions extends RequestInit {
  timeout?: number;
  retries?: number;
  signal?: AbortSignal;
}

async function fetchWithRetry(
  url: string,
  options: RequestOptions = {}
): Promise<Response> {
  const { timeout = DEFAULT_CONFIG.timeout, retries = 0, ...fetchOptions } = options;

  // Create abort controller for timeout
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  // Combine external signal with timeout signal
  const combinedSignal = fetchOptions.signal
    ? combineSignals([fetchOptions.signal, controller.signal])
    : controller.signal;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      signal: combinedSignal,
    });

    clearTimeout(timeoutId);

    // Retry if needed
    if (shouldRetry(response.status, retries)) {
      const delay = calculateRetryDelay(retries);
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, { ...options, retries: retries + 1 });
    }

    return response;
  } catch (error) {
    clearTimeout(timeoutId);

    if (error instanceof Error && error.name === 'AbortError') {
      throw new TimeoutError();
    }

    // Retry on network errors
    if (retries < DEFAULT_CONFIG.maxRetries) {
      const delay = calculateRetryDelay(retries);
      await new Promise((resolve) => setTimeout(resolve, delay));
      return fetchWithRetry(url, { ...options, retries: retries + 1 });
    }

    throw new NetworkError(
      error instanceof Error ? error.message : 'Network error occurred'
    );
  }
}

// Combine multiple abort signals
function combineSignals(signals: AbortSignal[]): AbortSignal {
  const controller = new AbortController();

  for (const signal of signals) {
    if (signal.aborted) {
      controller.abort();
      break;
    }
    signal.addEventListener('abort', () => controller.abort(), { once: true });
  }

  return controller.signal;
}

// =============================================================================
// Response Handler with Validation
// =============================================================================

async function handleResponse<T>(
  response: Response,
  schema?: z.ZodSchema<T>
): Promise<T> {
  // Handle non-JSON responses
  const contentType = response.headers.get('content-type');
  if (!contentType?.includes('application/json')) {
    if (!response.ok) {
      throw new ApiError(
        response.statusText || 'Request failed',
        response.status
      );
    }
    return undefined as T;
  }

  const data = await response.json();

  // Handle error responses
  if (!response.ok) {
    throw new ApiError(
      data.error || response.statusText || 'Request failed',
      response.status,
      data.code,
      data.details
    );
  }

  // Validate with schema if provided
  if (schema) {
    try {
      return schema.parseAsync(data) as Promise<T>;
    } catch (error) {
      if (error instanceof z.ZodError) {
        throw new ValidationError(
          error.errors.map((e) => `${e.path.join('.')}: ${e.message}`)
        );
      }
      throw error;
    }
  }

  return data as T;
}

// =============================================================================
// API Client
// =============================================================================

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_URL) {
    this.baseUrl = baseUrl;
  }

  /**
   * Generic GET request
   */
  async get<T>(
    endpoint: string,
    schema?: z.ZodSchema<T>,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetchWithRetry(url, {
      ...options,
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    return handleResponse(response, schema);
  }

  /**
   * Generic POST request
   */
  async post<T>(
    endpoint: string,
    data: unknown,
    schema?: z.ZodSchema<T>,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetchWithRetry(url, {
      ...options,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response, schema);
  }

  /**
   * Generic PUT request
   */
  async put<T>(
    endpoint: string,
    data: unknown,
    schema?: z.ZodSchema<T>,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetchWithRetry(url, {
      ...options,
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      body: JSON.stringify(data),
    });
    return handleResponse(response, schema);
  }

  /**
   * Generic DELETE request
   */
  async delete<T>(
    endpoint: string,
    schema?: z.ZodSchema<T>,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const response = await fetchWithRetry(url, {
      ...options,
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });
    return handleResponse(response, schema);
  }

  /**
   * Upload file with progress tracking
   */
  async uploadFile<T>(
    endpoint: string,
    formData: FormData,
    onProgress?: (progress: number) => void,
    schema?: z.ZodSchema<T>,
    options?: RequestOptions
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // For progress tracking, we need XMLHttpRequest
    if (onProgress && typeof XMLHttpRequest !== 'undefined') {
      return new Promise<T>((resolve, reject) => {
        const xhr = new XMLHttpRequest();

        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable) {
            onProgress((e.loaded / e.total) * 100);
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              if (schema) {
                const result = schema.safeParse(data);
                if (result.success) {
                  resolve(result.data as T);
                } else {
                  reject(new ValidationError(
                    result.error.errors.map((e) => `${e.path.join('.')}: ${e.message}`)
                  ));
                }
              } else {
                resolve(data as T);
              }
            } catch (error) {
              reject(error);
            }
          } else {
            try {
              const errorData = JSON.parse(xhr.responseText);
              reject(new ApiError(
                errorData.error || 'Upload failed',
                xhr.status,
                errorData.code
              ));
            } catch {
              reject(new ApiError('Upload failed', xhr.status));
            }
          }
        });

        xhr.addEventListener('error', () => {
          reject(new NetworkError('Upload failed'));
        });

        xhr.addEventListener('timeout', () => {
          reject(new TimeoutError());
        });

        xhr.open('POST', url);
        xhr.timeout = options?.timeout || DEFAULT_CONFIG.timeout;
        xhr.send(formData);
      });
    }

    // Fallback to regular fetch if progress tracking not needed
    const response = await fetchWithRetry(url, {
      ...options,
      method: 'POST',
      body: formData as unknown as BodyInit,
      // Don't set Content-Type for FormData, browser will handle it
    });
    return handleResponse(response, schema);
  }

  // ==========================================================================
  // API Endpoint Methods
  // ==========================================================================

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; message?: string }> {
    return this.get('/health');
  }

  /**
   * Evaluate a candidate resume
   */
  async evaluateCandidate(
    jobDescription: string,
    resumeFile: File,
    onProgress?: (progress: number) => void
  ): Promise<CandidateEvaluation> {
    const formData = new FormData();
    formData.append('jobDescription', jobDescription);
    formData.append('resume', resumeFile);

    return this.uploadFile(
      '/api/evaluate',
      formData,
      onProgress,
      CandidateEvaluationSchema
    );
  }

  /**
   * Get all candidates with optional filters
   */
  async getCandidates(params?: {
    limit?: number;
    offset?: number;
    tier?: string;
  }): Promise<{ candidates: Candidate[]; count: number }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.tier) searchParams.append('tier', params.tier);

    const query = searchParams.toString();
    return this.get(
      `/api/candidates${query ? `?${query}` : ''}`,
      CandidatesResponseSchema
    );
  }

  /**
   * Get a single candidate by ID
   */
  async getCandidate(id: number): Promise<Candidate> {
    return this.get(`/api/candidates/${id}`, CandidateSchema);
  }

  /**
   * Delete a candidate
   */
  async deleteCandidate(id: number): Promise<{ message: string }> {
    return this.delete(`/api/candidates/${id}`);
  }

  /**
   * Get interview questions for a candidate
   */
  async getInterviewQuestions(
    candidateId: number
  ): Promise<{ questions: InterviewQuestion[] }> {
    return this.get(
      `/api/candidates/${candidateId}/interview-questions`,
      InterviewQuestionsResponseSchema
    );
  }

  /**
   * Generate interview questions for a candidate
   */
  async generateInterviewQuestions(
    candidateId: number
  ): Promise<{ questions: InterviewQuestion[] }> {
    return this.post(
      `/api/candidates/${candidateId}/interview-questions`,
      {},
      InterviewQuestionsResponseSchema
    );
  }

  /**
   * Get statistics
   */
  async getStatistics(): Promise<Statistics> {
    return this.get('/api/statistics', StatisticsSchema);
  }

  /**
   * Get analytics data
   */
  async getAnalytics(): Promise<AnalyticsData> {
    return this.get('/api/analytics', AnalyticsSchema);
  }

  /**
   * Analyze skill gap
   */
  async analyzeSkillGap(
    request: SkillGapAnalysisRequest
  ): Promise<SkillGapAnalysisResponse> {
    return this.post(
      '/api/analytics/skill-gap',
      request,
      SkillGapAnalysisResponseSchema
    );
  }

  /**
   * Get all job posts
   */
  async getJobPosts(params?: {
    limit?: number;
    offset?: number;
    status?: string;
  }): Promise<{ job_posts: JobPost[]; count: number }> {
    const searchParams = new URLSearchParams();
    if (params?.limit) searchParams.append('limit', params.limit.toString());
    if (params?.offset) searchParams.append('offset', params.offset.toString());
    if (params?.status) searchParams.append('status', params.status);

    const query = searchParams.toString();
    return this.get(
      `/api/jobs${query ? `?${query}` : ''}`,
      JobPostsResponseSchema
    );
  }

  /**
   * Get a single job post
   */
  async getJobPost(id: number): Promise<JobPost> {
    return this.get(`/api/jobs/${id}`, JobPostSchema);
  }

  /**
   * Create a new job post
   */
  async createJobPost(data: {
    title: string;
    description: string;
    location?: string;
    requirements?: string;
    status?: string;
  }): Promise<{ message: string; job_id: number }> {
    return this.post(`/api/jobs`, data);
  }

  /**
   * Update a job post
   */
  async updateJobPost(
    id: number,
    data: {
      title?: string;
      description?: string;
      location?: string;
      requirements?: string;
      status?: string;
    }
  ): Promise<{ message: string }> {
    return this.put(`/api/jobs/${id}`, data);
  }

  /**
   * Delete a job post
   */
  async deleteJobPost(id: number): Promise<{ message: string }> {
    return this.delete(`/api/jobs/${id}`);
  }

  /**
   * Generate AI job post
   */
  async generateJobPost(data: {
    title: string;
    location?: string;
    additional_info?: string;
  }): Promise<{ description: string; requirements: string }> {
    return this.post('/api/jobs/generate-ai', data);
  }
}

// =============================================================================
// Export singleton instance
// =============================================================================

export const apiClient = new ApiClient();

// Export types for external use
export type {
  Candidate,
  CandidateEvaluation,
  JobPost,
  InterviewQuestion,
  Statistics,
  AnalyticsData,
  SkillGapAnalysisRequest,
  SkillGapAnalysisResponse,
};
