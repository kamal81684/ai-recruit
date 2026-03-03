/**
 * Evaluation Breakdown Component
 *
 * This component provides detailed visualization of AI evaluation scores
 * with explanations, highlighting the key factors that influenced the
 * candidate's ranking.
 *
 * Features:
 * - Visual score indicators with color coding
 * - Detailed explanations for each dimension
 * - Animated progress bars
 * - Tier-based styling
 * - Skill matching visualization
 *
 * Contributor: shubham21155102
 */

"use client";

import React from 'react';

interface EvaluationScore {
  score: number;
  explanation: string;
}

interface EvaluationBreakdownProps {
  exactMatch: EvaluationScore;
  similarityMatch: EvaluationScore;
  achievementImpact: EvaluationScore;
  ownership: EvaluationScore;
  tier: string;
  summary: string;
  matchedKeywords?: string[];
}

const ScoreCard: React.FC<{
  title: string;
  score: EvaluationScore;
  icon: string;
  color: string;
}> = ({ title, score, icon, color }) => {
  const getScoreColor = (value: number) => {
    if (value >= 80) return 'bg-emerald-500';
    if (value >= 60) return 'bg-blue-500';
    if (value >= 40) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  const getScoreLabel = (value: number) => {
    if (value >= 80) return 'Excellent';
    if (value >= 60) return 'Good';
    if (value >= 40) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="material-symbols-outlined text-lg" style={{ color }}>
            {icon}
          </span>
          <h3 className="font-semibold text-slate-800">{title}</h3>
        </div>
        <div className="flex items-center gap-2">
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${getScoreColor(score.score)} text-white`}>
            {getScoreLabel(score.score)}
          </span>
        </div>
      </div>

      {/* Score Progress Bar */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-2xl font-bold text-slate-800">{score.score}</span>
          <span className="text-xs text-slate-500">/ 100</span>
        </div>
        <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
          <div
            className={`h-full ${getScoreColor(score.score)} transition-all duration-500 ease-out`}
            style={{ width: `${score.score}%` }}
          />
        </div>
      </div>

      {/* Explanation */}
      <p className="text-sm text-slate-600 leading-relaxed">{score.explanation}</p>
    </div>
  );
};

const TierBadge: React.FC<{ tier: string }> = ({ tier }) => {
  const getTierConfig = (tier: string) => {
    switch (tier) {
      case 'Tier A':
        return {
          bg: 'bg-emerald-100',
          text: 'text-emerald-800',
          icon: 'verified',
          label: 'Top Tier',
        };
      case 'Tier B':
        return {
          bg: 'bg-blue-100',
          text: 'text-blue-800',
          icon: 'trending_up',
          label: 'Good Match',
        };
      case 'Tier C':
        return {
          bg: 'bg-slate-100',
          text: 'text-slate-800',
          icon: 'info',
          label: 'Needs Review',
        };
      default:
        return {
          bg: 'bg-slate-100',
          text: 'text-slate-800',
          icon: 'help',
          label: 'Unknown',
        };
    }
  };

  const config = getTierConfig(tier);

  return (
    <div className={`inline-flex items-center gap-2 px-4 py-2 rounded-full ${config.bg} ${config.text}`}>
      <span className="material-symbols-outlined text-sm">{config.icon}</span>
      <span className="font-semibold text-sm">{config.label}</span>
    </div>
  );
};

export const EvaluationBreakdown: React.FC<EvaluationBreakdownProps> = ({
  exactMatch,
  similarityMatch,
  achievementImpact,
  ownership,
  tier,
  summary,
  matchedKeywords = [],
}) => {
  const getOverallScore = () => {
    const scores = [exactMatch.score, similarityMatch.score, achievementImpact.score, ownership.score];
    return Math.round(scores.reduce((a, b) => a + b, 0) / scores.length);
  };

  const overallScore = getOverallScore();

  return (
    <div className="space-y-6">
      {/* Header with Tier and Overall Score */}
      <div className="bg-gradient-to-r from-primary to-primary/80 p-6 rounded-xl text-white">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <TierBadge tier={tier} />
            </div>
            <p className="text-white/90 text-sm mt-2">{summary}</p>
          </div>
          <div className="text-right">
            <div className="text-5xl font-bold">{overallScore}</div>
            <div className="text-white/80 text-sm">Overall Score</div>
          </div>
        </div>
      </div>

      {/* Score Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <ScoreCard
          title="Exact Match"
          score={exactMatch}
          icon="check_circle"
          color="#10b981"
        />
        <ScoreCard
          title="Similarity Match"
          score={similarityMatch}
          icon="psychology"
          color="#6366f1"
        />
        <ScoreCard
          title="Achievement & Impact"
          score={achievementImpact}
          icon="military_tech"
          color="#f59e0b"
        />
        <ScoreCard
          title="Ownership"
          score={ownership}
          icon="engineering"
          color="#8b5cf6"
        />
      </div>

      {/* AI Reasoning Summary */}
      <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
        <div className="flex items-center gap-2 mb-3">
          <span className="material-symbols-outlined text-primary">lightbulb</span>
          <h3 className="font-semibold text-slate-800">AI Reasoning</h3>
        </div>
        <p className="text-sm text-slate-600 leading-relaxed">
          This evaluation is based on a comprehensive analysis of the candidate's resume
          against the job description. The scores reflect multiple dimensions including
          direct skill matches, semantic similarities, quantifiable achievements, and
          indicators of leadership and ownership.
        </p>
      </div>

      {/* Matched Keywords (if available) */}
      {matchedKeywords.length > 0 && (
        <div className="bg-slate-50 p-5 rounded-xl border border-slate-200">
          <div className="flex items-center gap-2 mb-3">
            <span className="material-symbols-outlined text-primary">tag</span>
            <h3 className="font-semibold text-slate-800">Matched Keywords</h3>
          </div>
          <div className="flex flex-wrap gap-2">
            {matchedKeywords.map((keyword, index) => (
              <span
                key={index}
                className="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium bg-primary/10 text-primary"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default EvaluationBreakdown;
