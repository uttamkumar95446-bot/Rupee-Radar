import { useState } from "react";
import { useToast } from "../components/ToastProvider";
import type { Transaction } from "../types";

function transactionsToCSV(transactions: Transaction[]): string {
  const headers = [
    "Date",
    "Description",
    "Merchant",
    "Amount",
    "Type",
    "Category",
    "Category Confidence",
    "Is Recurring",
    "Recurring Type",
    "Tags",
    "Is Suspicious",
    "Suspicious Reason",
  ];

  const rows = transactions.map((t) =>
    [
      t.date,
      `"${t.description.replace(/"/g, '""')}"`,
      t.merchant ? `"${t.merchant.replace(/"/g, '""')}"` : "",
      t.amount,
      t.txn_type,
      t.category,
      t.category_confidence,
      t.is_recurring ? "Yes" : "No",
      t.recurring_type ?? "",
      `"${t.tags.join("; ")}"`,
      t.is_suspicious ? "Yes" : "No",
      t.suspicious_reason ? `"${t.suspicious_reason.replace(/"/g, '""')}"` : "",
    ].join(",")
  );

  return [headers.join(","), ...rows].join("\n");
}

function downloadCSV(csv: string, filename: string) {
  const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export function useCsvExport(transactions: Transaction[]) {
  const { addToast } = useToast();
  const [exporting, setExporting] = useState(false);

  const exportCSV = async () => {
    if (!transactions.length) {
      addToast("warning", "No data to export");
      return;
    }

    setExporting(true);
    try {
      await new Promise((r) => setTimeout(r, 100));
      const csv = transactionsToCSV(transactions);
      const filename = `rupeeradar-transactions-${new Date().toISOString().split("T")[0]}.csv`;
      downloadCSV(csv, filename);
      addToast("success", `Exported ${transactions.length} transactions`, filename);
    } catch {
      addToast("error", "Export failed", "Could not generate CSV file.");
    } finally {
      setExporting(false);
    }
  };

  return { exportCSV, exporting, transactionCount: transactions.length };
}
