import { useState, useRef, type DragEvent } from "react";
import { Upload, FileText, AlertCircle, CheckCircle2 } from "lucide-react";

interface FileUploaderProps {
  onUpload: (file: File) => Promise<string | null>;
  progress: number;
  state: "idle" | "uploading" | "processing" | "done" | "error";
  error: string | null;
}

export default function FileUploader({
  onUpload,
  progress,
  state,
  error,
}: FileUploaderProps) {
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = async (file: File) => {
    if (
      !file.name.toLowerCase().endsWith(".csv") &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      return;
    }
    await onUpload(file);
  };

  const onDrop = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file) handleFile(file);
  };

  const onDragOver = (e: DragEvent) => {
    e.preventDefault();
    setDragOver(true);
  };

  const onDragLeave = () => setDragOver(false);

  const onFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) handleFile(file);
  };

  const isBusy = state === "uploading" || state === "processing";

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onClick={() => !isBusy && inputRef.current?.click()}
        className={`relative cursor-pointer rounded-2xl border-2 border-dashed p-12 text-center transition-all duration-200 ${
          dragOver
            ? "border-emerald-500 bg-emerald-50"
            : isBusy
              ? "border-gray-300 bg-gray-50 cursor-wait"
              : "border-gray-300 bg-white hover:border-emerald-400 hover:bg-emerald-50/50"
        }`}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".csv,.pdf"
          className="hidden"
          onChange={onFileSelect}
          disabled={isBusy}
        />

        {state === "done" ? (
          <div className="flex flex-col items-center gap-3">
            <CheckCircle2 className="h-12 w-12 text-emerald-500" />
            <p className="text-lg font-semibold text-emerald-700">
              Analysis Complete!
            </p>
            <p className="text-sm text-gray-500">
              View your results on the Dashboard.
            </p>
          </div>
        ) : state === "error" ? (
          <div className="flex flex-col items-center gap-3">
            <AlertCircle className="h-12 w-12 text-red-500" />
            <p className="text-lg font-semibold text-red-700">
              Upload Failed
            </p>
            <p className="text-sm text-red-500">{error}</p>
            <button
              onClick={(e) => {
                e.stopPropagation();
                // reset is handled by parent
              }}
              className="mt-2 text-sm font-medium text-emerald-600 hover:text-emerald-700"
            >
              Try again
            </button>
          </div>
        ) : isBusy ? (
          <div className="flex flex-col items-center gap-4">
            <div className="h-12 w-12 animate-spin rounded-full border-4 border-emerald-200 border-t-emerald-600" />
            <p className="text-lg font-semibold text-gray-700">
              {state === "uploading"
                ? "Uploading..."
                : "Processing your statement..."}
            </p>
            <div className="w-full max-w-xs bg-gray-200 rounded-full h-2.5">
              <div
                className="bg-emerald-500 h-2.5 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <Upload className="h-12 w-12 text-gray-400" />
            <div>
              <p className="text-lg font-semibold text-gray-700">
                Drop your bank statement here
              </p>
              <p className="mt-1 text-sm text-gray-500">
                or click to browse — CSV or PDF up to 10MB
              </p>
            </div>
            <div className="flex gap-3 mt-2">
              <span className="flex items-center gap-1.5 rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700">
                <FileText className="h-3.5 w-3.5" />
                CSV
              </span>
              <span className="flex items-center gap-1.5 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
                <FileText className="h-3.5 w-3.5" />
                PDF
              </span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
