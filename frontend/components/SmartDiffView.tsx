"use client";

import { useState, useMemo } from "react";
import { MaterialSymbol } from "react-material-symbols";

interface SkillMatch {
  skill: string;
  matched: boolean;
  confidence?: number;
}

interface SmartDiffViewProps {
  jobDescription: string;
  resumeText: string;
  extractedSkills?: string[];
}

/**
 * SmartDiffView - Side-by-side comparison component showing skill matches
 *
 * This component provides a visual diff view that highlights:
 * - Matched skills (green)
 * - Missing skills (red)
 * - Partial matches (yellow)
 *
 * Contributor: shubham21155102 - Enterprise Architecture Phase 7
 */
export default function SmartDiffView({
  jobDescription,
  resumeText,
  extractedSkills = [],
}: SmartDiffViewProps) {
  const [viewMode, setViewMode] = useState<"inline" | "sideBySide">("inline");
  const [showPartialMatches, setShowPartialMatches] = useState(true);

  // Extract potential skills from job description
  const jobSkills = useMemo(() => {
    const skillPatterns = [
      // Technical skills
      /\b(Python|JavaScript|TypeScript|Java|C\+\+|Go|Rust|Ruby|PHP|Swift|Kotlin)\b/gi,
      /\b(React|Angular|Vue|Node\.js|Express|Django|Flask|Spring|\.NET|Laravel)\b/gi,
      /\b(AWS|Azure|GCP|Docker|Kubernetes|Terraform|Ansible|Jenkins)\b/gi,
      /\b(SQL|NoSQL|MongoDB|PostgreSQL|MySQL|Redis|Elasticsearch)\b/gi,
      /\b(Machine Learning|AI|Data Science|Deep Learning|NLP|Computer Vision)\b/gi,
      // Soft skills
      /\b(leadership|communication|collaboration|teamwork|problem-solving|agile|scrum)\b/gi,
    ];

    const skills = new Set<string>();
    skillPatterns.forEach((pattern) => {
      const matches = jobDescription.match(pattern);
      if (matches) {
        matches.forEach((match) => skills.add(match.toLowerCase()));
      }
    });

    return Array.from(skills).sort();
  }, [jobDescription]);

  const resumeTextLower = resumeText.toLowerCase();

  // Analyze skill matches
  const skillMatches = useMemo(() => {
    const matches: SkillMatch[] = [];

    jobSkills.forEach((skill) => {
      const exactMatch = resumeTextLower.includes(skill.toLowerCase());
      const partialMatch = extractedSkills.some(
        (s) => s.toLowerCase().includes(skill.toLowerCase()) ||
               skill.toLowerCase().includes(s.toLowerCase())
      );

      if (exactMatch) {
        matches.push({ skill, matched: true, confidence: 1.0 });
      } else if (partialMatch && showPartialMatches) {
        matches.push({ skill, matched: true, confidence: 0.7 });
      } else {
        matches.push({ skill, matched: false });
      }
    });

    return matches;
  }, [jobSkills, resumeTextLower, extractedSkills, showPartialMatches]);

  // Calculate statistics
  const stats = useMemo(() => {
    const total = skillMatches.length;
    const matched = skillMatches.filter((m) => m.matched).length;
    const percentage = total > 0 ? (matched / total) * 100 : 0;

    return { total, matched, percentage };
  }, [skillMatches]);

  const getMatchColor = (match: SkillMatch) => {
    if (!match.matched) return "bg-red-100 text-red-700 border-red-200";
    if (match.confidence === 1.0) return "bg-green-100 text-green-700 border-green-200";
    return "bg-yellow-100 text-yellow-700 border-yellow-200";
  };

  const getMatchIcon = (match: SkillMatch) => {
    if (!match.matched) return "close";
    if (match.confidence === 1.0) return "check_circle";
    return "help";
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-slate-100 bg-slate-50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-primary/10 rounded-lg">
              <MaterialSymbol symbol="compare" size={24} className="text-primary" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900">Skill Match Analysis</h3>
              <p className="text-sm text-slate-500">
                {stats.matched} of {stats.total} skills matched ({stats.percentage.toFixed(1)}%)
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setViewMode("inline")}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                viewMode === "inline"
                  ? "bg-primary text-white"
                  : "bg-slate-200 text-slate-600 hover:bg-slate-300"
              }`}
            >
              Inline
            </button>
            <button
              onClick={() => setViewMode("sideBySide")}
              className={`px-3 py-1.5 text-sm font-medium rounded-lg transition-colors ${
                viewMode === "sideBySide"
                  ? "bg-primary text-white"
                  : "bg-slate-200 text-slate-600 hover:bg-slate-300"
              }`}
            >
              Side by Side
            </button>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="mt-4">
          <div className="h-3 bg-slate-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-red-500 via-yellow-500 to-green-500 transition-all duration-500"
              style={{ width: `${stats.percentage}%` }}
            />
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="px-6 py-3 border-b border-slate-100 flex items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            checked={showPartialMatches}
            onChange={(e) => setShowPartialMatches(e.target.checked)}
            className="rounded border-slate-300 text-primary focus:ring-primary"
          />
          Show partial matches
        </label>

        <div className="flex items-center gap-3 text-xs">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-green-500" />
            Exact match
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-yellow-500" />
            Partial match
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 rounded bg-red-500" />
            Missing
          </span>
        </div>
      </div>

      {/* Content */}
      {viewMode === "inline" ? (
        <InlineView skillMatches={skillMatches} getMatchColor={getMatchColor} getMatchIcon={getMatchIcon} />
      ) : (
        <SideBySideView
          jobDescription={jobDescription}
          resumeText={resumeText}
          skillMatches={skillMatches}
          getMatchColor={getMatchColor}
          getMatchIcon={getMatchIcon}
        />
      )}

      {/* Footer */}
      <div className="px-6 py-4 bg-slate-50 border-t border-slate-100">
        <p className="text-sm text-slate-600">
          💡 <span className="font-medium">Tip:</span> Focus on addressing missing skills in your resume
          to improve your match score.
        </p>
      </div>
    </div>
  );
}

function InlineView({
  skillMatches,
  getMatchColor,
  getMatchIcon,
}: {
  skillMatches: SkillMatch[];
  getMatchColor: (match: SkillMatch) => string;
  getMatchIcon: (match: SkillMatch) => string;
}) {
  return (
    <div className="p-6">
      <div className="flex flex-wrap gap-2">
        {skillMatches.map((match, index) => (
          <div
            key={index}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border ${getMatchColor(
              match
            )} text-sm font-medium`}
          >
            <MaterialSymbol symbol={getMatchIcon(match)} size={16} />
            <span className="capitalize">{match.skill}</span>
            {match.confidence && match.confidence < 1.0 && (
              <span className="text-xs opacity-70">({Math.round(match.confidence * 100)}%)</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

function SideBySideView({
  jobDescription,
  resumeText,
  skillMatches,
  getMatchColor,
  getMatchIcon,
}: {
  jobDescription: string;
  resumeText: string;
  skillMatches: SkillMatch[];
  getMatchColor: (match: SkillMatch) => string;
  getMatchIcon: (match: SkillMatch) => string;
}) {
  const matchedSkills = skillMatches.filter((m) => m.matched).map((m) => m.skill.toLowerCase());
  const missingSkills = skillMatches.filter((m) => !m.matched).map((m) => m.skill.toLowerCase());

  // Highlight matching skills in job description
  const highlightJobSkills = (text: string) => {
    let highlighted = text;
    matchedSkills.forEach((skill) => {
      const regex = new RegExp(`\\b(${skill})\\b`, "gi");
      highlighted = highlighted.replace(
        regex,
        '<mark class="bg-green-200 text-green-800 rounded px-0.5 font-medium">$1</mark>'
      );
    });
    missingSkills.forEach((skill) => {
      const regex = new RegExp(`\\b(${skill})\\b`, "gi");
      highlighted = highlighted.replace(
        regex,
        '<mark class="bg-red-200 text-red-800 rounded px-0.5 font-medium">$1</mark>'
      );
    });
    return highlighted;
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 divide-y lg:divide-y-0 lg:divide-x divide-slate-200">
      {/* Job Description Column */}
      <div className="p-6">
        <h4 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
          <MaterialSymbol symbol="work_outline" size={20} className="text-primary" />
          Job Description
        </h4>
        <div
          className="prose prose-sm max-w-none text-slate-700 leading-relaxed"
          dangerouslySetInnerHTML={{ __html: highlightJobSkills(jobDescription) }}
        />

        {/* Missing Skills Summary */}
        {missingSkills.length > 0 && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm font-semibold text-red-900 mb-2">Missing Skills</p>
            <div className="flex flex-wrap gap-1.5">
              {missingSkills.map((skill, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium capitalize"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Resume Column */}
      <div className="p-6">
        <h4 className="font-bold text-slate-900 mb-4 flex items-center gap-2">
          <MaterialSymbol symbol="description" size={20} className="text-primary" />
          Resume
        </h4>
        <p className="prose prose-sm max-w-none text-slate-700 leading-relaxed whitespace-pre-wrap">
          {resumeText}
        </p>

        {/* Matched Skills Summary */}
        {matchedSkills.length > 0 && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-sm font-semibold text-green-900 mb-2">Matched Skills</p>
            <div className="flex flex-wrap gap-1.5">
              {matchedSkills.map((skill, i) => (
                <span
                  key={i}
                  className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium capitalize"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
