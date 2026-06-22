import { useState } from "react";
import { FileText, FileDown, X, ExternalLink, Loader2 } from "lucide-react";
import { downloadReport } from "../api/client";
import { useToast } from "./ToastProvider";

interface ReportViewProps {
  jobId: string;
  open: boolean;
  onClose: () => void;
}

export default function ReportView({ jobId, open, onClose }: ReportViewProps) {
  const [pdfLoading, setPdfLoading] = useState(false);
  const [htmlLoading, setHtmlLoading] = useState(false);
  const { addToast } = useToast();

  if (!open) return null;

  const handleDownload = async (format: "html" | "pdf") => {
    if (format === "pdf") setPdfLoading(true);
    else setHtmlLoading(true);

    try {
      const blob = await downloadReport(jobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `rupeeradar-report.${format}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
      addToast("success", `Report downloaded as ${format.toUpperCase()}`);
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Download failed.";
      if (format === "pdf") {
        addToast(
          "warning",
          "PDF unavailable - using HTML instead",
          "PDF generation requires system libraries. Opening HTML report in a new tab."
        );
        // Fallback: open HTML version in new tab
        window.open(`/api/report/${jobId}?format=html`, "_blank");
      } else {
        addToast("error", "Download failed", message);
      }
    } finally {
      setPdfLoading(false);
      setHtmlLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4">
      <div className="relative w-full max-w-lg rounded-2xl bg-white shadow-2xl">
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute right-4 top-4 rounded-lg p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-600 transition-colors"
          aria-label="Close"
        >
          <X className="h-5 w-5" />
        </button>

        <div className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <div className="rounded-xl bg-emerald-100 p-2.5">
              <FileText className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900">
                Download Report
              </h2>
              <p className="text-sm text-gray-500">
                Choose your preferred format
              </p>
            </div>
          </div>

          <div className="space-y-3">
            {/* HTML option */}
            <button
              onClick={() => handleDownload("html")}
              disabled={htmlLoading}
              className="w-full flex items-center gap-4 rounded-xl border border-gray-200 bg-gray-50 p-4 text-left transition-all hover:border-emerald-300 hover:bg-emerald-50 hover:shadow-sm disabled:opacity-60"
            >
              <div className="rounded-lg bg-blue-100 p-2">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-800">
                  Interactive HTML
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Full report with charts, insights, and transaction log. Opens
                  in browser.
                </p>
              </div>
              {htmlLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-blue-500" />
              ) : (
                <ExternalLink className="h-5 w-5 text-gray-400" />
              )}
            </button>

            {/* PDF option */}
            <button
              onClick={() => handleDownload("pdf")}
              disabled={pdfLoading}
              className="w-full flex items-center gap-4 rounded-xl border border-gray-200 bg-gray-50 p-4 text-left transition-all hover:border-emerald-300 hover:bg-emerald-50 hover:shadow-sm disabled:opacity-60"
            >
              <div className="rounded-lg bg-red-100 p-2">
                <FileDown className="h-5 w-5 text-red-600" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-gray-800">
                  Print-ready PDF
                </p>
                <p className="text-xs text-gray-500 mt-0.5">
                  Downloadable PDF with all sections. Great for sharing or
                  printing.
                </p>
              </div>
              {pdfLoading ? (
                <Loader2 className="h-5 w-5 animate-spin text-red-500" />
              ) : (
                <FileDown className="h-5 w-5 text-gray-400" />
              )}
            </button>
          </div>

          <p className="mt-4 text-xs text-center text-gray-400">
            Reports include: executive summary, category breakdown, recurring
            payments, AI insights, and full transaction log.
          </p>
        </div>
      </div>
    </div>
  );
}
