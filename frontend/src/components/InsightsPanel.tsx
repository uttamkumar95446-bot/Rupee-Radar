import { useState } from "react";
import {
  AlertTriangle,
  Lightbulb,
  TrendingUp,
  Info,
  Copy,
  Check,
} from "lucide-react";
import type { Insight } from "../types";
import { formatINR } from "../utils/format";

interface InsightsPanelProps {
  insights: Insight[];
  loading?: boolean;
}

const severityConfig: Record<
  string,
  { border: string; bg: string; icon: typeof Lightbulb }
> = {
  positive: {
    border: "border-l-emerald-500",
    bg: "bg-emerald-50",
    icon: TrendingUp,
  },
  warning: {
    border: "border-l-amber-500",
    bg: "bg-amber-50",
    icon: AlertTriangle,
  },
  info: {
    border: "border-l-blue-500",
    bg: "bg-blue-50",
    icon: Info,
  },
};

export default function InsightsPanel({
  insights,
  loading,
}: InsightsPanelProps) {
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);

  const copyToClipboard = async (insight: Insight, index: number) => {
    const text = `${insight.title}: ${insight.description}${
      insight.amount !== null ? ` (₹${formatINR(insight.amount)})` : ""
    }`;
    try {
      await navigator.clipboard.writeText(text);
      setCopiedIndex(index);
      setTimeout(() => setCopiedIndex(null), 2000);
    } catch {
      // Clipboard API not available
    }
  };

  if (loading) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 animate-pulse">
        <div className="h-5 w-32 bg-gray-200 rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 bg-gray-100 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!insights || insights.length === 0) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          AI Insights
        </h3>
        <p className="text-sm text-gray-400">No insights available yet.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">AI Insights</h3>
        <Lightbulb className="h-4 w-4 text-amber-500" />
      </div>

      <div className="space-y-3">
        {insights.map((insight, i) => {
          const config = severityConfig[insight.severity] ?? severityConfig.info;
          const Icon = config.icon;
          return (
            <div
              key={i}
              className={`group relative rounded-r-lg border-l-4 ${config.border} ${config.bg} p-4 transition-shadow hover:shadow-sm`}
            >
              <button
                onClick={() => copyToClipboard(insight, i)}
                className="absolute right-3 top-3 rounded-md p-1.5 text-gray-400 opacity-0 transition-all hover:bg-white hover:text-gray-600 group-hover:opacity-100"
                title="Copy insight"
                aria-label="Copy insight to clipboard"
              >
                {copiedIndex === i ? (
                  <Check className="h-3.5 w-3.5 text-emerald-500" />
                ) : (
                  <Copy className="h-3.5 w-3.5" />
                )}
              </button>
              <div className="flex items-start gap-3">
                <Icon className="mt-0.5 h-4 w-4 shrink-0 text-gray-500" />
                <div className="pr-6">
                  <p className="text-sm font-semibold text-gray-800">
                    {insight.title}
                  </p>
                  <p className="mt-1 text-sm text-gray-600 leading-relaxed">
                    {insight.description}
                  </p>
                  {insight.amount !== null && (
                    <p className="mt-1 text-sm font-bold text-gray-800">
                      ₹{formatINR(insight.amount)}
                    </p>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
