"use client";

import { useState, useEffect } from "react";

interface RankedCandidate {
  rank: number;
  id: number;
  name: string;
  email?: string;
  current_role?: string;
  location?: string;
  tier: string;
  overall_score: number;
  exact_match_score: number;
  similarity_match_score: number;
  achievement_impact_score: number;
  ownership_score: number;
  created_at?: string;
}

interface LeaderboardStats {
  overall_score: number;
  exact_match: number;
  similarity_match: number;
  achievement_impact: number;
  ownership: number;
}

interface CandidateLeaderboardProps {
  className?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function CandidateLeaderboard({ className = "" }: CandidateLeaderboardProps) {
  const [candidates, setCandidates] = useState<RankedCandidate[]>([]);
  const [stats, setStats] = useState<LeaderboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [sortBy, setSortBy] = useState("overall_score");
  const [order, setOrder] = useState("desc");
  const [tierFilter, setTierFilter] = useState("");

  useEffect(() => {
    fetchRankedCandidates();
  }, [sortBy, order, tierFilter]);

  const fetchRankedCandidates = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams({
        sort_by: sortBy,
        order: order,
        limit: "20",
      });
      if (tierFilter) params.append("tier", tierFilter);

      const response = await fetch(`${API_URL}/api/candidates/ranking?${params}`, {
        cache: 'no-store',
        headers: { 'Cache-Control': 'no-cache' }
      });

      if (!response.ok) throw new Error("Failed to fetch ranking");

      const data = await response.json();
      setCandidates(data.ranked_candidates || []);
      setStats(data.statistics || null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load ranking");
    } finally {
      setLoading(false);
    }
  };

  const getRankBadge = (rank: number) => {
    if (rank === 1) return { bg: "bg-yellow-100", text: "text-yellow-800", icon: "🥇" };
    if (rank === 2) return { bg: "bg-slate-200", text: "text-slate-800", icon: "🥈" };
    if (rank === 3) return { bg: "bg-amber-100", text: "text-amber-800", icon: "🥉" };
    return { bg: "bg-slate-100", text: "text-slate-600", icon: `#${rank}` };
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Tier A": return "bg-emerald-100 text-emerald-800";
      case "Tier B": return "bg-blue-100 text-blue-800";
      case "Tier C": return "bg-slate-100 text-slate-800";
      default: return "bg-slate-100 text-slate-800";
    }
  };

  return (
    <div className={`candidate-leaderboard ${className}`}>
      {/* Header with Controls */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <span className="material-symbols-outlined text-primary">leaderboard</span>
              Candidate Leaderboard
            </h2>
            <p className="text-sm text-slate-500 mt-1">Candidates ranked by match score</p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <select
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              <option value="">All Tiers</option>
              <option value="Tier A">Tier A</option>
              <option value="Tier B">Tier B</option>
              <option value="Tier C">Tier C</option>
            </select>

            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white focus:ring-2 focus:ring-primary/20 focus:border-primary"
            >
              <option value="overall_score">Overall Score</option>
              <option value="exact_match_score">Exact Match</option>
              <option value="similarity_match_score">Semantic Match</option>
              <option value="achievement_impact_score">Achievement</option>
              <option value="ownership_score">Ownership</option>
            </select>

            <button
              onClick={() => setOrder(order === "desc" ? "asc" : "desc")}
              className="px-3 py-2 text-sm border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors flex items-center gap-1"
            >
              <span className="material-symbols-outlined text-sm">
                {order === "desc" ? "arrow_downward" : "arrow_upward"}
              </span>
              {order === "desc" ? "Highest" : "Lowest"}
            </button>
          </div>
        </div>

        {/* Stats Summary */}
        {stats && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-6 pt-6 border-t border-slate-100">
            <div className="text-center">
              <p className="text-2xl font-bold text-primary">{stats.overall_score}</p>
              <p className="text-xs text-slate-500">Avg Overall</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-600">{stats.exact_match}</p>
              <p className="text-xs text-slate-500">Avg Exact</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-purple-600">{stats.similarity_match}</p>
              <p className="text-xs text-slate-500">Avg Semantic</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-emerald-600">{stats.achievement_impact}</p>
              <p className="text-xs text-slate-500">Avg Impact</p>
            </div>
            <div className="text-center">
              <p className="text-2xl font-bold text-amber-600">{stats.ownership}</p>
              <p className="text-xs text-slate-500">Avg Ownership</p>
            </div>
          </div>
        )}
      </div>

      {/* Leaderboard List */}
      {loading ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-slate-500">Loading leaderboard...</p>
        </div>
      ) : error ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 text-center">
          <span className="material-symbols-outlined text-4xl text-slate-300">error</span>
          <p className="mt-4 text-slate-500">{error}</p>
          <button
            onClick={fetchRankedCandidates}
            className="mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary/90"
          >
            Retry
          </button>
        </div>
      ) : candidates.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 text-center">
          <span className="material-symbols-outlined text-4xl text-slate-300">leaderboard</span>
          <p className="mt-4 text-slate-500">No candidates to rank</p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Rank</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Candidate</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Tier</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Overall</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider">Scores</th>
                  <th className="px-6 py-4 text-xs font-bold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {candidates.map((candidate) => {
                  const badge = getRankBadge(candidate.rank);
                  return (
                    <tr
                      key={candidate.id}
                      className={`hover:bg-slate-50 transition-colors ${candidate.rank <= 3 ? "bg-primary/5" : ""}`}
                    >
                      <td className="px-6 py-4">
                        <div className={`flex items-center justify-center w-10 h-10 rounded-lg ${badge.bg} ${badge.text} font-bold text-lg`}>
                          {badge.icon}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <p className="text-sm font-bold text-slate-900">{candidate.name}</p>
                          {candidate.current_role && (
                            <p className="text-xs text-slate-500">{candidate.current_role}</p>
                          )}
                          {candidate.location && (
                            <p className="text-xs text-slate-400 flex items-center gap-1 mt-1">
                              <span className="material-symbols-outlined text-[12px]">location_on</span>
                              {candidate.location}
                            </p>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${getTierColor(candidate.tier)}`}>
                          {candidate.tier}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-2 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-primary to-blue-500"
                              style={{ width: `${candidate.overall_score}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-bold text-slate-900">{candidate.overall_score}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2 text-xs">
                          <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded font-medium">
                            E: {candidate.exact_match_score}
                          </span>
                          <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded font-medium">
                            S: {candidate.similarity_match_score}
                          </span>
                          <span className="px-2 py-1 bg-emerald-100 text-emerald-700 rounded font-medium">
                            A: {candidate.achievement_impact_score}
                          </span>
                          <span className="px-2 py-1 bg-amber-100 text-amber-700 rounded font-medium">
                            O: {candidate.ownership_score}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => window.location.href = `/candidates/${candidate.id}`}
                          className="text-primary text-sm font-bold hover:underline"
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
          <div className="p-4 border-t border-slate-200 bg-slate-50">
            <p className="text-xs text-slate-500 text-center">
              Showing top {candidates.length} candidates sorted by {sortBy.replace('_', ' ')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
