import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileText, ArrowRight } from "lucide-react";
import FileUploader from "../components/FileUploader";
import { useUpload } from "../hooks/useUpload";

export default function UploadPage() {
  const { state, jobId, error, progress, upload, reset } = useUpload();
  const navigate = useNavigate();

  useEffect(() => {
    if (state === "done" && jobId) {
      const timer = setTimeout(() => {
        navigate(`/dashboard?job=${jobId}`);
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [state, jobId, navigate]);

  const handleUpload = async (file: File): Promise<string | null> => {
    return await upload(file);
  };

  return (
    <div className="mx-auto max-w-3xl">
      {/* Header */}
      <div className="mb-8 text-center">
        <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-100">
          <Upload className="h-8 w-8 text-emerald-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">
          Upload Bank Statement
        </h1>
        <p className="mt-2 text-gray-500">
          Upload your bank statement CSV or PDF to get AI-powered insights on
          your spending habits.
        </p>
      </div>

      {/* Upload area */}
      <FileUploader
        onUpload={handleUpload}
        progress={progress}
        state={state as "idle" | "uploading" | "processing" | "done" | "error"}
        error={error}
      />

      {/* Processing state with navigation hint */}
      {state === "done" && jobId && (
        <div className="mt-6 text-center animate-[fadeIn_0.5s_ease-in]">
          <button
            onClick={() => navigate(`/dashboard?job=${jobId}`)}
            className="inline-flex items-center gap-2 rounded-lg bg-emerald-600 px-6 py-3 text-sm font-semibold text-white shadow-sm hover:bg-emerald-700 transition-colors"
          >
            View Dashboard
            <ArrowRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Reset */}
      {(state === "done" || state === "error") && (
        <div className="mt-4 text-center">
          <button
            onClick={reset}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Upload another file
          </button>
        </div>
      )}

      {/* Supported formats */}
      <div className="mt-10 rounded-xl border border-gray-200 bg-white p-6">
        <h2 className="text-sm font-semibold text-gray-700 mb-3">
          Supported Formats
        </h2>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="flex items-start gap-3 rounded-lg bg-gray-50 p-4">
            <FileText className="h-5 w-5 text-emerald-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-700">CSV Files</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Bank statement CSVs from HDFC, ICICI, SBI, Axis, and other
                Indian banks. Auto-detects column mappings.
              </p>
            </div>
          </div>
          <div className="flex items-start gap-3 rounded-lg bg-gray-50 p-4">
            <FileText className="h-5 w-5 text-blue-500 shrink-0 mt-0.5" />
            <div>
              <p className="text-sm font-medium text-gray-700">PDF Files</p>
              <p className="text-xs text-gray-500 mt-0.5">
                Digitally-generated PDF bank statements. Uses text extraction
                and table parsing.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
