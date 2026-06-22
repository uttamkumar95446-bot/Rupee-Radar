import axios from "axios";
import type { JobStatus, UploadResponse } from "../types";

// In production (Vercel), VITE_API_URL points to the Railway backend URL.
// In development, the Vite proxy handles /api -> http://localhost:8000.
const API_BASE = import.meta.env.VITE_API_URL || "/api";

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

// ── Upload ──

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post<UploadResponse>("/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ── Analysis Polling ──

export async function getAnalysis(jobId: string): Promise<JobStatus> {
  const { data } = await api.get<JobStatus>(`/analysis/${jobId}`);
  return data;
}

// ── Report Download ──

export async function downloadReport(
  jobId: string,
  format: "html" | "pdf" = "html"
): Promise<Blob> {
  const { data } = await api.get(`/report/${jobId}`, {
    params: { format },
    responseType: "blob",
  });
  return data;
}

// ── Manual Overrides ──

export async function overrideCategory(
  jobId: string,
  transactionId: string,
  category: string
): Promise<void> {
  await api.put(
    `/analysis/${jobId}/transactions/${transactionId}/category`,
    null,
    { params: { category } }
  );
}

export async function overrideRecurring(
  jobId: string,
  transactionId: string,
  isRecurring: boolean,
  recurringType?: string
): Promise<void> {
  await api.put(
    `/analysis/${jobId}/transactions/${transactionId}/recurring`,
    null,
    { params: { is_recurring: isRecurring, recurring_type: recurringType } }
  );
}
