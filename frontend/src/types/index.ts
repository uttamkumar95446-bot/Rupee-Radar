// ── Data Models (matching backend Pydantic schemas) ──

export interface Transaction {
  id: string;
  date: string; // ISO date
  description: string;
  original_description: string;
  amount: number;
  txn_type: "debit" | "credit";
  category: string;
  category_confidence: number;
  merchant: string | null;
  is_recurring: boolean;
  recurring_type: string | null;
  tags: string[];
  is_suspicious: boolean;
  suspicious_reason: string | null;
}

export interface CategorySpend {
  category: string;
  amount: number;
  percentage: number;
  transaction_count: number;
}

export interface MerchantSpend {
  merchant: string;
  amount: number;
  category: string;
  transaction_count: number;
}

export interface RecurringPayment {
  merchant: string;
  category: string;
  amount: number;
  frequency: string;
  next_expected_date: string;
  r_type: string;
  transactions: Transaction[];
}

export interface Insight {
  title: string;
  description: string;
  insight_type: "spending" | "saving" | "recurring" | "alert";
  severity: "info" | "warning" | "positive";
  amount: number | null;
}

export interface FinancialMetrics {
  total_income: number;
  total_spend: number;
  savings: number;
  savings_rate: number;
  top_categories: CategorySpend[];
  top_merchants: MerchantSpend[];
  biggest_transaction: Transaction | null;
  biggest_credit: Transaction | null;
  monthly_spend: number;
  transaction_count: number;
  average_daily_spend: number;
}

export interface AnalysisData {
  file_name: string;
  parsed_at: string;
  transactions: Transaction[];
  total_transactions: number;
  recurring_payments: RecurringPayment[];
  metrics: FinancialMetrics;
  insights: Insight[];
  warnings: string[];
  total_parsed: number;
  total_skipped: number;
  balance_verified: boolean;
}

export interface JobStatus {
  status: "processing" | "completed" | "failed";
  data: AnalysisData | null;
  error?: string | null;
}

export interface UploadResponse {
  job_id: string;
  status: string;
  message: string;
}

// ── Category constants (matching backend) ──

export const ALL_CATEGORIES = [
  "Food",
  "Travel",
  "Shopping",
  "Bills",
  "EMI",
  "Subscriptions",
  "Salary",
  "Rent",
  "Investments",
  "Other",
] as const;

export type Category = (typeof ALL_CATEGORIES)[number];

export const CATEGORY_COLORS: Record<string, string> = {
  Food: "#FF9800",
  Travel: "#2196F3",
  Shopping: "#f44336",
  Bills: "#9C27B0",
  EMI: "#E91E63",
  Subscriptions: "#00BCD4",
  Salary: "#4CAF50",
  Rent: "#FF5722",
  Investments: "#607D8B",
  Other: "#9E9E9E",
};
