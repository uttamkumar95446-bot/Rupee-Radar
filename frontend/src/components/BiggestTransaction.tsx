import { TrendingUp, TrendingDown, Calendar, Building2 } from "lucide-react";
import type { Transaction, FinancialMetrics } from "../types";
import { CATEGORY_COLORS } from "../types";
import { formatINR } from "../utils/format";

interface BiggestTransactionProps {
  metrics: FinancialMetrics | null;
  loading?: boolean;
}

function TransactionCard({
  txn,
  type,
}: {
  txn: Transaction;
  type: "credit" | "debit";
}) {
  const isCredit = type === "credit";
  const borderColor = isCredit ? "border-l-emerald-500" : "border-l-red-500";
  const bgColor = isCredit ? "bg-emerald-50/50" : "bg-red-50/50";
  const iconBg = isCredit ? "bg-emerald-100" : "bg-red-100";
  const iconColor = isCredit ? "text-emerald-600" : "text-red-600";
  const Icon = isCredit ? TrendingUp : TrendingDown;

  return (
    <div
      className={`rounded-lg border-l-4 ${borderColor} ${bgColor} p-4 transition-shadow hover:shadow-md`}
    >
      <div className="flex items-start gap-3">
        <div className={`rounded-lg p-2 ${iconBg}`}>
          <Icon className={`h-5 w-5 ${iconColor}`} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">
            Biggest {isCredit ? "Credit" : "Debit"}
          </p>
          <p className="text-sm font-semibold text-gray-800 truncate">
            {txn.description}
          </p>
          <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-gray-500">
            {txn.merchant && (
              <span className="flex items-center gap-1">
                <Building2 className="h-3 w-3" />
                {txn.merchant}
              </span>
            )}
            <span className="flex items-center gap-1">
              <Calendar className="h-3 w-3" />
              {txn.date}
            </span>
            {txn.category && (
              <span
                className="rounded-full px-2 py-0.5 text-xs font-medium"
                style={{
                  backgroundColor: `${getCategoryColor(txn.category)}20`,
                  color: getCategoryColor(txn.category),
                }}
              >
                {txn.category}
              </span>
            )}
          </div>
        </div>
        <p
          className={`text-lg font-bold shrink-0 ${
            isCredit ? "text-emerald-600" : "text-red-600"
          }`}
        >
          {isCredit ? "+" : "-"}₹{formatINR(txn.amount)}
        </p>
      </div>
    </div>
  );
}

function getCategoryColor(cat: string): string {
  return CATEGORY_COLORS[cat] ?? "#9E9E9E";
}

export default function BiggestTransaction({
  metrics,
  loading,
}: BiggestTransactionProps) {
  if (loading) {
    return (
      <div className="grid gap-4 sm:grid-cols-2">
        {[1, 2].map((i) => (
          <div
            key={i}
            className="h-24 rounded-xl bg-white p-5 shadow-sm border border-gray-100 animate-pulse"
          >
            <div className="h-4 w-24 bg-gray-200 rounded mb-3" />
            <div className="h-4 w-40 bg-gray-100 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (
    !metrics ||
    (!metrics.biggest_transaction && !metrics.biggest_credit)
  ) {
    return null;
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2">
      {metrics.biggest_credit && (
        <TransactionCard txn={metrics.biggest_credit} type="credit" />
      )}
      {metrics.biggest_transaction &&
        (!metrics.biggest_credit ||
          metrics.biggest_transaction.id !== metrics.biggest_credit.id) && (
          <TransactionCard txn={metrics.biggest_transaction} type="debit" />
        )}
    </div>
  );
}
