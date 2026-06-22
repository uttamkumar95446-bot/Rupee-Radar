import { useState, useEffect } from "react";
import { Shield, X } from "lucide-react";

const PRIVACY_KEY = "rupeeradar-privacy-accepted";

export default function PrivacyBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const accepted = localStorage.getItem(PRIVACY_KEY);
    if (!accepted) {
      const timer = setTimeout(() => setVisible(true), 1000);
      return () => clearTimeout(timer);
    }
  }, []);

  const accept = () => {
    localStorage.setItem(PRIVACY_KEY, "true");
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div className="fixed bottom-4 left-4 right-4 z-50 mx-auto max-w-lg animate-[fadeIn_0.4s_ease-out]">
      <div className="rounded-xl border border-gray-200 bg-white p-4 shadow-lg dark:border-gray-700 dark:bg-gray-800">
        <div className="flex items-start gap-3">
          <Shield className="mt-0.5 h-5 w-5 shrink-0 text-emerald-500" />
          <div className="flex-1">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
              Your Privacy Matters
            </h3>
            <p className="mt-1 text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
              RupeeRadar processes your bank statements locally by default. AI
              analysis is optional and can be turned off in Settings. We never
              store your data on external servers without your explicit consent.
            </p>
            <div className="mt-3 flex items-center gap-2">
              <button
                onClick={accept}
                className="rounded-lg bg-emerald-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-emerald-700 transition-colors"
              >
                Got it
              </button>
              <button
                onClick={() => {
                  accept();
                  window.dispatchEvent(new CustomEvent("open-settings"));
                }}
                className="text-xs font-medium text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 transition-colors"
              >
                View Settings
              </button>
            </div>
          </div>
          <button
            onClick={accept}
            className="shrink-0 rounded-lg p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      </div>
    </div>
  );
}
