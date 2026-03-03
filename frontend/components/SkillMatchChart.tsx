"use client";

import { useEffect, useRef } from "react";
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
  ChartOptions,
} from "chart.js";
import { Radar } from "react-chartjs-2";

// Register Chart.js components
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
);

interface SkillMatchChartProps {
  exactMatch: number;
  similarityMatch: number;
  achievementImpact: number;
  ownership: number;
  className?: string;
}

export default function SkillMatchChart({
  exactMatch,
  similarityMatch,
  achievementImpact,
  ownership,
  className = "",
}: SkillMatchChartProps) {
  const chartRef = useRef<any>(null);

  const data = {
    labels: [
      "Exact Match",
      "Semantic Match",
      "Achievement Impact",
      "Project Ownership",
    ],
    datasets: [
      {
        label: "Skill Match Score",
        data: [exactMatch, similarityMatch, achievementImpact, ownership],
        backgroundColor: "rgba(59, 130, 246, 0.2)",
        borderColor: "rgba(59, 130, 246, 1)",
        borderWidth: 2,
        pointBackgroundColor: "rgba(59, 130, 246, 1)",
        pointBorderColor: "#fff",
        pointHoverBackgroundColor: "#fff",
        pointHoverBorderColor: "rgba(59, 130, 246, 1)",
        pointRadius: 4,
        pointHoverRadius: 6,
      },
    ],
  };

  const options: ChartOptions<"radar"> = {
    responsive: true,
    maintainAspectRatio: true,
    scales: {
      r: {
        angleLines: {
          color: "rgba(0, 0, 0, 0.1)",
        },
        grid: {
          color: "rgba(0, 0, 0, 0.1)",
        },
        pointLabels: {
          font: {
            size: 12,
            weight: 600 as const,
            family: "'Inter', sans-serif",
          },
          color: "#475569",
        },
        ticks: {
          backdropColor: "transparent",
          color: "#94a3b8",
          font: {
            size: 10,
          },
          stepSize: 20,
        },
        min: 0,
        max: 100,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        backgroundColor: "rgba(15, 23, 42, 0.9)",
        titleFont: {
          size: 13,
          weight: 600 as const,
        },
        bodyFont: {
          size: 12,
        },
        padding: 12,
        cornerRadius: 8,
        displayColors: false,
        callbacks: {
          label: function (context) {
            return `Score: ${context.parsed.r}/100`;
          },
        },
      },
    },
    animation: {
      duration: 1000,
      easing: "easeInOutQuart" as const,
    },
  };

  return (
    <div className={`skill-match-chart ${className}`}>
      <div className="w-full max-w-[280px] mx-auto">
        <Radar ref={chartRef} data={data} options={options} />
      </div>
    </div>
  );
}
