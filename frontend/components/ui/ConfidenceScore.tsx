/**
 * AI Confidence Score Component
 *
 * This component displays AI confidence scores for evaluation results,
 * providing transparency about the reliability of AI-generated assessments.
 *
 * Features:
 * - Visual confidence indicators (color-coded)
 * - Detailed confidence breakdown
 * - Tooltip explanations
 * - Animated score display
 * - Responsive design
 *
 * Contributor: shubham21155102
 */

"use client";

import { useState, useEffect } from "react";

interface ConfidenceScoreProps {
  confidence: number; // 0-100
  label?: string;
  size?: "sm" | "md" | "lg";
  showLabel?: boolean;
  animated?: boolean;
  variant?: "default" | "compact" | "detailed";
}

interface ConfidenceBreakdown {
  category: string;
  score: number;
  weight: number;
}

export function ConfidenceScore({
  confidence,
  label = "AI Confidence",
  size = "md",
  showLabel = true,
  animated = true,
  variant = "default",
}: ConfidenceScoreProps) {
  const [displayScore, setDisplayScore] = useState(0);

  useEffect(() => {
    if (animated) {
      const duration = 1000;
      const steps = 30;
      const stepDuration = duration / steps;
      const increment = confidence / steps;

      let currentStep = 0;
      const interval = setInterval(() => {
        currentStep++;
        setDisplayScore(Math.min(Math.round(increment * currentStep), confidence));

        if (currentStep >= steps) {
          clearInterval(interval);
          setDisplayScore(confidence);
        }
      }, stepDuration);

      return () => clearInterval(interval);
    } else {
      setDisplayScore(confidence);
    }
  }, [confidence, animated]);

  const getConfidenceLevel = (score: number): { level: string; color: string; bgColor: string; textColor: string } => {
    if (score >= 90) {
      return {
        level: "Very High",
        color: "text-emerald-600",
        bgColor: "bg-emerald-50",
        textColor: "text-emerald-700",
      };
    } else if (score >= 75) {
      return {
        level: "High",
        color: "text-green-600",
        bgColor: "bg-green-50",
        textColor: "text-green-700",
      };
    } else if (score >= 60) {
      return {
        level: "Moderate",
        color: "text-amber-600",
        bgColor: "bg-amber-50",
        textColor: "text-amber-700",
      };
    } else if (score >= 40) {
      return {
        level: "Low",
        color: "text-orange-600",
        bgColor: "bg-orange-50",
        textColor: "text-orange-700",
      };
    } else {
      return {
        level: "Very Low",
        color: "text-red-600",
        bgColor: "bg-red-50",
        textColor: "text-red-700",
      };
    }
  };

  const confidenceLevel = getConfidenceLevel(confidence);

  const sizeClasses = {
    sm: {
      container: "w-20 h-20",
      text: "text-xl",
      label: "text-xs",
      ring: "stroke-2",
    },
    md: {
      container: "w-28 h-28",
      text: "text-2xl",
      label: "text-sm",
      ring: "stroke-3",
    },
    lg: {
      container: "w-36 h-36",
      text: "text-4xl",
      label: "text-base",
      ring: "stroke-4",
    },
  };

  const circumference = 2 * Math.PI * 45; // r=45
  const offset = circumference - (displayScore / 100) * circumference;

  if (variant === "compact") {
    return (
      <div className={`flex items-center gap-2 ${confidenceLevel.bgColor} px-3 py-1.5 rounded-full`}>
        <div className={`w-2 h-2 rounded-full animate-pulse ${confidenceLevel.color.replace('text-', 'bg-')}`} />
        <span className={`text-sm font-semibold ${confidenceLevel.textColor}`}>
          {displayScore}% confidence
        </span>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center gap-3">
      {/* Circular Progress */}
      <div className={`relative ${sizeClasses[size].container}`}>
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
          {/* Background circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            className="stroke-slate-100"
            strokeWidth="8"
          />
          {/* Progress circle */}
          <circle
            cx="50"
            cy="50"
            r="45"
            fill="none"
            className={`${confidenceLevel.color} transition-all duration-500 ease-out`}
            strokeWidth="8"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            strokeLinecap="round"
          />
        </svg>

        {/* Center content */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className={`font-black ${sizeClasses[size].text} ${confidenceLevel.color}`}>
            {displayScore}%
          </span>
          {showLabel && size !== "sm" && (
            <span className={`font-medium ${sizeClasses[size].label} text-slate-500`}>
              {label}
            </span>
          )}
        </div>
      </div>

      {/* Confidence Level Badge */}
      <div className={`${confidenceLevel.bgColor} ${confidenceLevel.textColor} px-4 py-1.5 rounded-full`}>
        <span className="text-sm font-semibold">{confidenceLevel.level} Confidence</span>
      </div>

      {/* Helper text */}
      {variant === "detailed" && (
        <p className="text-xs text-slate-500 text-center max-w-xs leading-relaxed">
          This score indicates how reliable the AI assessment is based on data quality
          and clarity of information.
        </p>
      )}
    </div>
  );
}

interface ConfidenceBreakdownProps {
  breakdown: ConfidenceBreakdown[];
}

export function ConfidenceBreakdown({ breakdown }: ConfidenceBreakdownProps) {
  const overallConfidence = Math.round(
    breakdown.reduce((sum, item) => sum + item.score * item.weight, 0) /
    breakdown.reduce((sum, item) => sum + item.weight, 0)
  );

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-slate-900">Confidence Breakdown</h3>
        <ConfidenceScore confidence={overallConfidence} size="sm" variant="compact" />
      </div>

      <div className="space-y-4">
        {breakdown.map((item, index) => {
          const level = item.score >= 75 ? "High" : item.score >= 60 ? "Moderate" : "Low";
          const levelColor = item.score >= 75 ? "text-emerald-600" : item.score >= 60 ? "text-amber-600" : "text-orange-600";
          const barColor = item.score >= 75 ? "bg-emerald-500" : item.score >= 60 ? "bg-amber-500" : "bg-orange-500";

          return (
            <div key={index} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700">{item.category}</span>
                <div className="flex items-center gap-2">
                  <span className={`text-xs font-semibold ${levelColor}`}>{level}</span>
                  <span className="text-sm font-bold text-slate-900">{item.score}%</span>
                </div>
              </div>
              <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
                <div
                  className={`h-full ${barColor} transition-all duration-500`}
                  style={{ width: `${item.score}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Confidence info */}
      <div className="mt-6 pt-4 border-t border-slate-100">
        <div className="flex items-start gap-2">
          <span className="material-symbols-outlined text-slate-400 text-sm mt-0.5">info</span>
          <p className="text-xs text-slate-500 leading-relaxed">
            Confidence scores are calculated based on data completeness, pattern matches,
            and information clarity. Higher confidence indicates more reliable assessments.
          </p>
        </div>
      </div>
    </div>
  );
}

interface ConfidenceTooltipProps {
  score: number;
  children: React.ReactNode;
}

export function ConfidenceTooltip({ score, children }: ConfidenceTooltipProps) {
  const [show, setShow] = useState(false);

  const getConfidenceMessage = (score: number): string => {
    if (score >= 90) return "Very reliable - Based on comprehensive, clear data";
    if (score >= 75) return "Reliable - Based on substantial matching data";
    if (score >= 60) return "Moderately reliable - Some ambiguity in data";
    if (score >= 40) return "Lower reliability - Limited or unclear data";
    return "Low reliability - Insufficient data for assessment";
  };

  return (
    <div className="relative inline-block">
      <div
        onMouseEnter={() => setShow(true)}
        onMouseLeave={() => setShow(false)}
        className="cursor-help"
      >
        {children}
      </div>

      {show && (
        <div className="absolute z-50 w-64 p-3 bg-slate-900 text-white text-xs rounded-lg shadow-xl -top-full left-1/2 -translate-x-1/2 mb-2">
          <div className="font-semibold mb-1">AI Confidence: {score}%</div>
          <div className="text-slate-300">{getConfidenceMessage(score)}</div>
          {/* Arrow */}
          <div className="absolute -bottom-1 left-1/2 -translate-x-1/2 w-2 h-2 bg-slate-900 rotate-45" />
        </div>
      )}
    </div>
  );
}

// Confidence Legend Component
export function ConfidenceLegend() {
  const levels = [
    { label: "Very High", range: "90-100%", color: "bg-emerald-500", description: "Highly reliable" },
    { label: "High", range: "75-89%", color: "bg-green-500", description: "Reliable" },
    { label: "Moderate", range: "60-74%", color: "bg-amber-500", description: "Some uncertainty" },
    { label: "Low", range: "40-59%", color: "bg-orange-500", description: "Limited confidence" },
    { label: "Very Low", range: "0-39%", color: "bg-red-500", description: "Insufficient data" },
  ];

  return (
    <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
      <h4 className="text-sm font-bold text-slate-900 mb-3">Confidence Score Guide</h4>
      <div className="space-y-2">
        {levels.map((level, index) => (
          <div key={index} className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${level.color}`} />
            <div className="flex-1">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-slate-700">{level.label}</span>
                <span className="text-xs text-slate-500">{level.range}</span>
              </div>
              <p className="text-xs text-slate-500">{level.description}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
