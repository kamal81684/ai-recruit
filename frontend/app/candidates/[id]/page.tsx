"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";

interface Candidate {
  id: number;
  name: string;
  email: string;
  phone: string;
  resume_filename: string;
  resume_text: string;
  job_description: string;
  tier: string;
  summary: string;
  exact_match_score: number;
  exact_match_explanation: string;
  similarity_match_score: number;
  similarity_match_explanation: string;
  achievement_impact_score: number;
  achievement_impact_explanation: string;
  ownership_score: number;
  ownership_explanation: string;
  location?: string;
  skills?: string;
  education?: string;
  experience_years?: number;
  current_role?: string;
  created_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function CandidateProfilePage() {
  const params = useParams();
  const candidateId = params.id;
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    if (candidateId) {
      fetchCandidate();
    }
  }, [candidateId]);

  const fetchCandidate = async () => {
    try {
      const response = await fetch(`${API_URL}/api/candidates/${candidateId}`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        }
      });
      if (!response.ok) throw new Error("Failed to fetch candidate");
      const data = await response.json();
      console.log("Fetched candidate:", data);
      setCandidate(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load candidate");
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Tier A":
        return "text-green-600 border-green-200 bg-green-50";
      case "Tier B":
        return "text-orange-600 border-orange-200 bg-orange-50";
      case "Tier C":
        return "text-red-600 border-red-200 bg-red-50";
      default:
        return "text-gray-600 border-gray-200 bg-gray-50";
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
          <p className="mt-4 text-slate-500">Loading candidate profile...</p>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-center">
          <span className="material-symbols-outlined text-6xl text-slate-300">error</span>
          <p className="mt-4 text-slate-500">{error || "Candidate not found"}</p>
          <a
            href="/candidates"
            className="inline-block mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors"
          >
            Back to Candidates
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      {/* Left Sidebar */}
      <aside className="w-full lg:w-80 border-r border-slate-200 bg-white p-6 flex flex-col gap-8 lg:h-screen lg:sticky lg:top-0">
        <div className="flex flex-col items-center text-center gap-4">
          <div className="relative">
            <div className="size-32 rounded-2xl bg-slate-200 flex items-center justify-center">
              <span className="material-symbols-outlined text-6xl text-slate-400">person</span>
            </div>
            <div className="absolute -bottom-2 -right-2 bg-green-500 size-6 rounded-full border-4 border-white" title="Available now"></div>
          </div>
          <div className="space-y-1">
            <h1 className="text-2xl font-bold text-slate-900">{candidate.name || "Unknown Candidate"}</h1>
            {candidate.current_role && (
              <p className="text-primary font-semibold text-sm uppercase tracking-wider">{candidate.current_role}</p>
            )}
            {!candidate.current_role && (
              <p className="text-primary font-semibold text-sm uppercase tracking-wider">Candidate</p>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center gap-3 px-4 py-3 rounded-xl bg-primary text-white shadow-lg shadow-primary/20">
            <span className="material-symbols-outlined">analytics</span>
            <p className="text-sm font-semibold">AI Insights</p>
          </div>
          <div className="flex items-center gap-3 px-4 py-3 text-slate-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer">
            <span className="material-symbols-outlined">description</span>
            <p className="text-sm font-medium">Resume</p>
          </div>
        </div>

        <div className="mt-auto pt-6 border-t border-slate-100 space-y-4">
          {candidate.email && (
            <div className="flex items-center gap-3 text-slate-500 text-sm">
              <span className="material-symbols-outlined text-lg">mail</span>
              <span className="truncate">{candidate.email}</span>
            </div>
          )}
          {candidate.phone && (
            <div className="flex items-center gap-3 text-slate-500 text-sm">
              <span className="material-symbols-outlined text-lg">phone</span>
              <span>{candidate.phone}</span>
            </div>
          )}
          <div className="flex items-center gap-3 text-slate-500 text-sm">
            <span className="material-symbols-outlined text-lg">schedule</span>
            <span>{new Date(candidate.created_at).toLocaleDateString()}</span>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 overflow-y-auto p-6 lg:p-10 space-y-10">
        {/* Breadcrumbs & Header */}
        <div className="space-y-2">
          <nav className="flex items-center gap-2 text-sm font-medium text-slate-500">
            <a className="hover:text-primary transition-colors" href="/candidates">Candidates</a>
            <span className="material-symbols-outlined text-xs">chevron_right</span>
            <span className="text-slate-900 font-semibold">{candidate.name || "Unknown Candidate"}</span>
          </nav>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
            <div>
              <h2 className="text-3xl lg:text-4xl font-black text-slate-900 tracking-tight">Candidate Profile Deep-Dive</h2>
              <p className="text-slate-500 mt-2 text-lg">Detailed AI assessment and role compatibility analysis.</p>
            </div>
            <div className={`flex items-center gap-2 px-4 py-2 rounded-lg border font-bold text-sm ${getTierColor(candidate.tier)}`}>
              <span className="material-symbols-outlined text-lg">verified</span>
              {candidate.tier}
            </div>
          </div>
        </div>

        {/* Executive Summary */}
        <section className="bg-slate-50 rounded-2xl p-8 border border-slate-100">
          <div className="flex items-center gap-3 mb-4">
            <span className="material-symbols-outlined text-primary text-2xl">summarize</span>
            <h3 className="text-xl font-bold text-slate-900">Executive Summary</h3>
          </div>
          <p className="text-slate-700 leading-relaxed">{candidate.summary}</p>
        </section>

        {/* Multi-dimensional AI Scores */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
            <span className="material-symbols-outlined text-primary font-bold">query_stats</span>
            <h3 className="text-xl font-bold text-slate-900">Multi-dimensional AI Scores</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {/* Exact Match */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Exact Match</span>
                <span className="text-2xl font-black text-primary">{candidate.exact_match_score}%</span>
              </div>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: `${candidate.exact_match_score}%` }}></div>
              </div>
              <p className="mt-4 text-sm text-slate-500">{candidate.exact_match_explanation}</p>
            </div>

            {/* Semantic Similarity */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Semantic Similarity</span>
                <span className="text-2xl font-black text-primary">{candidate.similarity_match_score}%</span>
              </div>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: `${candidate.similarity_match_score}%` }}></div>
              </div>
              <p className="mt-4 text-sm text-slate-500">{candidate.similarity_match_explanation}</p>
            </div>

            {/* Achievement Score */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Achievement Score</span>
                <span className="text-2xl font-black text-primary">{candidate.achievement_impact_score}%</span>
              </div>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: `${candidate.achievement_impact_score}%` }}></div>
              </div>
              <p className="mt-4 text-sm text-slate-500">{candidate.achievement_impact_explanation}</p>
            </div>

            {/* Ownership */}
            <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Ownership</span>
                <span className="text-2xl font-black text-primary">{candidate.ownership_score}%</span>
              </div>
              <div className="h-3 w-full bg-slate-100 rounded-full overflow-hidden">
                <div className="h-full bg-primary rounded-full" style={{ width: `${candidate.ownership_score}%` }}></div>
              </div>
              <p className="mt-4 text-sm text-slate-500">{candidate.ownership_explanation}</p>
            </div>
          </div>
        </section>

        {/* Resume Preview */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
            <span className="material-symbols-outlined text-primary font-bold">description</span>
            <h3 className="text-xl font-bold text-slate-900">Resume</h3>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-100">
            <p className="text-sm text-slate-500 mb-4"><strong>File:</strong> {candidate.resume_filename}</p>
            <div className="bg-slate-50 rounded-xl p-6 max-h-96 overflow-y-auto">
              <pre className="text-sm text-slate-700 whitespace-pre-wrap font-sans">{candidate.resume_text}</pre>
            </div>
          </div>
        </section>

        {/* Job Description */}
        <section className="space-y-6">
          <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
            <span className="material-symbols-outlined text-primary font-bold">work</span>
            <h3 className="text-xl font-bold text-slate-900">Job Description</h3>
          </div>
          <div className="bg-white rounded-2xl p-6 border border-slate-100">
            <div className="bg-slate-50 rounded-xl p-6 max-h-96 overflow-y-auto">
              <p className="text-sm text-slate-700 whitespace-pre-wrap">{candidate.job_description}</p>
            </div>
          </div>
        </section>

        {/* Extracted Information */}
        {(candidate.skills || candidate.education || candidate.experience_years || candidate.location) && (
          <section className="space-y-6">
            <div className="flex items-center gap-3 border-b border-slate-200 pb-4">
              <span className="material-symbols-outlined text-primary font-bold">badge</span>
              <h3 className="text-xl font-bold text-slate-900">Candidate Information</h3>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {candidate.location && (
                <div className="bg-white rounded-2xl p-6 border border-slate-100">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="material-symbols-outlined text-primary">location_on</span>
                    <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Location</span>
                  </div>
                  <p className="text-slate-900 font-medium">{candidate.location}</p>
                </div>
              )}
              {candidate.experience_years && (
                <div className="bg-white rounded-2xl p-6 border border-slate-100">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="material-symbols-outlined text-primary">work_history</span>
                    <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Experience</span>
                  </div>
                  <p className="text-slate-900 font-medium">{candidate.experience_years} years</p>
                </div>
              )}
              {candidate.skills && (
                <div className="bg-white rounded-2xl p-6 border border-slate-100 md:col-span-2">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="material-symbols-outlined text-primary">psychology</span>
                    <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Skills</span>
                  </div>
                  <p className="text-slate-900 font-medium">{candidate.skills}</p>
                </div>
              )}
              {candidate.education && (
                <div className="bg-white rounded-2xl p-6 border border-slate-100 md:col-span-2">
                  <div className="flex items-center gap-3 mb-3">
                    <span className="material-symbols-outlined text-primary">school</span>
                    <span className="text-sm font-bold text-slate-500 uppercase tracking-wider">Education</span>
                  </div>
                  <p className="text-slate-900 font-medium">{candidate.education}</p>
                </div>
              )}
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
