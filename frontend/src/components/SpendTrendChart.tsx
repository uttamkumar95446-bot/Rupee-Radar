import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { Transaction } from "../types";
import { formatINR } from "../utils/format";

interface SpendTrendChartProps {
  transactions: Transaction[];
  loading?: boolean;
}

/** Group transactions by month and return income/spend totals. */
function computeMonthlyData(transactions: Transaction[]) {
  const monthMap: Record<string, { income: number; spend: number }> = {};

  for (const txn of transactions) {
    // Extract YYYY-MM from date
    const month = txn.date.slice(0, 7);
    if (!monthMap[month]) {
      monthMap[month] = { income: 0, spend: 0 };
    }
    if (txn.txn_type === "credit") {
      monthMap[month].income += txn.amount;
    } else {
      monthMap[month].spend += txn.amount;
    }
  }

  // Sort chronologically and format labels
  const sortedMonths = Object.keys(monthMap).sort();
  return sortedMonths.map((month) => {
    const [y, m] = month.split("-");
    const monthNames = [
      "Jan", "Feb", "Mar", "Apr", "May", "Jun",
      "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
    ];
    const label = `${monthNames[parseInt(m, 10) - 1]} ${y.slice(2)}`;
    return {
      month: label,
      income: Math.round(monthMap[month].income),
      spend: Math.round(monthMap[month].spend),
    };
  });
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: { name: string; value: number }[];
  label?: string;
}) => {
  if (!active || !payload || !label) return null;
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-3 shadow-lg">
      <p className="text-xs font-semibold text-gray-600 mb-2">{label}</p>
      {payload.map((entry) => (
        <div key={entry.name} className="flex items-center justify-between gap-4 text-xs">
          <span
            className={`font-medium ${
              entry.name === "income" ? "text-emerald-600" : "text-red-500"
            }`}
          >
            {entry.name === "income" ? "Income" : "Spend"}
          </span>
          <span className="font-bold text-gray-800">
            ₹{formatINR(entry.value)}
          </span>
        </div>
      ))}
    </div>
  );
};

export default function SpendTrendChart({
  transactions,
  loading,
}: SpendTrendChartProps) {
  if (loading) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 animate-pulse">
        <div className="h-5 w-40 bg-gray-200 rounded mb-4" />
        <div className="h-48 bg-gray-100 rounded" />
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Spending Trend
        </h3>
        <p className="text-sm text-gray-400">No data to visualize.</p>
      </div>
    );
  }

  const data = computeMonthlyData(transactions);

  if (data.length === 0) {
    return null;
  }

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <h3 className="text-sm font-semibold text-gray-700 mb-4">
        Income vs Spend Over Time
      </h3>
      <div className="h-56 sm:h-64">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 5, right: 10, left: 0, bottom: 5 }}
          >
            <defs>
              <linearGradient id="incomeGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10B981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10B981" stopOpacity={0} />
              </linearGradient>
              <linearGradient id="spendGrad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#EF4444" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="month"
              tick={{ fontSize: 11, fill: "#9CA3AF" }}
              axisLine={{ stroke: "#E5E7EB" }}
              tickLine={false}
            />
            <YAxis
              tick={{ fontSize: 11, fill: "#9CA3AF" }}
              axisLine={false}
              tickLine={false}
              tickFormatter={(v: number) => `₹${(v / 1000).toFixed(0)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Legend
              wrapperStyle={{ fontSize: 12, paddingTop: 8 }}
              formatter={(value: string) =>
                value === "income" ? "Income" : "Spend"
              }
            />
            <Area
              type="monotone"
              dataKey="income"
              stroke="#10B981"
              strokeWidth={2}
              fill="url(#incomeGrad)"
              dot={{ r: 3, fill: "#10B981" }}
              activeDot={{ r: 5, stroke: "#10B981", strokeWidth: 2 }}
            />
            <Area
              type="monotone"
              dataKey="spend"
              stroke="#EF4444"
              strokeWidth={2}
              fill="url(#spendGrad)"
              dot={{ r: 3, fill: "#EF4444" }}
              activeDot={{ r: 5, stroke: "#EF4444", strokeWidth: 2 }}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
