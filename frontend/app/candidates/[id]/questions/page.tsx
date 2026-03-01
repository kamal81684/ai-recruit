"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";

interface InterviewQuestion {
  id: number;
  candidate_id: number;
  question: string;
  category: string;
  created_at: string;
}

interface Candidate {
  id: number;
  name: string;
  email: string;
  tier: string;
  current_role?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:5001";

export default function InterviewQuestionsPage() {
  const params = useParams();
  const candidateId = params.id;
  const [questions, setQuestions] = useState<InterviewQuestion[]>([]);
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  useEffect(() => {
    fetchCandidate();
    fetchQuestions();
  }, [candidateId]);

  const fetchCandidate = async () => {
    try {
      const response = await fetch(`${API_URL}/api/candidates/${candidateId}`);
      if (response.ok) {
        const data = await response.json();
        setCandidate(data);
      }
    } catch (err) {
      console.error("Failed to fetch candidate:", err);
    }
  };

  const fetchQuestions = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/candidates/${candidateId}/interview-questions`);
      if (response.ok) {
        const data = await response.json();
        setQuestions(data.questions || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load questions");
    } finally {
      setLoading(false);
    }
  };

  const generateQuestions = async () => {
    setGenerating(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/candidates/${candidateId}/interview-questions`, {
        method: "POST",
      });
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || "Failed to generate questions");
      }
      const data = await response.json();
      setQuestions(data.questions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to generate questions");
    } finally {
      setGenerating(false);
    }
  };

  const categories = ["all", ...Array.from(new Set(questions.map((q) => q.category)))];
  const filteredQuestions = selectedCategory === "all"
    ? questions
    : questions.filter((q) => q.category === selectedCategory);

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case "technical":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "behavioral":
        return "bg-purple-100 text-purple-700 border-purple-200";
      case "cultural":
        return "bg-emerald-100 text-emerald-700 border-emerald-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category.toLowerCase()) {
      case "technical":
        return "code";
      case "behavioral":
        return "psychology";
      case "cultural":
        return "groups";
      default:
        return "help";
    }
  };

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Sidebar */}
      <aside className="w-80 border-r border-slate-200 bg-white flex flex-col">
        <div className="p-6 border-b border-slate-200">
          <div className="flex items-center gap-3 mb-6">
            <div className="size-10 bg-primary rounded-lg flex items-center justify-center text-white">
              <span className="material-symbols-outlined">quiz</span>
            </div>
            <div>
              <h1 className="text-lg font-bold leading-tight">Interview Questions</h1>
              <p className="text-xs text-slate-500">AI-powered questions</p>
            </div>
          </div>

          {candidate && (
            <div className="bg-slate-50 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-1">Candidate</p>
              <p className="text-sm font-bold text-slate-900">{candidate.name || "Unknown"}</p>
              {candidate.current_role && (
                <p className="text-xs text-primary mt-1">{candidate.current_role}</p>
              )}
              <div className="flex items-center gap-2 mt-3">
                <a
                  href={`/candidates/${candidateId}`}
                  className="text-xs text-slate-500 hover:text-primary transition-colors flex items-center gap-1"
                >
                  <span className="material-symbols-outlined text-[14px]">arrow_back</span>
                  Back to profile
                </a>
              </div>
            </div>
          )}
        </div>

        <div className="p-6 flex-1 overflow-y-auto">
          <h3 className="text-sm font-bold text-slate-700 mb-3">Categories</h3>
          <div className="space-y-1">
            {categories.map((category) => {
              const count = category === "all"
                ? questions.length
                : questions.filter((q) => q.category === category).length;
              return (
                <button
                  key={category}
                  onClick={() => setSelectedCategory(category)}
                  className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    selectedCategory === category
                      ? "bg-primary text-white"
                      : "text-slate-600 hover:bg-slate-100"
                  }`}
                >
                  <span className="capitalize">{category}</span>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    selectedCategory === category
                      ? "bg-white/20"
                      : "bg-slate-200 text-slate-600"
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-4 border-t border-slate-200">
          <button
            onClick={generateQuestions}
            disabled={generating}
            className="w-full bg-gradient-to-r from-primary to-purple-600 hover:from-primary/90 hover:to-purple-600/90 disabled:from-slate-300 disabled:to-slate-400 text-white px-4 py-3 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-primary/20 flex items-center justify-center gap-2"
          >
            {generating ? (
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
                Generate AI Questions
              </>
            )}
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 border-b border-slate-200 bg-white flex items-center justify-between px-8">
          <div>
            <h2 className="text-xl font-bold text-slate-900">
              {candidate?.name || "Candidate"} - Interview Questions
            </h2>
            <p className="text-sm text-slate-500">
              {filteredQuestions.length} question{filteredQuestions.length !== 1 ? "s" : ""} {selectedCategory !== "all" && `in ${selectedCategory}`}
            </p>
          </div>
          <div className="flex items-center gap-3">
            <button
              onClick={fetchQuestions}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-semibold border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors"
            >
              <span className="material-symbols-outlined text-[18px]">refresh</span>
              Refresh
            </button>
          </div>
        </header>

        {/* Questions List */}
        <div className="flex-1 overflow-y-auto p-8">
          {loading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="mt-4 text-slate-500">Loading questions...</p>
              </div>
            </div>
          ) : error ? (
            <div className="bg-red-50 border-l-4 border-red-500 rounded-r-xl p-4 flex items-center gap-3 max-w-md">
              <span className="material-symbols-outlined text-red-500">error</span>
              <div>
                <p className="text-red-800 font-medium text-sm">{error}</p>
                <button
                  onClick={fetchQuestions}
                  className="text-red-600 text-xs font-semibold mt-1 hover:underline"
                >
                  Try again
                </button>
              </div>
            </div>
          ) : filteredQuestions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="w-20 h-20 bg-slate-100 rounded-full flex items-center justify-center mb-6">
                <span className="material-symbols-outlined text-4xl text-slate-400">quiz</span>
              </div>
              <h3 className="text-xl font-bold text-slate-900 mb-2">No Interview Questions Yet</h3>
              <p className="text-slate-500 max-w-md mb-6">
                {selectedCategory !== "all"
                  ? `No questions found in the ${selectedCategory} category.`
                  : "Generate AI-powered interview questions tailored to this candidate's profile and the job description."}
              </p>
              <button
                onClick={generateQuestions}
                disabled={generating}
                className="bg-primary hover:bg-primary/90 disabled:bg-slate-300 text-white px-6 py-3 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-primary/20 flex items-center gap-2"
              >
                <span className="material-symbols-outlined">auto_awesome</span>
                Generate Questions
              </button>
            </div>
          ) : (
            <div className="max-w-4xl mx-auto space-y-4">
              {filteredQuestions.map((question, index) => (
                <div
                  key={question.id}
                  className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg hover:border-primary/30 transition-all group"
                >
                  <div className="flex items-start gap-4">
                    <div className="flex-shrink-0">
                      <div className="w-10 h-10 rounded-full bg-gradient-to-br from-primary to-purple-600 flex items-center justify-center text-white font-bold text-lg">
                        {index + 1}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <div className="flex-1">
                          <h4 className="text-lg font-semibold text-slate-900 leading-snug">
                            {question.question}
                          </h4>
                        </div>
                        <span className={`flex-shrink-0 inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold border ${getCategoryColor(question.category)}`}>
                          <span className="material-symbols-outlined text-[14px]">{getCategoryIcon(question.category)}</span>
                          {question.category}
                        </span>
                      </div>
                      <div className="flex items-center gap-4 text-xs text-slate-400">
                        <span className="material-symbols-outlined text-[16px]">schedule</span>
                        Created {new Date(question.created_at).toLocaleDateString()}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
