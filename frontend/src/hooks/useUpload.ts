import { useState, useCallback } from "react";
import { uploadFile } from "../api/client";

type UploadState = "idle" | "uploading" | "processing" | "done" | "error";

export function useUpload() {
  const [state, setState] = useState<UploadState>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  const upload = useCallback(async (file: File) => {
    setState("uploading");
    setError(null);
    setProgress(0);

    // Simulate progress for UX
    const progressInterval = setInterval(() => {
      setProgress((p) => Math.min(p + 10, 90));
    }, 300);

    try {
      const response = await uploadFile(file);
      clearInterval(progressInterval);
      setProgress(100);
      setJobId(response.job_id);
      setState("done");
      return response.job_id;
    } catch (err: unknown) {
      clearInterval(progressInterval);
      const message =
        err instanceof Error ? err.message : "Upload failed. Please try again.";
      setError(message);
      setState("error");
      return null;
    }
  }, []);

  const reset = useCallback(() => {
    setState("idle");
    setJobId(null);
    setError(null);
    setProgress(0);
  }, []);

  return { state, jobId, error, progress, upload, reset };
}
