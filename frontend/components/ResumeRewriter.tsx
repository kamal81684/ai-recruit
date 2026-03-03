"use client";

import { useState } from "react";

interface ResumeRewriteResult {
  improved_summary: string;
  suggested_bullets: string[];
  skills_to_highlight: string[];
  keywords_to_add: string[];
  cover_letter_suggestion: string;
}

interface ResumeRewriterProps {
  className?: string;
  initialResumeText?: string;
  initialJobDescription?: string;
  initialJobTitle?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function ResumeRewriter({
  className = "",
  initialResumeText = "",
  initialJobDescription = "",
  initialJobTitle = "",
}: ResumeRewriterProps) {
  const [resumeText, setResumeText] = useState(initialResumeText);
  const [jobDescription, setJobDescription] = useState(initialJobDescription);
  const [jobTitle, setJobTitle] = useState(initialJobTitle);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState<ResumeRewriteResult | null>(null);

  const handleRewrite = async () => {
    if (!resumeText.trim() || !jobDescription.trim() || !jobTitle.trim()) {
      setError("Please provide all required fields");
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/resume/rewrite`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          resume_text: resumeText,
          job_description: jobDescription,
          job_title: jobTitle,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.error || "Resume rewrite failed");
      }

      setResult(data);
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message || "An error occurred during rewrite. Please try again.");
      } else {
        setError("An error occurred during rewrite. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className={`resume-rewriter ${className}`}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          <div>
            <label className="block text-sm font-bold text-slate-900 mb-2">
              Target Job Title *
            </label>
            <input
              type="text"
              value={jobTitle}
              onChange={(e) => setJobTitle(e.target.value)}
              placeholder="e.g., Senior Software Engineer"
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all"
            />
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-900 mb-2">
              Current Resume Text *
            </label>
            <textarea
              value={resumeText}
              onChange={(e) => setResumeText(e.target.value)}
              placeholder="Paste your current resume content here..."
              rows={10}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-y font-mono text-sm"
            />
            <p className="text-xs text-slate-500 mt-2">
              {resumeText.trim().split(/\s+/).length} words
            </p>
          </div>

          <div>
            <label className="block text-sm font-bold text-slate-900 mb-2">
              Target Job Description *
            </label>
            <textarea
              value={jobDescription}
              onChange={(e) => setJobDescription(e.target.value)}
              placeholder="Paste the job description here..."
              rows={8}
              className="w-full px-4 py-3 rounded-xl border border-slate-200 bg-slate-50 focus:ring-2 focus:ring-primary/20 focus:border-primary transition-all resize-y text-sm"
            />
          </div>

          <button
            onClick={handleRewrite}
            disabled={isLoading || !resumeText.trim() || !jobDescription.trim() || !jobTitle.trim()}
            className="w-full bg-primary disabled:bg-slate-300 text-white h-14 rounded-xl font-bold text-lg flex items-center justify-center gap-2 hover:bg-primary/90 transition-all shadow-xl shadow-primary/20 active:scale-[0.98] disabled:active:scale-100 disabled:cursor-not-allowed"
          >
            {isLoading ? (
              <>
                <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Optimizing Resume...
              </>
            ) : (
              <>
                <span className="material-symbols-outlined">auto_fix_high</span>
                Optimize for Job
              </>
            )}
          </button>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {error && (
            <div className="p-4 bg-red-50 border-l-4 border-red-500 rounded-r-xl flex items-center gap-3">
              <span className="material-symbols-outlined text-red-500">error</span>
              <p className="text-red-800 font-medium text-sm">{error}</p>
            </div>
          )}

          {result && (
            <>
              {/* Improved Summary */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-primary">person</span>
                  <h3 className="text-lg font-bold text-slate-900">Improved Summary</h3>
                </div>
                <p className="text-slate-700 leading-relaxed bg-primary/5 p-4 rounded-lg border border-primary/10">
                  {result.improved_summary}
                </p>
              </div>

              {/* Suggested Bullets */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-primary">format_list_bulleted</span>
                  <h3 className="text-lg font-bold text-slate-900">Suggested Bullet Points</h3>
                </div>
                <ul className="space-y-3">
                  {result.suggested_bullets.map((bullet, idx) => (
                    <li key={idx} className="text-slate-700 bg-slate-50 p-3 rounded-lg border border-slate-100">
                      {bullet}
                    </li>
                  ))}
                </ul>
              </div>

              {/* Skills to Highlight */}
              <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                <div className="flex items-center gap-2 mb-4">
                  <span className="material-symbols-outlined text-primary">stars</span>
                  <h3 className="text-lg font-bold text-slate-900">Skills to Highlight</h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {result.skills_to_highlight.map((skill, idx) => (
                    <span
                      key={idx}
                      className="px-3 py-1.5 bg-primary/10 text-primary rounded-full text-sm font-semibold border border-primary/20"
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              {/* Keywords to Add */}
              {result.keywords_to_add && result.keywords_to_add.length > 0 && (
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-primary">label</span>
                    <h3 className="text-lg font-bold text-slate-900">Keywords to Incorporate</h3>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {result.keywords_to_add.map((keyword, idx) => (
                      <span
                        key={idx}
                        className="px-3 py-1.5 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium border border-emerald-200"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Cover Letter Suggestion */}
              {result.cover_letter_suggestion && (
                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                  <div className="flex items-center gap-2 mb-4">
                    <span className="material-symbols-outlined text-primary">mail</span>
                    <h3 className="text-lg font-bold text-slate-900">Cover Letter Opening</h3>
                  </div>
                  <p className="text-slate-700 leading-relaxed bg-blue-50 p-4 rounded-lg border border-blue-100 italic">
                    "{result.cover_letter_suggestion}"
                  </p>
                </div>
              )}
            </>
          )}

          {!result && !isLoading && (
            <div className="bg-slate-50 p-12 rounded-xl border border-slate-200 text-center">
              <span className="material-symbols-outlined text-6xl text-slate-300">auto_fix_high</span>
              <p className="mt-4 text-slate-600 font-medium">Enter your resume and job details to get AI-powered optimization suggestions</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
