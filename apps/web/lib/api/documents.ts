import { api, ensureCsrf, HttpError } from "./client";
import type { DocumentSummary, Paginated } from "./types";
import { getApiBase } from "../env";

export interface DocumentListParams {
  client?: number;
  page?: number;
}

export function listDocuments(params: DocumentListParams = {}) {
  return api<Paginated<DocumentSummary>>("/api/documents", { query: params });
}

export function deleteDocument(id: number) {
  return api<void>(`/api/documents/${id}`, { method: "DELETE" });
}

export interface UploadProgress {
  loaded: number;
  total: number;
}

export interface UploadDocumentInput {
  client: number;
  file: File;
  notes?: string;
  onProgress?: (progress: UploadProgress) => void;
  signal?: AbortSignal;
}

/**
 * Multipart upload via XHR — fetch can't report upload progress; XHR can.
 * Mirrors the api() wrapper's CSRF + cookie semantics.
 */
export async function uploadDocument(
  input: UploadDocumentInput,
): Promise<DocumentSummary> {
  await ensureCsrf();

  const form = new FormData();
  form.append("client", String(input.client));
  form.append("file", input.file);
  if (input.notes) form.append("notes", input.notes);

  const csrf = readCookie("csrftoken");

  return new Promise<DocumentSummary>((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    xhr.open("POST", `${getApiBase()}/api/documents`, true);
    xhr.withCredentials = true;
    if (csrf) xhr.setRequestHeader("X-CSRFToken", csrf);
    xhr.setRequestHeader("Accept", "application/json");

    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && input.onProgress) {
        input.onProgress({ loaded: e.loaded, total: e.total });
      }
    };

    xhr.onload = () => {
      let body: unknown = null;
      try {
        body = JSON.parse(xhr.responseText);
      } catch {
        body = xhr.responseText;
      }
      if (xhr.status >= 200 && xhr.status < 300) {
        resolve(body as DocumentSummary);
      } else {
        reject(new HttpError(xhr.status, body));
      }
    };

    xhr.onerror = () => reject(new Error("Network error"));
    xhr.onabort = () => reject(new Error("Upload aborted"));

    if (input.signal) {
      input.signal.addEventListener("abort", () => xhr.abort());
    }

    xhr.send(form);
  });
}

export function downloadDocumentUrl(id: number): string {
  return `${getApiBase()}/api/documents/${id}/download`;
}

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)"),
  );
  return match ? decodeURIComponent(match[1]) : null;
}
