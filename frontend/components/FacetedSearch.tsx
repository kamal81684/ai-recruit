/**
 * Faceted Search Component for Candidates
 *
 * Provides advanced filtering and search capabilities with:
 * - Multiple filter categories (tier, location, skills, experience)
 * - URL query parameter management for bookmarkable searches
 * - Real-time filter updates
 * - Clear filters functionality
 *
 * Contributor: shubham21155102 - Advanced Search UX
 */

"use client";

import React, { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams, usePathname } from 'next/navigation';

interface FacetedSearchProps {
  onFiltersChange?: (filters: CandidateFilters) => void;
  availableTiers?: string[];
  availableLocations?: string[];
  availableSkills?: string[];
}

export interface CandidateFilters {
  search: string;
  tier: string[];
  location: string[];
  skills: string[];
  minExperience: number | null;
  maxExperience: number | null;
  sortBy: 'recent' | 'score_desc' | 'score_asc' | 'name_asc';
}

const DEFAULT_FILTERS: CandidateFilters = {
  search: '',
  tier: [],
  location: [],
  skills: [],
  minExperience: null,
  maxExperience: null,
  sortBy: 'recent'
};

const EXPERIENCE_RANGES = [
  { label: '0-1 years', min: 0, max: 1 },
  { label: '1-3 years', min: 1, max: 3 },
  { label: '3-5 years', min: 3, max: 5 },
  { label: '5-10 years', min: 5, max: 10 },
  { label: '10+ years', min: 10, max: null },
];

const COMMON_SKILLS = [
  'Python', 'JavaScript', 'TypeScript', 'React', 'Node.js', 'Java',
  'SQL', 'AWS', 'Docker', 'Kubernetes', 'Machine Learning', 'Data Science',
  'Project Management', 'Agile', 'DevOps', 'CI/CD', 'Git', 'REST API'
];

