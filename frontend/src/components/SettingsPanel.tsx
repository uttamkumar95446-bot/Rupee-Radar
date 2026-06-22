import { useState, useEffect, useCallback } from "react";
import { X, Cpu, Cloud, Wifi, Shield } from "lucide-react";

export type AiMode = "local" | "cloud" | "offline";

const AI_MODE_KEY = "rupeeradar-ai-mode";
const DEFAULT_MODE: AiMode = "local";

export function getAiMode(): AiMode {
  const saved = localStorage.getItem(AI_MODE_KEY);
  if (saved === "local" || saved === "cloud" || saved === "offline") return saved;
  return DEFAULT_MODE;
}

export function setAiMode(mode: AiMode) {
  localStorage.setItem(AI_MODE_KEY, mode);
}

interface SettingsPanelProps {
  open: boolean;
  onClose: () => void;
}

const AI_OPTIONS: { value: AiMode; label: string; icon: typeof Cpu; description: string }[] = [
  {
    value: "local",
    label: "Local AI",
    icon: Cpu,
    description: "Uses lightweight models on your device. No data leaves your machine.",
  },
  {
    value: "cloud",
    label: "Cloud AI",
    icon: Cloud,
    description: "Uses Groq/OpenAI for richer analysis. Data sent to external API.",
  },
  {
    value: "offline",
    label: "Offline",
    icon: Wifi,
    description: "No AI features. Rule-based categorization only. Fully private.",
  },
];

export default function SettingsPanel({ open, onClose }: SettingsPanelProps) {
  const [aiMode, setAiModeState] = useState<AiMode>(getAiMode);

  const handleAiModeChange = (mode: AiMode) => {
    setAiMode(mode);
    setAiModeState(mode);
  };

  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    },
    [onClose]
  );

  useEffect(() => {
    if (open) {
      document.addEventListener("keydown", handleEscape);
      return () => document.removeEventListener("keydown", handleEscape);
    }
  }, [open, handleEscape]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="fixed inset-0 bg-black/40" onClick={onClose} />
      <div className="relative w-full max-w-md rounded-xl bg-white shadow-xl dark:bg-gray-800 animate-[fadeIn_0.2s_ease-out]">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-100 px-5 py-4 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Shield className="h-5 w-5 text-emerald-500" />
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              Settings
            </h2>
          </div>
          <button
            onClick={onClose}
            className="rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 dark:hover:bg-gray-700 dark:hover:text-gray-300"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <div className="max-h-[60vh] overflow-y-auto p-5 space-y-6">
          {/* AI Mode */}
          <div>
            <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
              AI Processing Mode
            </h3>
            <p className="text-xs text-gray-500 dark:text-gray-400 mb-3">
              Controls how transaction categorization and insights are generated.
            </p>
            <div className="space-y-2">
              {AI_OPTIONS.map((opt) => (
                <button
                  key={opt.value}
                  onClick={() => handleAiModeChange(opt.value)}
                  className={`flex w-full items-start gap-3 rounded-lg border p-3 text-left transition-colors ${
                    aiMode === opt.value
                      ? "border-emerald-400 bg-emerald-50 dark:border-emerald-600 dark:bg-emerald-900/20"
                      : "border-gray-200 bg-gray-50 hover:bg-gray-100 dark:border-gray-600 dark:bg-gray-700/50 dark:hover:bg-gray-700"
                  }`}
                >
                  <opt.icon className={`mt-0.5 h-5 w-5 shrink-0 ${
                    aiMode === opt.value ? "text-emerald-600" : "text-gray-400"
                  }`} />
                  <div className="flex-1">
                    <p className={`text-sm font-medium ${
                      aiMode === opt.value ? "text-emerald-800 dark:text-emerald-300" : "text-gray-700 dark:text-gray-300"
                    }`}>
                      {opt.label}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                      {opt.description}
                    </p>
                  </div>
                  {aiMode === opt.value && (
                    <div className="h-4 w-4 mt-0.5 rounded-full bg-emerald-500 flex items-center justify-center">
                      <div className="h-2 w-2 rounded-full bg-white" />
                    </div>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Data note */}
          <div className="rounded-lg bg-gray-50 p-3 dark:bg-gray-700/50">
            <p className="text-xs text-gray-500 dark:text-gray-400 leading-relaxed">
              <strong className="text-gray-700 dark:text-gray-300">Privacy Note:</strong>{" "}
              In "Local" mode, only transaction descriptions are sent to the AI for
              categorization. In "Cloud" mode, data is processed via Groq/OpenAI APIs.
              "Offline" mode disables all AI features entirely.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
