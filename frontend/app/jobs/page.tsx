"use client";

import { useState, useEffect } from "react";

interface JobPost {
  id: number;
  title: string;
  description: string;
  location?: string;
  requirements?: string;
  status: string;
  created_at: string;
  updated_at: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function JobsPage() {
  const [jobs, setJobs] = useState<JobPost[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [useAI, setUseAI] = useState(false);
  const [aiGenerating, setAiGenerating] = useState(false);
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    location: "",
    requirements: "",
    additionalInfo: "",
  });

  useEffect(() => {
    fetchJobs();
  }, []);

  const fetchJobs = async () => {
    try {
      const response = await fetch(`${API_URL}/api/jobs?status=active`);
      if (!response.ok) throw new Error("Failed to fetch job posts");
      const data = await response.json();
      setJobs(data.job_posts || []);
    } catch (err) {
      console.error("Failed to load jobs:", err);
      setError(err instanceof Error ? err.message : "Failed to load job posts");
    } finally {
      setLoading(false);
    }
  };

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.title.trim() || !formData.description.trim()) {
      setError("Title and description are required.");
      return;
    }

    setLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/jobs`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formData.title,
          description: formData.description,
          location: formData.location || undefined,
          requirements: formData.requirements || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to create job post");
      }

      // Reset form and refresh jobs
      setFormData({ title: "", description: "", location: "", requirements: "", additionalInfo: "" });
      setShowCreateForm(false);
      setUseAI(false);
      await fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job post");
    } finally {
      setLoading(false);
    }
  };

  const handleAIGenerate = async () => {
    if (!formData.title.trim()) {
      setError("Please enter a job title first.");
      return;
    }

    setAiGenerating(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/jobs/generate-ai`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          title: formData.title,
          location: formData.location || undefined,
          additional_info: formData.additionalInfo || undefined,
        }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to generate job post");
      }

      const data = await response.json();
      setFormData({
        ...formData,
        description: data.description,
        requirements: data.requirements || "",
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate job post");
    } finally {
      setAiGenerating(false);
    }
  };

  const handleDeleteJob = async (jobId: number) => {
    if (!confirm("Are you sure you want to delete this job post?")) return;

    try {
      const response = await fetch(`${API_URL}/api/jobs/${jobId}`, {
        method: "DELETE",
      });

      if (!response.ok) throw new Error("Failed to delete job post");

      await fetchJobs();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to delete job post");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "active":
        return "bg-emerald-100 text-emerald-800";
      case "inactive":
        return "bg-slate-100 text-slate-800";
      default:
        return "bg-slate-100 text-slate-800";
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
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/">
            <span className="material-symbols-outlined text-slate-400">dashboard</span>
            Add Candidate
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg text-slate-600 hover:bg-slate-100 transition-colors" href="/candidates">
            <span className="material-symbols-outlined text-slate-400">group</span>
            Candidates
          </a>
          <a className="flex items-center gap-3 px-3 py-2 text-sm font-medium rounded-lg bg-primary/10 text-primary" href="/jobs">
            <span className="material-symbols-outlined">work</span>
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
          <h1 className="text-xl font-bold text-slate-900">Job Posts</h1>
          <button
            onClick={() => setShowCreateForm(!showCreateForm)}
            className="bg-primary hover:bg-primary/90 text-white px-4 py-2 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
          >
            <span className="material-symbols-outlined text-sm">add</span>
            New Job Post
          </button>
        </header>

        <div className="p-8">
          {/* Create Job Form */}
          {showCreateForm && (
            <div className="mb-8 bg-white rounded-xl border border-slate-200 shadow-sm p-6">
              <div className="flex items-center justify-between mb-6">
                <h2 className="text-lg font-bold">Create New Job Post</h2>
                <button
                  onClick={() => {
                    setShowCreateForm(false);
                    setUseAI(false);
                  }}
                  className="text-slate-400 hover:text-slate-600"
                >
                  <span className="material-symbols-outlined">close</span>
                </button>
              </div>

              {/* AI Toggle */}
              <div className="mb-6 p-4 bg-gradient-to-r from-primary/5 to-purple-50 rounded-xl border border-primary/20">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-primary/10 rounded-lg">
                      <span className="material-symbols-outlined text-primary text-xl">auto_awesome</span>
                    </div>
                    <div>
                      <h3 className="font-semibold text-slate-900">AI-Assisted Creation</h3>
                      <p className="text-sm text-slate-500">Let AI generate a professional job description</p>
                    </div>
                  </div>
                  <button
                    onClick={() => setUseAI(!useAI)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${useAI ? 'bg-primary' : 'bg-slate-200'}`}
                  >
                    <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${useAI ? 'translate-x-6' : 'translate-x-1'}`} />
                  </button>
                </div>
              </div>

              <form onSubmit={handleCreateJob} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Job Title *</label>
                  <input
                    type="text"
                    value={formData.title}
                    onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                    placeholder="e.g. Senior Software Engineer"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Location</label>
                  <input
                    type="text"
                    value={formData.location}
                    onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none"
                    placeholder="e.g. San Francisco, CA / Remote"
                  />
                </div>

                {useAI && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">Additional Context (Optional)</label>
                    <textarea
                      value={formData.additionalInfo}
                      onChange={(e) => setFormData({ ...formData, additionalInfo: e.target.value })}
                      rows={2}
                      className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"
                      placeholder="Any specific requirements, experience level, or company culture details..."
                    />
                    <button
                      type="button"
                      onClick={handleAIGenerate}
                      disabled={aiGenerating || !formData.title.trim()}
                      className="mt-2 flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 disabled:from-slate-300 disabled:to-slate-400 text-white rounded-lg text-sm font-semibold transition-all shadow-lg shadow-primary/20"
                    >
                      {aiGenerating ? (
                        <>
                          <svg className="animate-spin h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                          </svg>
                          Generating...
                        </>
                      ) : (
                        <>
                          <span className="material-symbols-outlined text-sm">auto_awesome</span>
                          Generate with AI
                        </>
                      )}
                    </button>
                  </div>
                )}

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Job Description *</label>
                  <textarea
                    value={formData.description}
                    onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                    rows={6}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"
                    placeholder={useAI ? "AI will generate this, or you can type manually..." : "Enter the full job description including responsibilities, requirements, and qualifications..."}
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Requirements (Optional)</label>
                  <textarea
                    value={formData.requirements}
                    onChange={(e) => setFormData({ ...formData, requirements: e.target.value })}
                    rows={4}
                    className="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none resize-none"
                    placeholder="Specific requirements or qualifications..."
                  />
                </div>

                <div className="flex gap-3 justify-end pt-2">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateForm(false);
                      setUseAI(false);
                    }}
                    className="px-4 py-2 border border-slate-200 rounded-lg text-sm font-semibold hover:bg-slate-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="bg-primary hover:bg-primary/90 disabled:bg-slate-300 text-white px-6 py-2 rounded-lg text-sm font-semibold transition-colors"
                  >
                    {loading ? "Creating..." : "Create Job Post"}
                  </button>
                </div>
              </form>
            </div>
          )}

          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500">error</span>
              <p className="text-red-800 font-medium text-sm">{error}</p>
              <button
                onClick={() => setError("")}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                <span className="material-symbols-outlined">close</span>
              </button>
            </div>
          )}

          {/* Job Posts List */}
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-bold">Active Job Posts</h2>
            </div>

            {loading && jobs.length === 0 ? (
              <div className="p-12 text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-slate-500">Loading job posts...</p>
              </div>
            ) : jobs.length === 0 ? (
              <div className="p-12 text-center">
                <span className="material-symbols-outlined text-4xl text-slate-300">work_off</span>
                <p className="mt-4 text-slate-500">No job posts yet</p>
                <button
                  onClick={() => setShowCreateForm(true)}
                  className="mt-4 px-4 py-2 bg-primary text-white rounded-lg text-sm font-semibold hover:bg-primary/90 transition-colors"
                >
                  Create First Job Post
                </button>
              </div>
            ) : (
              <div className="divide-y divide-slate-100">
                {jobs.map((job) => (
                  <div key={job.id} className="p-6 hover:bg-slate-50 transition-colors">
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-lg font-bold text-slate-900">{job.title}</h3>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${getStatusColor(job.status)}`}>
                            {job.status}
                          </span>
                        </div>
                        {job.location && (
                          <div className="flex items-center gap-1 text-sm text-slate-500 mb-3">
                            <span className="material-symbols-outlined text-[16px]">location_on</span>
                            {job.location}
                          </div>
                        )}
                        <p className="text-sm text-slate-600 line-clamp-3 mb-3">
                          {job.description}
                        </p>
                        {job.requirements && (
                          <div className="mt-2">
                            <p className="text-xs font-semibold text-slate-500 mb-1">Requirements:</p>
                            <p className="text-sm text-slate-600 line-clamp-2">{job.requirements}</p>
                          </div>
                        )}
                        <p className="text-xs text-slate-400 mt-3">
                          Created: {new Date(job.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(job.description);
                            alert("Job description copied to clipboard!");
                          }}
                          className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors"
                          title="Copy description"
                        >
                          <span className="material-symbols-outlined text-[18px]">content_copy</span>
                        </button>
                        <button
                          onClick={() => handleDeleteJob(job.id)}
                          className="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                          title="Delete job post"
                        >
                          <span className="material-symbols-outlined text-[18px]">delete</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
