"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type DocumentListParams,
  type UploadDocumentInput,
  deleteDocument,
  listDocuments,
  uploadDocument,
} from "../api/documents";

export function useDocuments(params: DocumentListParams = {}) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => listDocuments(params),
    enabled: params.client === undefined || Number.isFinite(params.client),
  });
}

export function useUploadDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: UploadDocumentInput) => uploadDocument(input),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}
