/** Format a number as Indian Rupees (e.g., ₹1,23,456). */
export function formatINR(amount: number | null): string {
  if (amount === null) return "";
  return new Intl.NumberFormat("en-IN", {
    maximumFractionDigits: 0,
  }).format(Math.abs(amount));
}
