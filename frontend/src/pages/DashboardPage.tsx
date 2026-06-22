import { useState } from "react";
import { useSearchParams, Link } from "react-router-dom";
import { IndianRupee, List, FileText, BarChart3 } from "lucide-react";
import { useAnalysis } from "../hooks/useAnalysis";
import SpendSummary from "../components/SpendSummary";
import CategoryBreakdown from "../components/CategoryBreakdown";
import RecurringPayments from "../components/RecurringPayments";
import BiggestTransaction from "../components/BiggestTransaction";
import SpendTrendChart from "../components/SpendTrendChart";
import InsightsPanel from "../components/InsightsPanel";
import ReportView from "../components/ReportView";
import type { AnalysisData } from "../types";

export default function DashboardPage() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get("job");
  const { state, data, error } = useAnalysis(jobId);
  const [reportOpen, setReportOpen] = useState(false);

  // If no job_id is provided, prompt user to upload
  if (!jobId) {
    return (
      <div className="mx-auto max-w-2xl text-center py-20">
        <IndianRupee className="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600" />
        <h1 className="mt-6 text-2xl font-bold text-gray-900 dark:text-gray-100">
          Dashboard
        </h1>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Upload a bank statement to see your personalized financial dashboard.
        </p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 transition-colors"
        >
          Upload Statement
        </Link>
      </div>
    );
  }

  // Polling state
  if (state === "polling") {
    return (
      <div className="mx-auto max-w-2xl text-center py-20">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        <h2 className="mt-6 text-xl font-semibold text-gray-800 dark:text-gray-200">
          Analyzing your statement...
        </h2>
        <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
          Parsing transactions, categorizing, detecting recurring payments, and
          generating insights.
        </p>
        <div className="mt-8 grid grid-cols-4 gap-2 max-w-xs mx-auto">
          {[1, 2, 3, 4].map((i) => (
            <div
              key={i}
              className="h-1.5 rounded-full bg-gray-200 dark:bg-gray-700 animate-pulse"
              style={{ animationDelay: `${i * 0.2}s` }}
            />
          ))}
        </div>
      </div>
    );
  }

  // Failed state
  if (state === "failed") {
    return (
      <div className="mx-auto max-w-2xl text-center py-20">
        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-red-100 dark:bg-red-900/30">
          <span className="text-2xl text-red-600 dark:text-red-400">!</span>
        </div>
        <h2 className="mt-6 text-xl font-semibold text-red-700 dark:text-red-400">
          Analysis Failed
        </h2>
        <p className="mt-2 text-sm text-red-500">{error}</p>
        <Link
          to="/"
          className="mt-6 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 transition-colors"
        >
          Try Again
        </Link>
      </div>
    );
  }

  // Completed state
  if (state === "completed" && data) {
    return (
      <>
        <DashboardContent data={data} onOpenReport={() => setReportOpen(true)} />
        <ReportView
          jobId={jobId}
          open={reportOpen}
          onClose={() => setReportOpen(false)}
        />
      </>
    );
  }

  return null;
}

function DashboardContent({
  data,
  onOpenReport,
}: {
  data: AnalysisData;
  onOpenReport: () => void;
}) {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get("job") ?? "";
  const { metrics, insights, recurring_payments, transactions, file_name } =
    data;

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      {/* Page header */}
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Dashboard
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {file_name} &middot; {transactions.length} transactions processed
            {data.parsed_at &&
              ` on ${new Date(data.parsed_at).toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })}`}
          </p>
        </div>
        <button
          onClick={onOpenReport}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
        >
          <FileText className="h-4 w-4" />
          Download Report
        </button>
      </div>

      {/* ── Stats Cards Row (per architecture §10 wireframe) ── */}
      <SpendSummary metrics={metrics} />

      {/* ── Biggest Transaction Highlights ── */}
      <BiggestTransaction metrics={metrics} />

      {/* ── Two-Column Layout ── */}
      <div className="grid gap-6 lg:grid-cols-2">
        <CategoryBreakdown categories={metrics.top_categories} />
        <RecurringPayments payments={recurring_payments} />
      </div>

      {/* ── Spend Trend Chart ── */}
      <SpendTrendChart transactions={transactions} />

      {/* ── AI Insights Panel ── */}
      <InsightsPanel insights={insights} />

      {/* ── Quick links ── */}
      <div className="flex flex-wrap gap-3">
        <Link
          to={`/transactions?job=${jobId}`}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
        >
          <List className="h-4 w-4" />
          View All Transactions
        </Link>
        <button
          onClick={onOpenReport}
          className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors"
        >
          <BarChart3 className="h-4 w-4" />
          Download Report
        </button>
      </div>

      {/* ── Warnings ── */}
      {data.warnings && data.warnings.length > 0 && (
        <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 dark:border-amber-800 dark:bg-amber-900/20">
          <p className="text-sm font-medium text-amber-800 dark:text-amber-300 mb-1">
            Notices
          </p>
          <ul className="list-inside list-disc space-y-0.5">
            {data.warnings.map((w, i) => (
              <li key={i} className="text-xs text-amber-700 dark:text-amber-400">
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
