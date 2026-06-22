import { createContext, useContext, useState, useCallback, type ReactNode } from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
  id: string;
  type: ToastType;
  title: string;
  message?: string;
}

interface ToastContextType {
  toast: Toast[];
  addToast: (type: ToastType, title: string, message?: string) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}

const ICONS: Record<ToastType, typeof CheckCircle> = {
  success: CheckCircle,
  error: AlertCircle,
  info: Info,
  warning: AlertTriangle,
};

const COLORS: Record<ToastType, string> = {
  success: "border-emerald-500 bg-emerald-50 dark:bg-emerald-900/20",
  error: "border-red-500 bg-red-50 dark:bg-red-900/20",
  info: "border-blue-500 bg-blue-50 dark:bg-blue-900/20",
  warning: "border-amber-500 bg-amber-50 dark:bg-amber-900/20",
};

const TEXT_COLORS: Record<ToastType, string> = {
  success: "text-emerald-800 dark:text-emerald-300",
  error: "text-red-800 dark:text-red-300",
  info: "text-blue-800 dark:text-blue-300",
  warning: "text-amber-800 dark:text-amber-300",
};

const ICON_COLORS: Record<ToastType, string> = {
  success: "text-emerald-500",
  error: "text-red-500",
  info: "text-blue-500",
  warning: "text-amber-500",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toastList, setToastList] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, title: string, message?: string) => {
    const id = crypto.randomUUID();
    setToastList((prev) => [...prev, { id, type, title, message }]);
    setTimeout(() => {
      setToastList((prev) => prev.filter((t) => t.id !== id));
    }, 5000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToastList((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toast: toastList, addToast, removeToast }}>
      {children}
      {/* Toast container */}
      <div className="fixed bottom-4 right-4 z-[60] flex flex-col gap-2 max-w-sm">
        {toastList.map((t) => {
          const Icon = ICONS[t.type];
          return (
            <div
              key={t.id}
              className={`flex items-start gap-3 rounded-lg border-l-4 p-3 shadow-lg animate-[fadeIn_0.3s_ease-out] ${COLORS[t.type]}`}
            >
              <Icon className={`h-5 w-5 shrink-0 mt-0.5 ${ICON_COLORS[t.type]}`} />
              <div className="flex-1 min-w-0">
                <p className={`text-sm font-medium ${TEXT_COLORS[t.type]}`}>{t.title}</p>
                {t.message && (
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{t.message}</p>
                )}
              </div>
              <button
                onClick={() => removeToast(t.id)}
                className="shrink-0 rounded p-0.5 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                <X className="h-3.5 w-3.5" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}
