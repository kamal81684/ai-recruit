"use client";

import { useState, useEffect } from "react";

interface Candidate {
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
  location?: string;
  skills?: string;
  education?: string;
  experience_years?: number;
  current_role?: string;
  created_at: string;
}

interface Statistics {
  total_candidates: number;
  by_tier: Record<string, number>;
  average_scores: {
    exact_match: number;
    similarity_match: number;
    achievement_impact: number;
    ownership: number;
  };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function CandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchCandidates();
    fetchStatistics();
  }, []);

  // Debug log when candidates state changes
  useEffect(() => {
    console.log("Candidates state updated:", candidates);
    if (candidates.length > 0) {
      console.log("First candidate in state:", candidates[0]);
    }
  }, [candidates]);

  const fetchCandidates = async () => {
    try {
      console.log("🔍 Fetching from:", `${API_URL}/api/candidates`);
      const response = await fetch(`${API_URL}/api/candidates`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        }
      });

      console.log("🔍 Response status:", response.status);
      console.log("🔍 Response headers:", Object.fromEntries(response.headers.entries()));

      if (!response.ok) throw new Error("Failed to fetch candidates");

      // Clone response to read it multiple times
      const clonedResponse = response.clone();
      const textData = await clonedResponse.text();
      console.log("🔍 Raw response text:", textData);
      console.log("🔍 Response text length:", textData.length);

      const data = await response.json();
      console.log("🔍 Parsed JSON:", data);
      console.log("🔍 Candidates array:", data.candidates);
      console.log("🔍 Type of candidates:", typeof data.candidates);
      console.log("🔍 Is candidates an array?", Array.isArray(data.candidates));

      if (data.candidates && data.candidates.length > 0) {
        console.log("🔍 First candidate keys:", Object.keys(data.candidates[0]));
        console.log("🔍 First candidate:", data.candidates[0]);
      }

      const candidatesData = data.candidates || [];
      setCandidates(candidatesData);
    } catch (err) {
      console.error("❌ Error fetching candidates:", err);
      setError(err instanceof Error ? err.message : "Failed to load candidates");
    } finally {
      setLoading(false);
    }
  };

  const fetchStatistics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/statistics`, {
        cache: 'no-store',
        headers: {
          'Cache-Control': 'no-cache',
        }
      });
      if (!response.ok) throw new Error("Failed to fetch statistics");
      const data = await response.json();
      console.log("Fetched statistics:", data);
      setStatistics(data);
    } catch (err) {
      console.error("Failed to load statistics:", err);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Tier A":
        return "bg-emerald-100 text-emerald-800";
      case "Tier B":
        return "bg-blue-100 text-blue-800";
      case "Tier C":
        return "bg-slate-100 text-slate-800";
      default:
        return "bg-slate-100 text-slate-800";
    }
  };

  const getAverageScore = (candidate: Candidate) => {
    const scores = [
      candidate.exact_match_score,
      candidate.similarity_match_score,
      candidate.achievement_impact_score,
      candidate.ownership_score
    ].filter(s => s != null && !isNaN(s));

    if (scores.length === 0) return 0;
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar Navigation */}
      <aside className="w-64 border-r border-slate-200 bg-white flex flex-col">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3">
            <div className="size-10 bg-primary rounded-lg flex items-center justify-center text-white">
              <span className="material-symbols-outlined">psychology</span>
            </div>
            <div>
              <h1 className="text-sm font-bold leading-tight">AI Recruit</h1>
              <p className="text-xs text-slate-500">Enterprise AI</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2">
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/">
            <span className="material-symbols-outlined text-slate-400">dashboard</span>
            Dashboard
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg bg-primary/10 text-primary" href="/candidates">
            <span className="material-symbols-outlined">group</span>
            Candidates
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="#">
            <span className="material-symbols-outlined text-slate-400">work</span>
            Jobs
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="#">
            <span className="material-symbols-outlined text-slate-400">bar_chart</span>
            Analytics
          </a>
        </nav>
        <div className="p-4 border-t border-slate-200">
          <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-slate-100 cursor-pointer transition-colors">
            <div className="size-8 rounded-full bg-slate-200"></div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-semibold truncate">Hiring Manager</p>
              <p className="text-[10px] text-slate-500 truncate">Recruiting Team</p>
            </div>
            <span className="material-symbols-outlined text-slate-400 text-sm">settings</span>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        {/* Header */}
        <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex items-center gap-4 flex-1">
            <div className="relative w-full max-w-md">
              <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-lg">search</span>
              <input
                className="w-full pl-10 pr-4 py-2 text-sm bg-slate-100 border-none rounded-lg focus:ring-2 focus:ring-primary/20 placeholder:text-slate-500"
                placeholder="Search candidates, roles, or skills..."
                type="text"
              />
            </div>
          </div>
          <div className="flex items-center gap-4">
            <button className="size-10 flex items-center justify-center rounded-lg hover:bg-slate-100 text-slate-600 transition-colors">
              <span className="material-symbols-outlined">notifications</span>
            </button>
            <a
              href="/"
              className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              New Candidate
            </a>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {/* Top-level Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500 text-sm font-medium">Total Applicants</span>
                <span className="material-symbols-outlined text-primary bg-primary/10 p-1.5 rounded-lg text-lg">group</span>
              </div>
              <div className="flex items-end gap-2">
                <h3 className="text-3xl font-bold">{statistics?.total_candidates || 0}</h3>
              </div>
              <p className="text-xs text-slate-400 mt-2">All time candidates</p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500 text-sm font-medium">Tier A Matches</span>
                <span className="material-symbols-outlined text-amber-500 bg-amber-500/10 p-1.5 rounded-lg text-lg">verified</span>
              </div>
              <div className="flex items-end gap-2">
                <h3 className="text-3xl font-bold">{statistics?.by_tier?.["Tier A"] || 0}</h3>
              </div>
              <p className="text-xs text-slate-400 mt-2">Top tier candidates</p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500 text-sm font-medium">Avg Match Score</span>
                <span className="material-symbols-outlined text-indigo-500 bg-indigo-500/10 p-1.5 rounded-lg text-lg">query_stats</span>
              </div>
              <div className="flex items-end gap-2">
                <h3 className="text-3xl font-bold">
                  {statistics?.average_scores
                    ? (() => {
                        const scores = [
                          statistics.average_scores.exact_match,
                          statistics.average_scores.similarity_match,
                          statistics.average_scores.achievement_impact,
                          statistics.average_scores.ownership
                        ].filter(s => s != null && !isNaN(s));
                        return scores.length > 0 ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
                      })()
                    : 0}
                  %
                </h3>
              </div>
              <p className="text-xs text-slate-400 mt-2">System-wide performance</p>
            </div>

            <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <span className="text-slate-500 text-sm font-medium">Tier B Candidates</span>
                <span className="material-symbols-outlined text-blue-500 bg-blue-500/10 p-1.5 rounded-lg text-lg">person</span>
              </div>
              <div className="flex items-end gap-2">
                <h3 className="text-3xl font-bold">{statistics?.by_tier?.["Tier B"] || 0}</h3>
              </div>
              <p className="text-xs text-slate-400 mt-2">Good matches</p>
            </div>
          </div>

          {/* Candidate Queue Table */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200 flex items-center justify-between">
              <h2 className="text-lg font-bold">Candidate Queue</h2>
              <div className="flex items-center gap-2">
                <button className="px-3 py-1.5 text-xs font-semibold border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors">
                  Filter
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="px-3 py-1.5 text-xs font-semibold border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
                >
                  Refresh
                </button>
              </div>
            </div>

            {loading ? (
              <div className="p-12 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-slate-500">Loading candidates...</p>
              </div>
            ) : error ? (
              <div className="p-12 text-center">
                <span className="material-symbols-outlined text-4xl text-slate-300">error</span>
                <p className="mt-4 text-slate-500">{error}</p>
                <button
                  onClick={fetchCandidates}
                  className="mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                  Retry
                </button>
              </div>
            ) : candidates.length === 0 ? (
              <div className="p-12 text-center">
                <span className="material-symbols-outlined text-4xl text-slate-300">group_off</span>
                <p className="mt-4 text-slate-500">No candidates yet</p>
                <a
                  href="/"
                  className="inline-block mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                  Add First Candidate
                </a>
              </div>
            ) : (
              <>
                <div className="overflow-x-auto">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Name</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Role</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Location</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Tier</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Match Score</th>
                        <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {candidates.map((candidate) => {
                        console.log("Rendering candidate:", candidate);
                        return (
                        <tr key={candidate.id} className="hover:bg-slate-50 transition-colors">
                          <td className="px-6 py-4">
                            <div>
                              <p className="text-sm font-bold">{candidate.name || "Unknown"}</p>
                              {candidate.email && (
                                <p className="text-xs text-slate-500">{candidate.email}</p>
                              )}
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-sm font-medium text-slate-700">
                              {candidate.current_role || candidate.resume_filename}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className="text-sm text-slate-500">
                              {candidate.location || "N/A"}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${getTierColor(candidate.tier)}`}>
                              {candidate.tier}
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <div className="w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                <div className="h-full bg-primary" style={{ width: `${getAverageScore(candidate)}%` }}></div>
                              </div>
                              <span className="text-sm font-bold">{getAverageScore(candidate)}</span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <button
                              onClick={() => window.location.href = `/candidates/${candidate.id}`}
                              className="text-primary text-sm font-bold hover:underline"
                            >
                              View Profile
                            </button>
                          </td>
                        </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
                <div className="p-4 border-t border-slate-200 flex items-center justify-between">
                  <p className="text-xs text-slate-500">Showing {candidates.length} candidates</p>
                </div>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
