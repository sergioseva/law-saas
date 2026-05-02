import { api } from "./client";
import type { DocumentSummary, Paginated } from "./types";

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
