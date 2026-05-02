"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type ActionListParams,
  createAction,
  deleteAction,
  listActions,
  markActionCompleted,
  updateAction,
} from "../api/actions";
import type { ActionWriteInput } from "../api/types";

export function useActions(params: ActionListParams = {}) {
  return useQuery({
    queryKey: ["actions", params],
    queryFn: () => listActions(params),
    enabled: params.client === undefined || Number.isFinite(params.client),
  });
}

export function useCreateAction(clientId: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ActionWriteInput) => createAction(clientId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["actions"] });
      qc.invalidateQueries({ queryKey: ["client", clientId] });
    },
  });
}

export function useUpdateAction(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ActionWriteInput) => updateAction(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["actions"] }),
  });
}

export function useDeleteAction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteAction(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["actions"] }),
  });
}

export function useMarkActionCompleted() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => markActionCompleted(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["actions"] }),
  });
}
