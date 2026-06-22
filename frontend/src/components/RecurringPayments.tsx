import { Repeat, Landmark, Home, TrendingUp, Shield } from "lucide-react";
import type { RecurringPayment } from "../types";
import { formatINR } from "../utils/format";

interface RecurringPaymentsProps {
  payments: RecurringPayment[];
  loading?: boolean;
}

const typeIcons: Record<string, { icon: typeof Repeat; label: string }> = {
  subscription: { icon: Repeat, label: "Subscription" },
  emi: { icon: Landmark, label: "EMI" },
  rent: { icon: Home, label: "Rent" },
  sip: { icon: TrendingUp, label: "SIP" },
  insurance: { icon: Shield, label: "Insurance" },
};

export default function RecurringPayments({
  payments,
  loading,
}: RecurringPaymentsProps) {
  if (loading) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100 animate-pulse">
        <div className="h-5 w-40 bg-gray-200 rounded mb-4" />
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-14 bg-gray-100 rounded-lg" />
          ))}
        </div>
      </div>
    );
  }

  if (!payments || payments.length === 0) {
    return (
      <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
        <h3 className="text-sm font-semibold text-gray-700 mb-3">
          Recurring Payments
        </h3>
        <p className="text-sm text-gray-400">No recurring payments detected.</p>
      </div>
    );
  }

  const totalMonthly = payments
    .filter((p) => p.frequency === "monthly")
    .reduce((s, p) => s + p.amount, 0);

  return (
    <div className="rounded-xl bg-white p-5 shadow-sm border border-gray-100">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-gray-700">
          Recurring Payments
        </h3>
        <span className="text-xs text-gray-500">
          {payments.length} active
        </span>
      </div>

      <div className="space-y-2">
        {payments.map((p, i) => {
          const typeInfo = typeIcons[p.r_type] ?? {
            icon: Repeat,
            label: p.r_type,
          };
          const Icon = typeInfo.icon;
          return (
            <div
              key={`${p.merchant}-${i}`}
              className="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
            >
              <div className="flex items-center gap-3">
                <div className="rounded-full bg-blue-100 p-1.5">
                  <Icon className="h-4 w-4 text-blue-600" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-800">
                    {p.merchant}
                  </p>
                  <p className="text-xs text-gray-500 capitalize">
                    {typeInfo.label} &middot; {p.frequency}
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm font-semibold text-gray-800">
                  ₹{formatINR(p.amount)}
                </p>
                {p.frequency === "monthly" && (
                  <p className="text-xs text-gray-400">/mo</p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="mt-3 rounded-lg bg-emerald-50 px-4 py-2 text-xs text-emerald-700">
        Total monthly recurring: ₹{formatINR(totalMonthly)}
      </div>
    </div>
  );
}
