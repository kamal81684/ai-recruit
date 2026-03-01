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

export default function AnalyticsPage() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [timeRange, setTimeRange] = useState<"7d" | "30d" | "90d">("30d");

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    setLoading(true);
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
      case "Tier A": return { bg: "bg-emerald-50", text: "text-emerald-600", bar: "bg-emerald-500", border: "border-emerald-200" };
      case "Tier B": return { bg: "bg-orange-50", text: "text-orange-600", bar: "bg-orange-500", border: "border-orange-200" };
      case "Tier C": return { bg: "bg-red-50", text: "text-red-600", bar: "bg-red-500", border: "border-red-200" };
      default: return { bg: "bg-slate-50", text: "text-slate-600", bar: "bg-slate-500", border: "border-slate-200" };
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
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/dashboard">
            <span className="material-symbols-outlined text-slate-400">dashboard</span>
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
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg bg-primary/10 text-primary" href="/analytics">
            <span className="material-symbols-outlined">bar_chart</span>
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
          <h1 className="text-xl font-bold text-slate-900">Analytics</h1>
          <div className="flex items-center gap-3">
            <div className="flex items-center bg-slate-100 rounded-lg p-1">
              {["7d", "30d", "90d"].map((range) => (
                <button
                  key={range}
                  onClick={() => setTimeRange(range as typeof timeRange)}
                  className={`px-3 py-1 text-xs font-semibold rounded-md transition-all ${
                    timeRange === range
                      ? "bg-white text-slate-900 shadow-sm"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  {range === "7d" ? "7 Days" : range === "30d" ? "30 Days" : "90 Days"}
                </button>
              ))}
            </div>
            <button
              onClick={fetchAnalytics}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
              Refresh
            </button>
          </div>
        </header>

        <div className="p-8 space-y-8">
          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-slate-500">Loading analytics...</p>
              </div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border-l-4 border-red-500 rounded-r-xl p-4 flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500">error</span>
              <p className="text-red-800 font-medium text-sm">{error}</p>
            </div>
          ) : analytics ? (
            <>
              {/* Summary Stats */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-gradient-to-br from-emerald-50 to-teal-50 rounded-xl border border-emerald-200 p-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-emerald-100 rounded-xl">
                      <span className="material-symbols-outlined text-emerald-600 text-2xl">trending_up</span>
                    </div>
                    <div>
                      <p className="text-sm text-emerald-700 font-medium">Total Candidates</p>
                      <p className="text-3xl font-black text-emerald-900">{analytics.total_candidates}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border border-blue-200 p-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-blue-100 rounded-xl">
                      <span className="material-symbols-outlined text-blue-600 text-2xl">workspace_premium</span>
                    </div>
                    <div>
                      <p className="text-sm text-blue-700 font-medium">Tier A Candidates</p>
                      <p className="text-3xl font-black text-blue-900">{analytics.by_tier["Tier A"] || 0}</p>
                    </div>
                  </div>
                </div>

                <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-xl border border-purple-200 p-6">
                  <div className="flex items-center gap-4">
                    <div className="p-3 bg-purple-100 rounded-xl">
                      <span className="material-symbols-outlined text-purple-600 text-2xl">work</span>
                    </div>
                    <div>
                      <p className="text-sm text-purple-700 font-medium">Active Job Posts</p>
                      <p className="text-3xl font-black text-purple-900">{analytics.active_jobs}</p>
                    </div>
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Tier Distribution Pie Chart (simplified as bar) */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                  <h2 className="text-lg font-bold mb-6">Candidate Distribution by Tier</h2>
                  <div className="space-y-5">
                    {["Tier A", "Tier B", "Tier C"].map((tier) => {
                      const count = analytics.by_tier[tier] || 0;
                      const percentage = analytics.total_candidates > 0 ? (count / analytics.total_candidates) * 100 : 0;
                      const colors = getTierColor(tier);
                      return (
                        <div key={tier}>
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full ${colors.bar}`}></div>
                              <span className="text-sm font-semibold text-slate-700">{tier}</span>
                            </div>
                            <div className="text-right">
                              <span className="text-sm font-bold text-slate-900">{count}</span>
                              <span className="text-xs text-slate-500 ml-1">({percentage.toFixed(1)}%)</span>
                            </div>
                          </div>
                          <div className="w-full h-4 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${colors.bar} transition-all duration-700 ease-out`}
                              style={{ width: `${percentage}%` }}
                            ></div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Average Scores by Tier */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                  <h2 className="text-lg font-bold mb-6">Average Scores by Tier</h2>
                  <div className="space-y-4">
                    {Object.entries(analytics.avg_scores_by_tier).map(([tier, scores]) => {
                      const colors = getTierColor(tier);
                      const avgScore = (scores.exact_match + scores.similarity_match + scores.achievement_impact + scores.ownership) / 4;
                      return (
                        <div key={tier} className={`p-4 rounded-lg border ${colors.bg} ${colors.border}`}>
                          <div className="flex items-center justify-between mb-3">
                            <span className={`text-sm font-bold ${colors.text}`}>{tier}</span>
                            <span className={`text-lg font-black ${colors.text}`}>{avgScore.toFixed(0)}</span>
                          </div>
                          <div className="grid grid-cols-2 gap-2 text-xs">
                            <div className="flex justify-between">
                              <span className="text-slate-500">Exact Match:</span>
                              <span className="font-semibold text-slate-700">{scores.exact_match}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Similarity:</span>
                              <span className="font-semibold text-slate-700">{scores.similarity_match}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Impact:</span>
                              <span className="font-semibold text-slate-700">{scores.achievement_impact}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-slate-500">Ownership:</span>
                              <span className="font-semibold text-slate-700">{scores.ownership}</span>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* Candidates Over Time */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 lg:col-span-2">
                  <h2 className="text-lg font-bold mb-6">Candidates Added Over Time (Last 30 Days)</h2>
                  {analytics.candidates_over_time.length > 0 ? (
                    <div className="space-y-3">
                      {analytics.candidates_over_time.slice(-10).map(([date, count]) => (
                        <div key={date} className="flex items-center gap-4">
                          <span className="text-xs text-slate-500 w-24 flex-shrink-0">
                            {new Date(date).toLocaleDateString("en-US", { month: "short", day: "numeric" })}
                          </span>
                          <div className="flex-1 h-8 bg-slate-100 rounded-lg overflow-hidden flex items-end">
                            <div
                              className="h-full bg-gradient-to-t from-primary to-purple-500 transition-all duration-500 hover:from-primary/80 hover:to-purple-500/80"
                              style={{ width: `${Math.max((count / Math.max(...analytics.candidates_over_time.map(([, c]) => c), 1)) * 100, 5)}%` }}
                            ></div>
                          </div>
                          <span className="text-sm font-bold text-slate-700 w-8 text-right">{count}</span>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <p className="text-slate-500 text-sm text-center py-8">No data available for the selected time range</p>
                  )}
                </div>

                {/* Top Locations */}
                {analytics.top_locations.length > 0 && (
                  <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                    <h2 className="text-lg font-bold mb-6">Top Candidate Locations</h2>
                    <div className="space-y-3">
                      {analytics.top_locations.map(([location, count], index) => (
                        <div key={location} className="flex items-center gap-4">
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center text-sm font-bold ${
                            index === 0 ? "bg-amber-100 text-amber-700" :
                            index === 1 ? "bg-slate-200 text-slate-600" :
                            index === 2 ? "bg-orange-100 text-orange-700" :
                            "bg-slate-100 text-slate-500"
                          }`}>
                            {index + 1}
                          </div>
                          <div className="flex-1">
                            <p className="text-sm font-semibold text-slate-900">{location}</p>
                          </div>
                          <div className="flex items-center gap-2">
                            <div className="w-20 h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-primary"
                                style={{ width: `${(count / analytics.top_locations[0][1]) * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm font-bold text-slate-600 w-8 text-right">{count}</span>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Score Breakdown */}
                <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
                  <h2 className="text-lg font-bold mb-6">Score Category Averages</h2>
                  <div className="space-y-4">
                    {[
                      { key: "exact_match", label: "Exact Match", icon: "rule_folder", color: "bg-blue-500" },
                      { key: "similarity_match", label: "Semantic Match", icon: "hub", color: "bg-purple-500" },
                      { key: "achievement_impact", label: "Business Impact", icon: "rocket_launch", color: "bg-emerald-500" },
                      { key: "ownership", label: "Project Ownership", icon: "award_star", color: "bg-amber-500" },
                    ].map((category) => {
                      const avgScore = Object.values(analytics.avg_scores_by_tier).length > 0
                        ? Object.values(analytics.avg_scores_by_tier).reduce((acc, tier) => acc + tier[category.key as keyof typeof tier], 0) / Object.values(analytics.avg_scores_by_tier).length
                        : 0;
                      return (
                        <div key={category.key} className="flex items-center gap-4">
                          <div className={`p-2 rounded-lg ${category.color} bg-opacity-10`}>
                            <span className={`material-symbols-outlined ${category.color.replace("bg-", "text-")}`}>{category.icon}</span>
                          </div>
                          <div className="flex-1">
                            <div className="flex items-center justify-between mb-1">
                              <span className="text-sm font-semibold text-slate-700">{category.label}</span>
                              <span className="text-sm font-bold text-slate-900">{avgScore.toFixed(1)}/100</span>
                            </div>
                            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                              <div
                                className={`h-full ${category.color} transition-all duration-500`}
                                style={{ width: `${avgScore}%` }}
                              ></div>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              </div>
            </>
          ) : null}
        </div>
      </main>
    </div>
  );
}
