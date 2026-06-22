import { useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Sector,
} from "recharts";
import { CATEGORY_COLORS } from "../types";
import type { CategorySpend } from "../types";
import { formatINR } from "../utils/format";

interface CategoryBreakdownProps {
  categories: CategorySpend[];
  loading?: boolean;
}

// Custom shape for pie sectors — Recharts v3 uses `shape` prop with `isActive` flag
function renderCustomShape(props: any) {
  const {
    cx,
    cy,
    innerRadius,
    outerRadius,
    startAngle,
    endAngle,
    fill,
    isActive,
  } = props;

  return (
    <Sector
      cx={cx}
      cy={cy}
      innerRadius={innerRadius}
      outerRadius={isActive ? outerRadius + 6 : outerRadius}
      startAngle={startAngle}
      endAngle={endAngle}
      fill={fill}
      stroke={isActive ? "#1F2937" : "none"}
      strokeWidth={isActive ? 2 : 0}
    />
  );
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean;
  payload?: { name: string; value: number; payload: CategorySpend }[];
}) => {
  if (!active || !payload || payload.length === 0) return null;
  const entry = payload[0];
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
      <div className="flex items-center gap-2 mb-1">
        <span
          className="inline-block h-2.5 w-2.5 rounded-full"
          style={{
            backgroundColor:
              CATEGORY_COLORS[entry.payload.category] ?? "#9E9E9E",
          }}
        />
        <span className="text-xs font-semibold text-gray-700">
          {entry.payload.category}
        </span>
      </div>
      <p className="text-xs text-gray-500">
        ₹{formatINR(entry.value)} ({entry.payload.percentage.toFixed(1)}% of
        spend, {entry.payload.transaction_count} txns)
      </p>
    </div>
  );
};

export default function CategoryBreakdown({
  categories,
  loading,
}: CategoryBreakdownProps) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  if (loading) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 animate-pulse">
        <div className="h-5 w-40 bg-gray-200 rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-8 bg-gray-100 rounded" />
          ))}
        </div>
      </div>
    );
  }

  if (!categories || categories.length === 0) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Spending by Category
        </h3>
        <p className="text-sm text-gray-400">No category data available.</p>
      </div>
    );
  }

  const total = categories.reduce((s, c) => s + c.amount, 0);

  const handlePieClick = (_: unknown, index: number) => {
    const cat = categories[index].category;
    setSelectedCategory(selectedCategory === cat ? null : cat);
  };

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">
        Spending by Category
      </h3>

      {/* Donut chart + bar chart side by side */}
      <div className="grid gap-4 sm:grid-cols-2">
        {/* Donut chart — Recharts v3 uses `shape` prop with `isActive` flag */}
        <div className="h-48 sm:h-52">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={categories}
                dataKey="amount"
                nameKey="category"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={72}
                shape={renderCustomShape}
                onClick={handlePieClick}
                cursor="pointer"
              >
                {categories.map((entry) => (
                  <Cell
                    key={entry.category}
                    fill={CATEGORY_COLORS[entry.category] ?? "#9E9E9E"}
                    opacity={
                      selectedCategory && selectedCategory !== entry.category
                        ? 0.4
                        : 1
                    }
                    stroke={
                      selectedCategory === entry.category ? "#1F2937" : "none"
                    }
                    strokeWidth={selectedCategory === entry.category ? 2 : 0}
                  />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Bar list */}
        <div className="space-y-2.5">
          {categories.map((cat) => {
            const pct = total > 0 ? (cat.amount / total) * 100 : 0;
            const color = CATEGORY_COLORS[cat.category] ?? "#9E9E9E";
            const isSelected =
              !selectedCategory || selectedCategory === cat.category;
            return (
              <button
                key={cat.category}
                onClick={() =>
                  setSelectedCategory(
                    selectedCategory === cat.category ? null : cat.category
                  )
                }
                className={`w-full text-left transition-opacity ${
                  isSelected ? "opacity-100" : "opacity-40"
                }`}
              >
                <div className="flex items-center justify-between text-xs mb-1">
                  <div className="flex items-center gap-2">
                    <span
                      className="inline-block h-2.5 w-2.5 rounded-full"
                      style={{ backgroundColor: color }}
                    />
                    <span className="font-medium text-gray-700">
                      {cat.category}
                    </span>
                  </div>
                  <span className="text-gray-500">
                    ₹{formatINR(cat.amount)} ({pct.toFixed(1)}%)
                  </span>
                </div>
                <div className="h-2 w-full rounded-full bg-gray-100 overflow-hidden">
                  <div
                    className="h-full rounded-full transition-all duration-500"
                    style={{ width: `${pct}%`, backgroundColor: color }}
                  />
                </div>
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
