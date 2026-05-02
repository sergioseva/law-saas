"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type DocumentListParams,
  deleteDocument,
  listDocuments,
} from "../api/documents";

export function useDocuments(params: DocumentListParams = {}) {
  return useQuery({
    queryKey: ["documents", params],
    queryFn: () => listDocuments(params),
    enabled: params.client === undefined || Number.isFinite(params.client),
  });
}

export function useDeleteDocument() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteDocument(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents"] }),
  });
}
