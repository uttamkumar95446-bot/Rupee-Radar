import { useMemo, useState } from "react";
import {
  ArrowUpDown,
  Search,
  ChevronLeft,
  ChevronRight,
  Check,
  X,
} from "lucide-react";
import type { Transaction } from "../types";
import { ALL_CATEGORIES, CATEGORY_COLORS } from "../types";
import { overrideCategory } from "../api/client";
import { formatINR } from "../utils/format";

interface TransactionTableProps {
  transactions: Transaction[];
  jobId: string | null;
  loading?: boolean;
}

type SortKey = "date" | "description" | "amount" | "category" | "merchant";
type SortDir = "asc" | "desc";

const PAGE_SIZES = [25, 50, 100] as const;

export default function TransactionTable({
  transactions,
  jobId,
  loading,
}: TransactionTableProps) {
  // Search & filters
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [typeFilter, setTypeFilter] = useState<string>("all");
  const [recurringFilter, setRecurringFilter] = useState<string>("all");

  // Sorting
  const [sortKey, setSortKey] = useState<SortKey>("date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");

  // Pagination
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState<number>(50);

  // Inline editing
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [editSaving, setEditSaving] = useState(false);

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) {
      setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const filtered = useMemo(() => {
    let result = [...transactions];

    // Search
    if (search) {
      const q = search.toLowerCase();
      result = result.filter(
        (t) =>
          t.description.toLowerCase().includes(q) ||
          (t.merchant && t.merchant.toLowerCase().includes(q)) ||
          t.category.toLowerCase().includes(q)
      );
    }

    // Category filter
    if (categoryFilter !== "all") {
      result = result.filter((t) => t.category === categoryFilter);
    }

    // Type filter
    if (typeFilter !== "all") {
      result = result.filter((t) => t.txn_type === typeFilter);
    }

    // Recurring filter
    if (recurringFilter === "yes") {
      result = result.filter((t) => t.is_recurring);
    } else if (recurringFilter === "no") {
      result = result.filter((t) => !t.is_recurring);
    }

    // Sort
    result.sort((a, b) => {
      let cmp = 0;
      switch (sortKey) {
        case "date":
          cmp = a.date.localeCompare(b.date);
          break;
        case "description":
          cmp = a.description.localeCompare(b.description);
          break;
        case "amount":
          cmp = a.amount - b.amount;
          break;
        case "category":
          cmp = a.category.localeCompare(b.category);
          break;
        case "merchant":
          cmp = (a.merchant ?? "").localeCompare(b.merchant ?? "");
          break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

    return result;
  }, [transactions, search, categoryFilter, typeFilter, recurringFilter, sortKey, sortDir]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const safePage = Math.min(page, totalPages - 1);
  const paged = filtered.slice(safePage * pageSize, (safePage + 1) * pageSize);

  const startEdit = (txn: Transaction) => {
    setEditingId(txn.id);
    setEditValue(txn.category);
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditValue("");
  };

  const saveEdit = async (txn: Transaction) => {
    if (!jobId || editValue === txn.category) {
      cancelEdit();
      return;
    }
    setEditSaving(true);
    try {
      await overrideCategory(jobId, txn.id, editValue);
      txn.category = editValue;
      txn.category_confidence = 1.0;
    } catch {
      // revert silently
    }
    setEditSaving(false);
    cancelEdit();
  };

  const SortIcon = ({ column }: { column: SortKey }) => {
    if (sortKey !== column) return <ArrowUpDown className="h-3 w-3 text-gray-300" />;
    return (
      <span className="text-emerald-600">
        {sortDir === "asc" ? " ▲" : " ▼"}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="rounded-xl bg-white shadow-sm border border-gray-100 animate-pulse p-6">
        <div className="h-8 w-full bg-gray-100 rounded mb-4" />
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="h-12 bg-gray-50 rounded mb-2" />
        ))}
      </div>
    );
  }

  if (!transactions || transactions.length === 0) {
    return (
      <div className="rounded-xl bg-white p-6 shadow-sm border border-gray-100 text-center">
        <p className="text-gray-400">No transactions to display.</p>
        <p className="text-sm text-gray-300 mt-1">
          Upload a bank statement to get started.
        </p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-white shadow-sm border border-gray-100 overflow-hidden">
      {/* Toolbar: search + filters */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-gray-100">
        {/* Search */}
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
          <input
            type="text"
            placeholder="Search transactions..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(0);
            }}
            className="w-full rounded-lg border border-gray-200 bg-gray-50 pl-9 pr-3 py-2 text-sm focus:border-emerald-400 focus:outline-none focus:ring-1 focus:ring-emerald-400"
          />
        </div>

        {/* Category filter */}
        <select
          value={categoryFilter}
          onChange={(e) => {
            setCategoryFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none"
        >
          <option value="all">All Categories</option>
          {ALL_CATEGORIES.map((c) => (
            <option key={c} value={c}>
              {c}
            </option>
          ))}
        </select>

        {/* Type filter */}
        <select
          value={typeFilter}
          onChange={(e) => {
            setTypeFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none"
        >
          <option value="all">All Types</option>
          <option value="debit">Debit</option>
          <option value="credit">Credit</option>
        </select>

        {/* Recurring filter */}
        <select
          value={recurringFilter}
          onChange={(e) => {
            setRecurringFilter(e.target.value);
            setPage(0);
          }}
          className="rounded-lg border border-gray-200 bg-gray-50 px-3 py-2 text-sm focus:border-emerald-400 focus:outline-none"
        >
          <option value="all">All</option>
          <option value="yes">Recurring</option>
          <option value="no">One-time</option>
        </select>

        <span className="text-xs text-gray-400 whitespace-nowrap">
          {filtered.length} of {transactions.length}
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-100 bg-gray-50/50">
              <Th onClick={() => toggleSort("date")}>
                Date <SortIcon column="date" />
              </Th>
              <Th onClick={() => toggleSort("description")}>
                Description <SortIcon column="description" />
              </Th>
              <Th onClick={() => toggleSort("merchant")}>
                Merchant <SortIcon column="merchant" />
              </Th>
              <Th onClick={() => toggleSort("amount")}>
                Amount <SortIcon column="amount" />
              </Th>
              <Th onClick={() => toggleSort("category")}>
                Category <SortIcon column="category" />
              </Th>
              <Th>Type</Th>
              <Th>Recurring</Th>
            </tr>
          </thead>
          <tbody>
            {paged.map((txn) => (
              <tr
                key={txn.id}
                className="border-b border-gray-50 hover:bg-gray-50/50 transition-colors"
              >
                <Td>{txn.date}</Td>
                <Td className="max-w-[200px] truncate" title={txn.description}>
                  {txn.description}
                </Td>
                <Td>{txn.merchant ?? "-"}</Td>
                <Td
                  className={`font-semibold ${
                    txn.txn_type === "credit"
                      ? "text-emerald-600"
                      : "text-red-600"
                  }`}
                >
                  {txn.txn_type === "credit" ? "+" : "-"}₹{formatINR(txn.amount)}
                </Td>
                <Td>
                  {editingId === txn.id ? (
                    <div className="flex items-center gap-1">
                      <select
                        value={editValue}
                        onChange={(e) => setEditValue(e.target.value)}
                        autoFocus
                        className="rounded border border-emerald-400 px-1.5 py-0.5 text-xs focus:outline-none"
                      >
                        {ALL_CATEGORIES.map((c) => (
                          <option key={c} value={c}>
                            {c}
                          </option>
                        ))}
                      </select>
                      <button
                        onClick={() => saveEdit(txn)}
                        disabled={editSaving}
                        className="text-emerald-600 hover:text-emerald-700"
                      >
                        <Check className="h-3.5 w-3.5" />
                      </button>
                      <button
                        onClick={cancelEdit}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <X className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => startEdit(txn)}
                      className="flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors"
                      style={{
                        backgroundColor: `${CATEGORY_COLORS[txn.category] ?? "#9E9E9E"}20`,
                        color: CATEGORY_COLORS[txn.category] ?? "#9E9E9E",
                      }}
                    >
                      {txn.category}
                    </button>
                  )}
                </Td>
                <Td>
                  <span
                    className={`text-xs font-medium ${
                      txn.txn_type === "credit"
                        ? "text-emerald-600"
                        : "text-gray-500"
                    }`}
                  >
                    {txn.txn_type}
                  </span>
                </Td>
                <Td>
                  {txn.is_recurring ? (
                    <span className="rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-600">
                      {txn.recurring_type ?? "recurring"}
                    </span>
                  ) : (
                    <span className="text-xs text-gray-300">-</span>
                  )}
                </Td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between border-t border-gray-100 px-4 py-3">
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>Rows per page:</span>
          <select
            value={pageSize}
            onChange={(e) => {
              setPageSize(Number(e.target.value));
              setPage(0);
            }}
            className="rounded border border-gray-200 px-2 py-1 text-xs"
          >
            {PAGE_SIZES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span>
            {safePage * pageSize + 1}–
            {Math.min((safePage + 1) * pageSize, filtered.length)} of{" "}
            {filtered.length}
          </span>
          <button
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            disabled={safePage === 0}
            className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"
          >
            <ChevronLeft className="h-4 w-4" />
          </button>
          <button
            onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))}
            disabled={safePage >= totalPages - 1}
            className="rounded p-1 hover:bg-gray-100 disabled:opacity-30"
          >
            <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

// Helper styled table elements
function Th({
  children,
  onClick,
}: {
  children: React.ReactNode;
  onClick?: () => void;
}) {
  return (
    <th
      onClick={onClick}
      className={`px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider ${
        onClick ? "cursor-pointer hover:text-gray-700 select-none" : ""
      }`}
    >
      {children}
    </th>
  );
}

function Td({
  children,
  className,
  title,
}: {
  children: React.ReactNode;
  className?: string;
  title?: string;
}) {
  return (
    <td className={`px-4 py-3 text-sm text-gray-700 ${className ?? ""}`} title={title}>
      {children}
    </td>
  );
}
