import { TrendingUp, TrendingDown, PiggyBank, Percent } from "lucide-react";
import type { FinancialMetrics } from "../types";
import { formatINR } from "../utils/format";
import { useCountUp } from "../hooks/useCountUp";

interface SpendSummaryProps {
  metrics: FinancialMetrics | null;
  loading?: boolean;
}

function AnimatedNumber({
  value,
  prefix = "",
  className,
}: {
  value: number;
  prefix?: string;
  className?: string;
}) {
  const animated = useCountUp(value);
  const display = formatINR(animated);

  return (
    <p className={`text-2xl font-bold ${className ?? ""}`}>
      {prefix}
      {display}
    </p>
  );
}

export default function SpendSummary({ metrics, loading }: SpendSummaryProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 animate-pulse"
          >
            <div className="h-4 w-20 bg-gray-200 rounded mb-3" />
            <div className="h-8 w-28 bg-gray-200 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!metrics) return null;

  const cards = [
    {
      label: "Total Income",
      value: metrics.total_income,
      prefix: "₹",
      icon: TrendingUp,
      color: "text-emerald-600",
      bg: "bg-emerald-50",
      iconColor: "text-emerald-600",
      animated: true,
    },
    {
      label: "Total Spend",
      value: metrics.total_spend,
      prefix: "₹",
      icon: TrendingDown,
      color: "text-red-600",
      bg: "bg-red-50",
      iconColor: "text-red-600",
      animated: true,
    },
    {
      label: "Savings",
      value: metrics.savings,
      prefix: "₹",
      icon: PiggyBank,
      color: metrics.savings >= 0 ? "text-blue-600" : "text-red-600",
      bg: metrics.savings >= 0 ? "bg-blue-50" : "bg-red-50",
      iconColor: metrics.savings >= 0 ? "text-blue-600" : "text-red-600",
      animated: true,
    },
    {
      label: "Savings Rate",
      // Not animated — preserves decimal precision (e.g., "7.2%")
      display: `${metrics.savings_rate.toFixed(1)}%`,
      icon: Percent,
      color: metrics.savings_rate >= 20 ? "text-emerald-600" : "text-amber-600",
      bg: metrics.savings_rate >= 20 ? "bg-emerald-50" : "bg-amber-50",
      iconColor:
        metrics.savings_rate >= 20 ? "text-emerald-600" : "text-amber-600",
    },
  ];

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 hover:shadow-md transition-all duration-200 hover:-translate-y-0.5"
        >
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">
              {card.label}
            </span>
            <div className={`rounded-lg p-2 ${card.bg}`}>
              <card.icon className={`h-4 w-4 ${card.iconColor}`} />
            </div>
          </div>
          {"animated" in card && card.animated ? (
            <AnimatedNumber
              value={card.value!}
              prefix={card.prefix!}
              className={card.color}
            />
          ) : (
            <p className={`text-2xl font-bold ${card.color}`}>
              {card.display}
            </p>
          )}
        </div>
      ))}
    </div>
  );
}
