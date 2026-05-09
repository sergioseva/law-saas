import { api } from "./client";
import { getApiBase } from "../env";

export type ExportFormat = "excel" | "pdf";

export interface ExportEnqueued {
  task_id: string;
  status: "queued";
}

export type ExportStatusResponse =
  | { task_id: string; status: "pending" | "queued" | "failed" }
  | {
      task_id: string;
      status: "ready";
      size_bytes: number | null;
      mime_type: string;
      download_url: string;
    };

export function startExport(format: ExportFormat) {
  return api<ExportEnqueued>(`/api/exports/${format}`, { method: "POST" });
}

export function getExportStatus(taskId: string) {
  return api<ExportStatusResponse>(`/api/exports/${taskId}`);
}

export function exportDownloadUrl(taskId: string): string {
  return `${getApiBase()}/api/exports/${taskId}/download`;
}
