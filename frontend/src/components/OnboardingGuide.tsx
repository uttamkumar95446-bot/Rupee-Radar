import { useState, useEffect } from "react";
import { Upload, BarChart3, List, FileText, Lightbulb, X, ArrowRight, Check } from "lucide-react";

const ONBOARDING_KEY = "rupeeradar-onboarding-done";

const STEPS = [
  {
    icon: Upload,
    title: "Upload Your Statement",
    description: "Start by uploading your bank statement CSV or PDF. RupeeRadar supports HDFC, ICICI, SBI, Axis, and other Indian banks.",
    color: "bg-emerald-100 text-emerald-600 dark:bg-emerald-900/30 dark:text-emerald-400",
  },
  {
    icon: BarChart3,
    title: "View Your Dashboard",
    description: "Get a comprehensive overview of your finances — income, spending, savings rate, top categories, and AI-powered insights.",
    color: "bg-blue-100 text-blue-600 dark:bg-blue-900/30 dark:text-blue-400",
  },
  {
    icon: List,
    title: "Manage Transactions",
    description: "Search, filter, and sort through all your transactions. Override categories or mark recurring payments manually.",
    color: "bg-purple-100 text-purple-600 dark:bg-purple-900/30 dark:text-purple-400",
  },
  {
    icon: FileText,
    title: "Download Reports",
    description: "Generate downloadable HTML/PDF reports with charts and detailed transaction logs to share or archive.",
    color: "bg-amber-100 text-amber-600 dark:bg-amber-900/30 dark:text-amber-400",
  },
  {
    icon: Lightbulb,
    title: "Get AI Insights",
    description: "Receive personalized financial advice, detect recurring payments, and identify suspicious transactions automatically.",
    color: "bg-rose-100 text-rose-600 dark:bg-rose-900/30 dark:text-rose-400",
  },
];

export default function OnboardingGuide() {
  const [open, setOpen] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    const done = localStorage.getItem(ONBOARDING_KEY);
    if (!done) {
      const timer = setTimeout(() => setOpen(true), 500);
      return () => clearTimeout(timer);
    }
  }, []);

  const dismiss = () => {
    localStorage.setItem(ONBOARDING_KEY, "true");
    setOpen(false);
  };

  const next = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      dismiss();
    }
  };

  const prev = () => {
    if (step > 0) setStep((s) => s - 1);
  };

  if (!open) return null;

  const CurrentIcon = STEPS[step].icon;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/50 backdrop-blur-sm" onClick={dismiss} />
      <div className="relative w-full max-w-md rounded-2xl bg-white shadow-2xl dark:bg-gray-800 animate-[fadeIn_0.3s_ease-out] overflow-hidden">
        {/* Progress bar */}
        <div className="flex gap-1 px-6 pt-5">
          {STEPS.map((_, i) => (
            <div
              key={i}
              className={`h-1 flex-1 rounded-full transition-colors ${
                i <= step ? "bg-emerald-500" : "bg-gray-200 dark:bg-gray-700"
              }`}
            />
          ))}
        </div>

        <div className="px-6 py-6">
          <div className={`mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl ${STEPS[step].color}`}>
            <CurrentIcon className="h-8 w-8" />
          </div>

          <h2 className="text-center text-lg font-bold text-gray-900 dark:text-gray-100">
            {STEPS[step].title}
          </h2>
          <p className="mt-2 text-center text-sm text-gray-500 dark:text-gray-400 leading-relaxed">
            {STEPS[step].description}
          </p>
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-gray-100 px-6 py-4 dark:border-gray-700">
          <button
            onClick={dismiss}
            className="text-sm text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
          >
            Skip
          </button>

          <div className="flex items-center gap-2">
            {step > 0 && (
              <button
                onClick={prev}
                className="rounded-lg border border-gray-200 px-3 py-2 text-sm font-medium text-gray-600 hover:bg-gray-50 dark:border-gray-600 dark:text-gray-400 dark:hover:bg-gray-700 transition-colors"
              >
                Back
              </button>
            )}
            <button
              onClick={next}
              className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 px-4 py-2 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 transition-colors"
            >
              {step < STEPS.length - 1 ? (
                <>
                  Next <ArrowRight className="h-4 w-4" />
                </>
              ) : (
                <>
                  Get Started <Check className="h-4 w-4" />
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
