"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type ClientListParams,
  createClient,
  deleteClient,
  getClient,
  listClients,
  updateClient,
} from "../api/clients";
import type { ClientWriteInput } from "../api/types";

export function useClients(params: ClientListParams = {}) {
  return useQuery({
    queryKey: ["clients", params],
    queryFn: () => listClients(params),
  });
}

export function useClient(id: number | undefined) {
  return useQuery({
    queryKey: ["client", id],
    queryFn: () => getClient(id as number),
    enabled: typeof id === "number" && Number.isFinite(id),
  });
}

export function useCreateClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ClientWriteInput) => createClient(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}

export function useUpdateClient(id: number) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: ClientWriteInput) => updateClient(id, data),
    onSuccess: (data) => {
      qc.invalidateQueries({ queryKey: ["clients"] });
      qc.setQueryData(["client", id], data);
    },
  });
}

export function useDeleteClient() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => deleteClient(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["clients"] });
    },
  });
}
