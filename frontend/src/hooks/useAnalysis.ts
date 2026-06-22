import { useState, useEffect, useCallback, useRef } from "react";
import { getAnalysis } from "../api/client";
import type { AnalysisData } from "../types";

type PollState = "idle" | "polling" | "completed" | "failed";

export function useAnalysis(jobId: string | null) {
  const [state, setState] = useState<PollState>("idle");
  const [data, setData] = useState<AnalysisData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
  }, []);

  useEffect(() => {
    if (!jobId) {
      setState("idle");
      setData(null);
      return;
    }

    setState("polling");
    setError(null);

    const poll = async () => {
      try {
        const result = await getAnalysis(jobId);
        if (result.status === "completed") {
          setData(result.data);
          setState("completed");
          stopPolling();
        } else if (result.status === "failed") {
          setError(result.error ?? "Analysis failed.");
          setState("failed");
          stopPolling();
        }
        // "processing" → keep polling
      } catch (err: unknown) {
        const message =
          err instanceof Error
            ? err.message
            : "Failed to fetch analysis results.";
        setError(message);
        setState("failed");
        stopPolling();
      }
    };

    // Poll every 2 seconds
    poll();
    pollingRef.current = setInterval(poll, 2000);

    return () => {
      stopPolling();
    };
  }, [jobId, stopPolling]);

  return { state, data, error };
}
