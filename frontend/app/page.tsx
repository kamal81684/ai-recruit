"use client";

import { useState, useEffect } from "react";

interface EvaluationData {
  tier: string;
  summary: string;
  exact_match: { score: number; explanation: string };
  similarity_match: { score: number; explanation: string };
  achievement_impact: { score: number; explanation: string };
  ownership: { score: number; explanation: string };
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function Home() {
  const [jobDescription, setJobDescription] = useState("");
  const [resumeFile, setResumeFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<EvaluationData | null>(null);
  const [backendStatus, setBackendStatus] = useState<"checking" | "connected" | "disconnected">("checking");

  // Check backend connection on mount
  useEffect(() => {
    const checkBackend = async () => {
      try {
        const response = await fetch(`${API_URL}/health`, {
          signal: AbortSignal.timeout(5000),
        });
        if (response.ok) {
          setBackendStatus("connected");
        } else {
          setBackendStatus("disconnected");
        }
      } catch {
        setBackendStatus("disconnected");
      }
    };

    checkBackend();
    const interval = setInterval(checkBackend, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file && file.type === "application/pdf") {
      setResumeFile(file);
      setError("");
    } else {
      setError("Please upload a valid PDF file.");
      setResumeFile(null);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && file.type === "application/pdf") {
      setResumeFile(file);
      setError("");
    } else {
      setError("Please upload a valid PDF file.");
      setResumeFile(null);
    }
  };

  const handleEvaluate = async () => {
    if (!jobDescription.trim() || !resumeFile) {
      setError("Please provide both a Job Description and a Resume.");
      return;
    }

    setIsLoading(true);
    setError("");

    const formData = new FormData();
    formData.append("jobDescription", jobDescription);
    formData.append("resume", resumeFile);

    try {
      const response = await fetch(`${API_URL}/api/evaluate`, {
        method: "POST",
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Evaluation failed");
      }

      setResult(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || "An error occurred during evaluation. Please try again.");
      } else {
        setError("An error occurred during evaluation. Please try again.");
      }
      console.error(err);
    } finally {
      setIsLoading(false);
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

  const formatFileSize = (bytes: number) => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(0) + " KB";
    return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  };

  return (
    <div className="relative flex h-auto min-screen w-full flex-col">
      <div className="layout-container flex h-full grow flex-col">
        {/* Top Navigation Bar */}
        <header className="flex items-center justify-between whitespace-nowrap border-b border-solid border-slate-200 bg-white px-6 lg:px-10 py-3">
          <div className="flex items-center gap-8">
            <div className="flex items-center gap-4 text-primary">
              <div className="size-8 bg-primary rounded-lg flex items-center justify-center text-white">
                <span className="material-symbols-outlined">cognition</span>
              </div>
              <h2 className="text-slate-900 text-lg font-bold leading-tight tracking-tight">AI Recruit</h2>
            </div>
            <label className="hidden md:flex flex-col min-w-40 h-10 max-w-64">
              <div className="flex w-full flex-1 items-stretch rounded-lg h-full">
                <div className="text-slate-500 flex border-none bg-slate-100 items-center justify-center pl-4 rounded-l-lg">
                  <span className="material-symbols-outlined">search</span>
                </div>
                <input className="form-input flex w-full min-w-0 flex-1 resize-none overflow-hidden rounded-lg text-slate-900 focus:outline-0 focus:ring-0 border-none bg-slate-100 focus:border-none h-full placeholder:text-slate-500 px-4 rounded-l-none border-l-0 pl-2 text-base font-normal" placeholder="Search candidates..." value="" readOnly />
              </div>
            </label>
          </div>
          <div className="flex flex-1 justify-end gap-6 items-center">
            <nav className="hidden lg:flex items-center gap-8">
              <a className="text-slate-600 hover:text-primary transition-colors text-sm font-medium" href="/candidates">Dashboard</a>
              <a className="text-slate-600 hover:text-primary transition-colors text-sm font-semibold border-b-2 border-transparent hover:border-primary py-1" href="/candidates">Candidates</a>
              <a className="text-slate-600 hover:text-primary transition-colors text-sm font-medium" href="#">Job Posts</a>
              <a className="text-slate-600 hover:text-primary transition-colors text-sm font-medium" href="#">Analytics</a>
            </nav>
            <div className="h-10 w-[1px] bg-slate-200 hidden lg:block mx-2"></div>
            <div className="bg-slate-200 bg-center bg-no-repeat aspect-square bg-cover rounded-full size-10 border border-slate-200" style={{ backgroundImage: 'url("https://images.unsplash.com/photo-1534528741775-53994a69daeb?auto=format&fit=crop&q=80&w=100&h=100")' }}></div>
          </div>
        </header>

        <main className="flex-1 flex flex-col items-center">
          <div className="w-full max-w-5xl px-6 py-8">
            {/* Breadcrumbs */}
            <div className="flex items-center gap-2 mb-8 text-slate-500 text-sm font-medium">
              <a className="hover:text-primary" href="#">Dashboard</a>
              <span className="material-symbols-outlined text-xs">chevron_right</span>
              <a className="hover:text-primary" href="#">Candidates</a>
              <span className="material-symbols-outlined text-xs">chevron_right</span>
              <span className="text-slate-900">Add New Candidate</span>
            </div>

            {/* Page Header */}
            <div className="mb-10">
              <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-3">Add New Candidate</h1>
              <p className="text-slate-600 text-lg max-w-2xl leading-relaxed">
                Upload a resume to automatically extract professional details. Our AI will match the candidate&apos;s skills against your job requirements.
              </p>
            </div>

            {/* Error Message */}
            {error && (
              <div className="mb-8 p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl flex items-center gap-3">
                <span className="material-symbols-outlined text-red-500">error</span>
                <p className="text-red-800 font-medium text-sm">{error}</p>
              </div>
            )}

            {/* Content Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
              {/* Left Column: Resume Upload */}
              <div className="lg:col-span-2 flex flex-col gap-6">
                {/* Resume Upload Section */}
                <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center gap-2 mb-6">
                    <span className="material-symbols-outlined text-primary">description</span>
                    <h2 className="text-xl font-bold text-slate-900">Resume Upload</h2>
                  </div>

                  {/* Drag & Drop Zone */}
                  {!resumeFile ? (
                    <div
                      className="relative border-2 border-dashed border-primary/30 bg-primary/5 rounded-xl p-12 transition-all hover:bg-primary/10 hover:border-primary group flex flex-col items-center justify-center text-center cursor-pointer"
                      onDragOver={handleDragOver}
                      onDrop={handleDrop}
                    >
                      <div className="size-16 bg-primary/10 rounded-full flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                        <span className="material-symbols-outlined text-primary text-4xl">upload_file</span>
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">Drag and drop resume here</h3>
                      <p className="text-slate-500 mb-6 text-sm">Supported formats: PDF, DOCX, TXT (Max 10MB)</p>
                      <button className="bg-primary text-white px-6 py-2.5 rounded-lg font-bold hover:bg-primary/90 transition-colors shadow-lg shadow-primary/20">
                        Browse Files
                      </button>
                      <input className="absolute inset-0 opacity-0 cursor-pointer" type="file" accept=".pdf,.docx,.txt" onChange={handleFileChange} />
                    </div>
                  ) : (
                    <div className="relative border-2 border-primary/30 bg-primary/5 rounded-xl p-8 flex flex-col items-center justify-center text-center">
                      <button
                        onClick={() => setResumeFile(null)}
                        className="absolute top-4 right-4 p-1 hover:bg-slate-200 rounded transition-colors"
                      >
                        <span className="material-symbols-outlined text-slate-400 text-lg">close</span>
                      </button>
                      <div className="size-16 bg-primary/10 rounded-full flex items-center justify-center mb-4">
                        <span className="material-symbols-outlined text-primary text-4xl">picture_as_pdf</span>
                      </div>
                      <h3 className="text-lg font-semibold text-slate-900 mb-2">{resumeFile.name}</h3>
                      <p className="text-slate-500 text-sm">{formatFileSize(resumeFile.size)} • Ready to analyze</p>
                    </div>
                  )}

                  {/* Uploaded Files List */}
                  {resumeFile && (
                    <div className="mt-6 flex items-center gap-3 p-3 bg-slate-50 rounded-lg border border-slate-100">
                      <span className="material-symbols-outlined text-red-500">picture_as_pdf</span>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-slate-900 leading-none">{resumeFile.name}</p>
                        <p className="text-xs text-slate-500 mt-1">{formatFileSize(resumeFile.size)} • Ready to analyze</p>
                      </div>
                      <button
                        onClick={() => setResumeFile(null)}
                        className="p-1 hover:bg-slate-200 rounded transition-colors"
                      >
                        <span className="material-symbols-outlined text-slate-400 text-lg">close</span>
                      </button>
                    </div>
                  )}
                </div>

                {/* Job Description Section */}
                <div className="bg-white p-8 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center gap-2 mb-6">
                    <span className="material-symbols-outlined text-primary">work_outline</span>
                    <h2 className="text-xl font-bold text-slate-900">Target Role (Optional)</h2>
                  </div>
                  <p className="text-sm text-slate-500 mb-4">Provide a job description to get a specific match score and AI-generated interview questions.</p>
                  <textarea
                    value={jobDescription}
                    onChange={(e) => setJobDescription(e.target.value)}
                    className="w-full h-48 rounded-xl border-slate-200 bg-slate-50 p-4 text-slate-900 focus:ring-primary focus:border-primary transition-all placeholder:text-slate-400"
                    placeholder="Paste the job description here or select an existing job post..."
                  />
                  <div className="mt-4 flex justify-between items-center">
                    <button className="flex items-center gap-2 text-primary text-sm font-semibold hover:underline">
                      <span className="material-symbols-outlined text-sm">link</span>
                      Select from active Job Posts
                    </button>
                    <span className="text-xs text-slate-400 font-medium">{jobDescription.trim() ? jobDescription.trim().split(/\s+/).length : 0} words entered</span>
                  </div>
                </div>
              </div>

              {/* Right Column: Settings & Actions */}
              <div className="lg:col-span-1 flex flex-col gap-6">
                {/* Analysis Settings */}
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <h3 className="font-bold text-slate-900 mb-4">Analysis Settings</h3>
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">Detailed Skills Gap</label>
                      <div className="relative inline-block w-10 align-middle select-none">
                        <input defaultChecked className="sr-only peer" id="toggle-skills" type="checkbox" />
                        <div className="block bg-slate-200 w-10 h-6 rounded-full"></div>
                        <div className="absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition peer-checked:translate-x-full peer-checked:bg-primary"></div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">Generate Interview Qs</label>
                      <div className="relative inline-block w-10 align-middle select-none">
                        <input defaultChecked className="sr-only peer" id="toggle-questions" type="checkbox" />
                        <div className="block bg-slate-200 w-10 h-6 rounded-full"></div>
                        <div className="absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition peer-checked:translate-x-full peer-checked:bg-primary"></div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between">
                      <label className="text-sm font-medium text-slate-700">Anonymize Profile</label>
                      <div className="relative inline-block w-10 align-middle select-none">
                        <input className="sr-only peer" id="toggle-anon" type="checkbox" />
                        <div className="block bg-slate-200 w-10 h-6 rounded-full"></div>
                        <div className="absolute left-1 top-1 bg-white w-4 h-4 rounded-full transition peer-checked:translate-x-full peer-checked:bg-primary"></div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Big Action Area */}
                <div className="bg-primary/5 p-6 rounded-xl border border-primary/20 flex flex-col gap-4">
                  <button
                    onClick={handleEvaluate}
                    disabled={isLoading || !resumeFile || backendStatus !== "connected"}
                    className="w-full bg-primary disabled:bg-slate-300 text-white h-14 rounded-xl font-bold text-lg flex items-center justify-center gap-2 hover:bg-primary/90 transition-all shadow-xl shadow-primary/20 active:scale-[0.98] disabled:active:scale-100 disabled:cursor-not-allowed"
                  >
                    {isLoading ? (
                      <>
                        <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                        Analyzing...
                      </>
                    ) : (
                      <>
                        <span className="material-symbols-outlined">auto_awesome</span>
                        Analyze with AI
                      </>
                    )}
                  </button>
                  <p className="text-center text-xs text-slate-500">
                    This will use 1 analysis credit. You have 42 credits remaining.
                  </p>
                </div>

                {/* Information Card */}
                <div className="bg-slate-100 p-6 rounded-xl flex items-start gap-4">
                  <span className="material-symbols-outlined text-primary">info</span>
                  <div className="flex-1">
                    <h4 className="text-sm font-bold text-slate-900 mb-1">Quick Tip</h4>
                    <p className="text-sm text-slate-600 leading-snug">
                      Analysis usually takes 10-15 seconds. We&apos;ll automatically save the candidate to your dashboard once complete.
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Results Section */}
            {result && (
              <div className="mt-12">
                <div className="flex items-center justify-between mb-8">
                  <h2 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-3">
                    <span className="bg-primary/10 text-primary p-2 rounded-xl border border-primary/20">
                      <span className="material-symbols-outlined block">insights</span>
                    </span>
                    Analysis Report
                  </h2>
                  <div className="flex gap-2">
                    <button className="flex items-center gap-1.5 text-sm font-bold text-slate-600 bg-white border border-slate-200 px-4 py-2 rounded-lg hover:bg-slate-50 transition-colors shadow-sm">
                      <span className="material-symbols-outlined text-[18px]">download</span> Export
                    </button>
                  </div>
                </div>

                <div className="bg-white rounded-3xl border border-slate-200 shadow-[0_8px_30px_-4px_rgba(0,0,0,0.05)] overflow-hidden">
                  <div className="absolute top-0 inset-x-0 h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-primary"></div>

                  <div className="p-8 lg:p-10 pb-10">
                    {/* Tier and Executive Summary */}
                    <div className="flex flex-col lg:flex-row gap-8 lg:gap-12 items-center lg:items-start border-b border-slate-100 pt-2 pb-10 mb-8">
                      <div className="flex flex-col items-center flex-shrink-0">
                        <span className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3">Overall Rating</span>
                        <div className={`flex flex-col items-center justify-center w-[140px] h-[140px] rounded-[32px] border-4 shadow-xl ${getTierColor(result.tier)} relative overflow-hidden group`}>
                          <div className="absolute inset-0 bg-white/40 mix-blend-overlay"></div>
                          <span className="text-5xl font-black uppercase tracking-tight relative z-10 transform group-hover:scale-110 transition-transform duration-500 leading-none mb-1">
                            {result.tier.replace('Tier ', '')}
                          </span>
                          <span className="text-sm font-bold uppercase tracking-widest relative z-10 opacity-70">Tier</span>
                        </div>
                      </div>

                      <div className="flex-1 w-full bg-slate-50 rounded-3xl p-7 relative border border-slate-100/50 h-full flex flex-col justify-center">
                        <span className="material-symbols-outlined absolute -top-4 -left-2 text-[40px] text-primary/20 transform -rotate-12 bg-white rounded-full">format_quote</span>
                        <h3 className="text-xs font-black text-slate-400 uppercase tracking-widest mb-3 flex items-center gap-2">
                          <span className="material-symbols-outlined text-[14px]">psychology</span> Executive Summary
                        </h3>
                        <p className="text-slate-800 leading-relaxed text-lg font-medium pr-4">{result.summary}</p>
                      </div>
                    </div>

                    {/* Score Metrics Grid */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 lg:gap-6 mb-12">
                      {[
                        { val: result.exact_match.score, title: "Exact Match", bg: "bg-blue-50", border: "border-blue-100", text: "text-blue-600", label: "text-blue-800", icon: "rule" },
                        { val: result.similarity_match.score, title: "Semantic Value", bg: "bg-purple-50", border: "border-purple-100", text: "text-purple-600", label: "text-purple-800", icon: "join_inner" },
                        { val: result.achievement_impact.score, title: "Business Impact", bg: "bg-emerald-50", border: "border-emerald-100", text: "text-emerald-600", label: "text-emerald-800", icon: "emoji_events" },
                        { val: result.ownership.score, title: "Project Ownership", bg: "bg-amber-50", border: "border-amber-100", text: "text-amber-600", label: "text-amber-800", icon: "gavel" }
                      ].map((stat, i) => (
                        <div key={i} className={`${stat.bg} border ${stat.border} rounded-2xl p-6 text-center transition-all hover:-translate-y-1 hover:shadow-lg flex flex-col items-center justify-center relative overflow-hidden group`}>
                          <div className={`absolute -right-4 -bottom-4 opacity-[0.03] group-hover:scale-150 transition-transform duration-700 ${stat.text}`}>
                            <span className="material-symbols-outlined text-[100px]">{stat.icon}</span>
                          </div>
                          <span className={`material-symbols-outlined ${stat.text} text-2xl mb-3 relative z-10`}>{stat.icon}</span>
                          <div className="relative z-10 flex items-baseline gap-1">
                            <p className={`text-4xl font-black tracking-tight ${stat.text}`}>
                              {stat.val}<span className="text-xl font-bold opacity-50">/100</span>
                            </p>
                          </div>
                          <p className={`text-sm font-bold tracking-wide mt-2 ${stat.label} uppercase opacity-80 z-10`}>
                            {stat.title}
                          </p>
                        </div>
                      ))}
                    </div>

                    {/* Detailed Explanations */}
                    <div className="max-w-[840px] mx-auto">
                      <div className="flex items-center gap-3 mb-6">
                        <h3 className="text-xl font-black text-slate-900 tracking-tight flex-1">
                          Evaluation Breakdown
                        </h3>
                        <div className="h-px bg-slate-200 flex-[2]"></div>
                      </div>

                      <div className="space-y-4">
                        {[
                          { key: "exact_match", title: "Exact Requirements Match", colorClass: "text-blue-600", icon: "rule_folder", border: "border-l-blue-500" },
                          { key: "similarity_match", title: "Semantic Concept Match", colorClass: "text-purple-600", icon: "hub", border: "border-l-purple-500" },
                          { key: "achievement_impact", title: "Scale & Impact Analysis", colorClass: "text-emerald-600", icon: "rocket_launch", border: "border-l-emerald-500" },
                          { key: "ownership", title: "Leadership & Autonomy", colorClass: "text-amber-600", icon: "award_star", border: "border-l-amber-500" },
                        ].map((section) => (
                          <details
                            key={section.key}
                            className={`group bg-white rounded-2xl border border-slate-200 border-l-[6px] ${section.border} overflow-hidden shadow-sm open:shadow-md transition-shadow`}
                            open={section.key === "exact_match"}
                          >
                            <summary className="flex items-center gap-4 p-5 py-5 cursor-pointer hover:bg-slate-50 transition-colors list-none outline-none">
                              <div className={`p-2 rounded-xl bg-slate-100 flex items-center justify-center ${section.colorClass}`}>
                                <span className="material-symbols-outlined text-[20px]">{section.icon}</span>
                              </div>
                              <span className="font-bold text-slate-800 flex-1 text-lg tracking-wide">
                                {section.title}
                              </span>
                              <div className="bg-slate-100 rounded-full w-8 h-8 flex items-center justify-center">
                                <span className="material-symbols-outlined text-slate-400 group-open:rotate-180 transition-transform duration-300">
                                  expand_more
                                </span>
                              </div>
                            </summary>
                            <div className="p-6 pt-2 pl-[76px] pr-8">
                              <div className="flex gap-4">
                                <div className="w-[3px] bg-slate-100 rounded-full my-1"></div>
                                <p className="text-slate-600 whitespace-pre-wrap leading-[1.8] font-medium text-[15px]">
                                  {result[section.key as "exact_match" | "similarity_match" | "achievement_impact" | "ownership"].explanation}
                                </p>
                              </div>
                            </div>
                          </details>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Footer Links */}
            <div className="mt-12 flex flex-col md:flex-row justify-between items-center py-6 border-t border-slate-200 gap-4">
              <p className="text-slate-500 text-sm">© 2024 AI Recruit. Powered by GPT-4 Advanced Reasoning.</p>
              <div className="flex gap-6">
                <a className="text-slate-500 hover:text-primary text-sm transition-colors" href="#">Privacy Policy</a>
                <a className="text-slate-500 hover:text-primary text-sm transition-colors" href="#">Help Center</a>
                <a className="text-slate-500 hover:text-primary text-sm transition-colors" href="#">System Status</a>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}
