/**
 * Skeleton Loading Components for AI Recruit
 *
 * These components provide skeleton loading screens for better perceived performance.
 * Skeleton screens show placeholder UI elements that match the actual content shape,
 * reducing perceived latency compared to generic spinners.
 *
 * Contributor: shubham21155102 - UX Enhancements
 */

import React from 'react';

interface SkeletonProps {
  className?: string;
}

/**
 * Base skeleton component with shimmer animation
 */
export function Skeleton({ className = '' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-slate-200 rounded ${className}`}
      role="status"
      aria-label="Loading..."
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}

/**
 * Skeleton for candidate card/row
 */
export function CandidateRowSkeleton() {
  return (
    <tr className="animate-pulse">
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-slate-200 rounded-full" />
          <div className="space-y-2">
            <div className="h-4 bg-slate-200 rounded w-32" />
            <div className="h-3 bg-slate-200 rounded w-48" />
          </div>
        </div>
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-slate-200 rounded w-24" />
      </td>
      <td className="px-6 py-4">
        <div className="h-4 bg-slate-200 rounded w-20" />
      </td>
      <td className="px-6 py-4">
        <div className="h-6 bg-slate-200 rounded-full w-16" />
      </td>
      <td className="px-6 py-4">
        <div className="flex items-center gap-3">
          <div className="h-2 bg-slate-200 rounded-full w-24" />
          <div className="h-4 bg-slate-200 rounded w-8" />
        </div>
      </td>
      <td className="px-6 py-4 text-right">
        <div className="h-4 bg-slate-200 rounded w-20 ml-auto" />
      </td>
    </tr>
  );
}

/**
 * Skeleton for candidate table
 */
export function CandidateTableSkeleton({ count = 5 }: { count?: number }) {
  return (
    <>
      <thead className="bg-slate-50">
        <tr>
          <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Name</th>
          <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Role</th>
          <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Location</th>
          <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Tier</th>
          <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase">Match</th>
          <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase text-right">Actions</th>
        </tr>
      </thead>
      <tbody className="divide-y divide-slate-100">
        {Array.from({ length: count }).map((_, i) => (
          <CandidateRowSkeleton key={i} />
        ))}
      </tbody>
    </>
  );
}

/**
 * Skeleton for statistics cards
 */
export function StatsCardSkeleton() {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm animate-pulse">
      <div className="flex items-center justify-between mb-2">
        <div className="h-4 bg-slate-200 rounded w-32" />
        <div className="h-10 w-10 bg-slate-200 rounded-lg" />
      </div>
      <div className="h-8 bg-slate-200 rounded w-20 mb-2" />
      <div className="h-3 bg-slate-200 rounded w-40" />
    </div>
  );
}

/**
 * Skeleton for stats grid
 */
export function StatsGridSkeleton({ count = 4 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <StatsCardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * Skeleton for leaderboard entry
 */
export function LeaderboardEntrySkeleton({ rank = 1 }: { rank?: number }) {
  return (
    <div className="flex items-center gap-4 p-4 bg-white rounded-lg border border-slate-100 animate-pulse">
      <div className="h-8 w-8 bg-slate-200 rounded-lg flex items-center justify-center font-bold">
        {rank}
      </div>
      <div className="h-12 w-12 bg-slate-200 rounded-full" />
      <div className="flex-1">
        <div className="h-4 bg-slate-200 rounded w-32 mb-2" />
        <div className="h-3 bg-slate-200 rounded w-48" />
      </div>
      <div className="text-right">
        <div className="h-6 bg-slate-200 rounded w-16 mb-1 ml-auto" />
        <div className="h-3 bg-slate-200 rounded w-20 ml-auto" />
      </div>
    </div>
  );
}

/**
 * Skeleton for leaderboard
 */
export function LeaderboardSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-2">
      {Array.from({ length: count }).map((_, i) => (
        <LeaderboardEntrySkeleton key={i} rank={i + 1} />
      ))}
    </div>
  );
}

/**
 * Skeleton for job post card
 */
export function JobCardSkeleton() {
  return (
    <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm animate-pulse">
      <div className="flex items-start justify-between mb-4">
        <div className="flex-1">
          <div className="h-6 bg-slate-200 rounded w-48 mb-2" />
          <div className="h-4 bg-slate-200 rounded w-32" />
        </div>
        <div className="h-6 bg-slate-200 rounded-full w-16" />
      </div>
      <div className="space-y-2 mb-4">
        <div className="h-4 bg-slate-200 rounded w-full" />
        <div className="h-4 bg-slate-200 rounded w-full" />
        <div className="h-4 bg-slate-200 rounded w-2/3" />
      </div>
      <div className="flex items-center gap-2">
        <div className="h-4 bg-slate-200 rounded w-20" />
        <div className="h-8 bg-slate-200 rounded-lg w-24" />
      </div>
    </div>
  );
}

/**
 * Skeleton for job posts list
 */
export function JobListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {Array.from({ length: count }).map((_, i) => (
        <JobCardSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * Skeleton for evaluation result card
 */
export function EvaluationResultSkeleton() {
  return (
    <div className="bg-white rounded-3xl border border-slate-200 shadow-sm p-8 animate-pulse">
      <div className="flex flex-col lg:flex-row gap-8 items-center mb-8">
        <div className="h-40 w-40 bg-slate-200 rounded-3xl" />
        <div className="flex-1 space-y-3">
          <div className="h-4 bg-slate-200 rounded w-32" />
          <div className="h-6 bg-slate-200 rounded w-full" />
          <div className="h-6 bg-slate-200 rounded w-full" />
          <div className="h-6 bg-slate-200 rounded w-3/4" />
        </div>
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="h-32 bg-slate-200 rounded-2xl" />
        ))}
      </div>
    </div>
  );
}

/**
 * Skeleton for interview question item
 */
export function InterviewQuestionSkeleton() {
  return (
    <div className="p-4 bg-white rounded-lg border border-slate-100 animate-pulse">
      <div className="flex items-start gap-3">
        <div className="h-8 w-8 bg-slate-200 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="h-4 bg-slate-200 rounded w-full" />
          <div className="h-4 bg-slate-200 rounded w-3/4" />
        </div>
        <div className="h-6 w-16 bg-slate-200 rounded" />
      </div>
    </div>
  );
}

/**
 * Skeleton for interview questions list
 */
export function InterviewQuestionsSkeleton({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <InterviewQuestionSkeleton key={i} />
      ))}
    </div>
  );
}

/**
 * Combined loading state for candidates page
 */
export function CandidatesPageSkeleton() {
  return (
    <div className="p-8 space-y-8">
      <StatsGridSkeleton />
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-200 flex items-center justify-between">
          <div className="h-10 bg-slate-200 rounded-lg w-32 animate-pulse" />
          <div className="h-10 bg-slate-200 rounded-lg w-24 animate-pulse" />
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <CandidateTableSkeleton count={5} />
          </table>
        </div>
      </div>
    </div>
  );
}

/**
 * Loading spinner with backdrop
 */
export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className="flex items-center justify-center">
      <svg
        className={`animate-spin ${sizeClasses[size]} text-primary`}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        />
      </svg>
    </div>
  );
}

/**
 * Full page loading overlay
 */
export function FullPageLoading({ message = 'Loading...' }: { message?: string }) {
  return (
    <div className="fixed inset-0 bg-white/80 backdrop-blur-sm flex items-center justify-center z-50">
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <p className="mt-4 text-slate-600 font-medium">{message}</p>
      </div>
    </div>
  );
}
