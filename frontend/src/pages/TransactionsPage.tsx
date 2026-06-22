import { useSearchParams, Link } from "react-router-dom";
import { List, Download } from "lucide-react";
import { useAnalysis } from "../hooks/useAnalysis";
import TransactionTable from "../components/TransactionTable";
import { useCsvExport } from "../hooks/useCsvExport";
import type { Transaction } from "../types";

export default function TransactionsPage() {
  const [searchParams] = useSearchParams();
  const jobId = searchParams.get("job");
  const { state, data, error } = useAnalysis(jobId);

  // Must call all hooks BEFORE any early returns to comply with React's rules of hooks
  const transactions: Transaction[] = data?.transactions ?? [];
  const { exportCSV, exporting } = useCsvExport(transactions);

  if (!jobId) {
    return (
      <div className="mx-auto max-w-2xl text-center py-20">
        <List className="mx-auto h-16 w-16 text-gray-300 dark:text-gray-600" />
        <h1 className="mt-6 text-2xl font-bold text-gray-900 dark:text-gray-100">
          Transactions
        </h1>
        <p className="mt-2 text-gray-500 dark:text-gray-400">
          Upload a bank statement to view and manage your transactions.
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

  if (state === "polling") {
    return (
      <div className="mx-auto max-w-2xl text-center py-20">
        <div className="mx-auto h-12 w-12 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
        <h2 className="mt-6 text-xl font-semibold text-gray-800 dark:text-gray-200">
          Loading transactions...
        </h2>
      </div>
    );
  }

  if (state === "failed") {
    return (
      <div className="mx-auto max-w-2xl text-center py-20">
        <p className="text-red-500">{error}</p>
        <Link
          to="/"
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white"
        >
          Try Again
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            Transactions
          </h1>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {data?.file_name && `${data.file_name} · `}
            {data?.total_transactions ?? 0} transactions
            {data && data.total_parsed > data.total_transactions &&
              ` (${data.total_skipped} skipped)`}
          </p>
        </div>
        {transactions.length > 0 && (
          <button
            onClick={exportCSV}
            disabled={exporting}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-2.5 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-300 dark:hover:bg-gray-700 transition-colors disabled:opacity-50"
          >
            <Download className="h-4 w-4" />
            {exporting ? "Exporting..." : "Export CSV"}
          </button>
        )}
      </div>

      <TransactionTable
        transactions={transactions}
        jobId={jobId}
      />
    </div>
  );
}
