"use client";

import { useState, useEffect } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

interface AnalyticsData {
  total_candidates: number;
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
  recent_candidates: Array<{
    id: number;
    name: string;
    email: string;
    tier: string;
    created_at: string;
  }>;
}
export default function DashboardPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`${API_URL}/api/analytics`);
      if (!response.ok) throw new Error("Failed to fetch analytics");
      const data = await response.json();
      setAnalytics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  const getTierColor = (tier: string) => {
    switch (tier) {
      case "Tier A": return "text-emerald-600 bg-emerald-50 border-emerald-200";
      case "Tier B": return "text-orange-600 bg-orange-50 border-orange-200";
      case "Tier C": return "text-red-600 bg-red-50 border-red-200";
      default: return "text-slate-600 bg-slate-50 border-slate-200";
    }
  };

  const getTierBarColor = (tier: string) => {
    switch (tier) {
      case "Tier A": return "bg-emerald-500";
      case "Tier B": return "bg-orange-500";
      case "Tier C": return "bg-red-500";
      default: return "bg-slate-500";
    }
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
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg bg-primary/10 text-primary" href="/dashboard">
            <span className="material-symbols-outlined">dashboard</span>
            Dashboard
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/candidates">
            <span className="material-symbols-outlined text-slate-400">group</span>
            Candidates
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/jobs">
            <span className="material-symbols-outlined text-slate-400">work</span>
            Jobs
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/analytics">
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
          <h1 className="text-xl font-bold text-slate-900">Dashboard</h1>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchAnalytics}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
              Refresh
            </button>
            <a
              href="/"
              className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
            >
              <span className="material-symbols-outlined text-sm">add</span>
              Add Candidate
            </a>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-slate-500">Loading dashboard...</p>
              </div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border-l-4 border-red-500 rounded-r-xl p-4 flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500">error</span>
              <p className="text-red-800 font-medium text-sm">{error}</p>
            </div>
          ) : analytics ? (
            <>
              {/* Top Stats Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-500 text-sm font-medium">Total Candidates</span>
                    <span className="material-symbols-outlined text-primary bg-primary/10 p-1.5 rounded-lg text-lg">group</span>
                  </div>
                  <div className="flex items-end gap-2">
                    <h3 className="text-3xl font-bold">{analytics.total_candidates}</h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">All time candidates</p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-500 text-sm font-medium">Tier A Matches</span>
                    <span className="material-symbols-outlined text-amber-500 bg-amber-500/10 p-1.5 rounded-lg text-lg">verified</span>
                  </div>
                  <div className="flex items-end gap-2">
                    <h3 className="text-3xl font-bold">{analytics.by_tier["Tier A"] || 0}</h3>
                    <span className="text-xs text-slate-500 mb-1">
                      ({analytics.total_candidates > 0 ? Math.round(((analytics.by_tier["Tier A"] || 0) / analytics.total_candidates) * 100) : 0}%)
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">Top tier candidates</p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-500 text-sm font-medium">Active Jobs</span>
                    <span className="material-symbols-outlined text-indigo-500 bg-indigo-500/10 p-1.5 rounded-lg text-lg">work</span>
                  </div>
                  <div className="flex items-end gap-2">
                    <h3 className="text-3xl font-bold">{analytics.active_jobs}</h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">Open job posts</p>
                </div>

                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-slate-500 text-sm font-medium">Avg Match Score</span>
                    <span className="material-symbols-outlined text-emerald-500 bg-emerald-500/10 p-1.5 rounded-lg text-lg">query_stats</span>
                  </div>
                  <div className="flex items-end gap-2">
                    <h3 className="text-3xl font-bold">
                      {Object.values(analytics.avg_scores_by_tier).length > 0
                        ? Math.round(
                            Object.values(analytics.avg_scores_by_tier).reduce((acc, tier) => {
                              const scores = [tier.exact_match, tier.similarity_match, tier.achievement_impact, tier.ownership];
                              return acc + scores.reduce((a, b) => a + b, 0) / 4;
                            }, 0) / Object.values(analytics.avg_scores_by_tier).length
                          )
                        : 0}%
                    </h3>
                  </div>
                  <p className="text-xs text-slate-400 mt-2">System-wide average</p>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Tier Distribution */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                  <h2 className="text-lg font-bold mb-6">Candidate Distribution by Tier</h2>
                  <div className="space-y-4">
                    {["Tier A", "Tier B", "Tier C"].map((tier) => {
                      const count = analytics.by_tier[tier] || 0;
                      const percentage = analytics.total_candidates > 0 ? (count / analytics.total_candidates) * 100 : 0;
                      return (
                        <div key={tier}>
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-sm font-semibold text-slate-700">{tier}</span>
                            <span className="text-sm font-bold text-slate-900">{count} candidates</span>
                          </div>
                          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getTierBarColor(tier)} transition-all duration-500`}
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                          <p className="text-xs text-slate-500 mt-1">{percentage.toFixed(1)}% of total</p>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Top Locations */}
                {analytics.top_locations.length > 0 && (
                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                    <h2 className="text-lg font-bold mb-6">Top Locations</h2>
                    <div className="space-y-3">
                      {analytics.top_locations.slice(0, 5).map(([location, count], index) => (
                        <div key={location} className="flex items-center gap-3">
                          <span className="text-sm font-bold text-slate-400 w-6">{index + 1}</span>
                          <div className="flex-1">
                            <p className="text-sm font-medium text-slate-900">{location}</p>
                          </div>
                          <span className="text-sm font-bold text-slate-600">{count}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* Recent Candidates */}
              {analytics.recent_candidates.length > 0 && (
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                  <div className="p-6 border-b border-slate-200">
                    <h2 className="text-lg font-bold">Recent Candidates</h2>
                    <p className="text-sm text-slate-500 mt-1">Candidates added in the last 7 days</p>
                  </div>
                  <div className="divide-y divide-slate-100">
                    {analytics.recent_candidates.map((candidate) => (
                      <div key={candidate.id} className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div className="size-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold">
                            {candidate.name?.charAt(0).toUpperCase() || "U"}
                          </div>
                          <div>
                            <p className="text-sm font-semibold text-slate-900">{candidate.name || "Unknown"}</p>
                            <p className="text-xs text-slate-500">{candidate.email || "No email"}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={`px-2.5 py-1 rounded-full text-xs font-bold border ${getTierColor(candidate.tier)}`}>
                            {candidate.tier}
                          </span>
                          <span className="text-xs text-slate-400">
                            {new Date(candidate.created_at).toLocaleDateString()}
                          </span>
                          <a
                            href={`/candidates/${candidate.id}`}
                            className="text-primary text-sm font-bold hover:underline"
                          >
                            View
                          </a>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          ) : null}
        </div>
      </main>
    </div>
  );
}