export function FacetedSearch({
  onFiltersChange,
  availableTiers = ['Tier A', 'Tier B', 'Tier C'],
  availableLocations = [],
  availableSkills = COMMON_SKILLS
}: FacetedSearchProps) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const pathname = usePathname();

  // Initialize filters from URL params
  const [filters, setFilters] = useState<CandidateFilters>(() => {
    const params: CandidateFilters = { ...DEFAULT_FILTERS };

    params.search = searchParams.get('search') || '';
    params.sortBy = (searchParams.get('sortBy') as CandidateFilters['sortBy']) || 'recent';

    const tierParam = searchParams.get('tier');
    if (tierParam) params.tier = tierParam.split(',');

    const locationParam = searchParams.get('location');
    if (locationParam) params.location = locationParam.split(',');

    const skillsParam = searchParams.get('skills');
    if (skillsParam) params.skills = skillsParam.split(',');

    const minExp = searchParams.get('minExperience');
    if (minExp) params.minExperience = parseInt(minExp);

    const maxExp = searchParams.get('maxExperience');
    if (maxExp) params.maxExperience = parseInt(maxExp);

    return params;
  });

  const [isExpanded, setIsExpanded] = useState(false);
  const [customSkill, setCustomSkill] = useState('');

  // Update URL params when filters change
  const updateURL = useCallback((newFilters: CandidateFilters) => {
    const params = new URLSearchParams();

    if (newFilters.search) params.set('search', newFilters.search);
    if (newFilters.tier.length > 0) params.set('tier', newFilters.tier.join(','));
    if (newFilters.location.length > 0) params.set('location', newFilters.location.join(','));
    if (newFilters.skills.length > 0) params.set('skills', newFilters.skills.join(','));
    if (newFilters.minExperience !== null) params.set('minExperience', newFilters.minExperience.toString());
    if (newFilters.maxExperience !== null) params.set('maxExperience', newFilters.maxExperience.toString());
    if (newFilters.sortBy !== 'recent') params.set('sortBy', newFilters.sortBy);

    const queryString = params.toString();
    const url = queryString ? `${pathname}?${queryString}` : pathname;
    router.push(url, { scroll: false });
  }, [pathname, router]);

  // Handle filter changes
  const updateFilter = useCallback(<K extends keyof CandidateFilters>(
    key: K,
    value: CandidateFilters[K]
  ) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    updateURL(newFilters);
    onFiltersChange?.(newFilters);
  }, [filters, updateURL, onFiltersChange]);

  // Toggle array filter (tier, location, skills)
  const toggleArrayFilter = useCallback((
    key: 'tier' | 'location' | 'skills',
    value: string
  ) => {
    const currentArray = filters[key];
    const newArray = currentArray.includes(value)
      ? currentArray.filter(item => item !== value)
      : [...currentArray, value];
    updateFilter(key, newArray);
  }, [filters, updateFilter]);

  // Clear all filters
  const clearFilters = useCallback(() => {
    const clearedFilters: CandidateFilters = {
      ...DEFAULT_FILTERS,
      search: filters.search, // Keep search term
      sortBy: filters.sortBy // Keep sort order
    };
    setFilters(clearedFilters);
    updateURL(clearedFilters);
    onFiltersChange?.(clearedFilters);
  }, [filters.search, filters.sortBy, updateURL, onFiltersChange]);

  // Add custom skill
  const addCustomSkill = useCallback(() => {
    if (customSkill.trim() && !filters.skills.includes(customSkill.trim())) {
      toggleArrayFilter('skills', customSkill.trim());
      setCustomSkill('');
    }
  }, [customSkill, filters.skills, toggleArrayFilter]);

  // Get active filter count
  const activeFilterCount = (
    filters.tier.length +
    filters.location.length +
    filters.skills.length +
    (filters.minExperience !== null ? 1 : 0) +
    (filters.maxExperience !== null ? 1 : 0)
  );

  // Check if any filters are active
  const hasActiveFilters = activeFilterCount > 0;

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Search and Toggle Header */}
      <div className="p-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <div className="relative flex-1">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400">
              search
            </span>
            <input
              type="text"
              value={filters.search}
              onChange={(e) => updateFilter('search', e.target.value)}
              placeholder="Search candidates by name, role, or skills..."
              className="w-full pl-10 pr-4 py-2 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
            />
          </div>
          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold rounded-lg transition-colors relative ${
              hasActiveFilters
                ? 'bg-primary text-white'
                : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}
          >
            <span className="material-symbols-outlined text-lg">tune</span>
            Filters
            {hasActiveFilters && (
              <span className="absolute -top-1 -right-1 h-5 w-5 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">
                {activeFilterCount}
              </span>
            )}
          </button>
        </div>
      </div>

      {/* Expandable Filters */}
      {isExpanded && (
        <div className="p-4 space-y-4 border-b border-slate-100">
          {/* Tier Filters */}
          <div>
            <h4 className="text-sm font-bold text-slate-700 mb-2">Candidate Tier</h4>
            <div className="flex flex-wrap gap-2">
              {availableTiers.map((tier) => (
                <button
                  key={tier}
                  onClick={() => toggleArrayFilter('tier', tier)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-colors ${
                    filters.tier.includes(tier)
                      ? 'bg-primary text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {tier}
                </button>
              ))}
            </div>
          </div>

          {/* Experience Level Filters */}
          <div>
            <h4 className="text-sm font-bold text-slate-700 mb-2">Experience Level</h4>
            <div className="flex flex-wrap gap-2">
              {EXPERIENCE_RANGES.map((range) => (
                <button
                  key={range.label}
                  onClick={() => {
                    updateFilter('minExperience', range.min);
                    updateFilter('maxExperience', range.max);
                  }}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-colors ${
                    filters.minExperience === range.min &&
                    filters.maxExperience === range.max
                      ? 'bg-primary text-white'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {range.label}
                </button>
              ))}
            </div>
          </div>

          {/* Skills Filters */}
          <div>
            <h4 className="text-sm font-bold text-slate-700 mb-2">Skills</h4>
            <div className="flex flex-wrap gap-2 mb-2">
              {availableSkills.map((skill) => (
                <button
                  key={skill}
                  onClick={() => toggleArrayFilter('skills', skill)}
                  className={`px-3 py-1.5 text-xs font-semibold rounded-full transition-colors ${
                    filters.skills.includes(skill)
                      ? 'bg-blue-100 text-blue-700 border border-blue-200'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {skill}
                </button>
              ))}
            </div>
            {/* Add custom skill */}
            <div className="flex gap-2">
              <input
                type="text"
                value={customSkill}
                onChange={(e) => setCustomSkill(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && addCustomSkill()}
                placeholder="Add custom skill..."
                className="flex-1 px-3 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
              />
              <button
                onClick={addCustomSkill}
                className="px-3 py-1.5 bg-slate-100 text-slate-600 text-sm font-semibold rounded-lg hover:bg-slate-200 transition-colors"
              >
                Add
              </button>
            </div>
          </div>

          {/* Active Filters Display */}
          {hasActiveFilters && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm font-bold text-slate-700">Active Filters</h4>
                <button
                  onClick={clearFilters}
                  className="text-xs font-semibold text-red-600 hover:text-red-700 transition-colors"
                >
                  Clear All
                </button>
              </div>
              <div className="flex flex-wrap gap-2">
                {filters.tier.map((tier) => (
                  <span
                    key={tier}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-primary/10 text-primary text-xs font-semibold rounded-full"
                  >
                    {tier}
                    <button
                      onClick={() => toggleArrayFilter('tier', tier)}
                      className="material-symbols-outlined text-[14px] hover:text-red-500"
                    >
                      close
                    </button>
                  </span>
                ))}
                {filters.skills.map((skill) => (
                  <span
                    key={skill}
                    className="inline-flex items-center gap-1 px-2 py-1 bg-blue-50 text-blue-600 text-xs font-semibold rounded-full"
                  >
                    {skill}
                    <button
                      onClick={() => toggleArrayFilter('skills', skill)}
                      className="material-symbols-outlined text-[14px] hover:text-red-500"
                    >
                      close
                    </button>
                  </span>
                ))}
                {filters.minExperience !== null && (
                  <span className="inline-flex items-center gap-1 px-2 py-1 bg-purple-50 text-purple-600 text-xs font-semibold rounded-full">
                    {EXPERIENCE_RANGES.find(r => r.min === filters.minExperience)?.label}
                    <button
                      onClick={() => {
                        updateFilter('minExperience', null);
                        updateFilter('maxExperience', null);
                      }}
                      className="material-symbols-outlined text-[14px] hover:text-red-500"
                    >
                      close
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Sort Options */}
      <div className="p-4 flex items-center justify-between">
        <span className="text-sm text-slate-500">
          Sort by:
        </span>
        <select
          value={filters.sortBy}
          onChange={(e) => updateFilter('sortBy', e.target.value as CandidateFilters['sortBy'])}
          className="px-3 py-1.5 text-sm bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none cursor-pointer"
        >
          <option value="recent">Most Recent</option>
          <option value="score_desc">Highest Score</option>
          <option value="score_asc">Lowest Score</option>
          <option value="name_asc">Name (A-Z)</option>
        </select>
      </div>
    </div>
  );
}

/**
 * Quick action row component for candidate list
 * Provides inline actions without opening profile
 */
export function CandidateQuickActions({
  candidateId,
  candidateName,
  onStatusChange,
  onDelete
}: {
  candidateId: number;
  candidateName: string;
  onStatusChange?: (id: number, status: string) => void;
  onDelete?: (id: number) => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  const handleAction = (action: string) => {
    switch (action) {
      case 'interview':
        onStatusChange?.(candidateId, 'interview_scheduled');
        break;
      case 'shortlist':
        onStatusChange?.(candidateId, 'shortlisted');
        break;
      case 'reject':
        onStatusChange?.(candidateId, 'rejected');
        break;
      case 'delete':
        if (confirm(`Are you sure you want to delete ${candidateName}?`)) {
          onDelete?.(candidateId);
        }
        break;
    }
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="p-1.5 hover:bg-slate-100 rounded transition-colors"
      >
        <span className="material-symbols-outlined text-slate-400">more_vert</span>
      </button>
      {isOpen && (
        <>
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />
          <div className="absolute right-0 top-full mt-1 w-48 bg-white rounded-lg shadow-xl border border-slate-200 z-20 py-1">
            <button
              onClick={() => handleAction('shortlist')}
              className="w-full px-4 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px] text-blue-500">star</span>
              Shortlist
            </button>
            <button
              onClick={() => handleAction('interview')}
              className="w-full px-4 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px] text-green-500">event</span>
              Schedule Interview
            </button>
            <button
              onClick={() => handleAction('reject')}
              className="w-full px-4 py-2 text-left text-sm font-medium text-slate-700 hover:bg-slate-50 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px] text-red-500">cancel</span>
              Reject
            </button>
            <hr className="my-1 border-slate-100" />
            <button
              onClick={() => handleAction('delete')}
              className="w-full px-4 py-2 text-left text-sm font-medium text-red-600 hover:bg-red-50 flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-[18px]">delete</span>
              Delete
            </button>
          </div>
        </>
      )}
    </div>
  );
}
