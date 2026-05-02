import { api } from "./client";
import type {
  ActionDetail,
  ActionSummary,
  ActionWriteInput,
  Paginated,
} from "./types";

export interface ActionListParams {
  client?: number;
  completed?: boolean;
  page?: number;
}

export function listActions(params: ActionListParams = {}) {
  return api<Paginated<ActionSummary>>("/api/actions", { query: params });
}

export function getAction(id: number) {
  return api<ActionDetail>(`/api/actions/${id}`);
}

export function createAction(client: number, data: ActionWriteInput) {
  return api<ActionDetail>("/api/actions", {
    method: "POST",
    body: { client, ...data },
  });
}

export function updateAction(id: number, data: ActionWriteInput) {
  return api<ActionDetail>(`/api/actions/${id}`, { method: "PATCH", body: data });
}

export function deleteAction(id: number) {
  return api<void>(`/api/actions/${id}`, { method: "DELETE" });
}

export function markActionCompleted(id: number) {
  return api<ActionDetail>(`/api/actions/${id}/complete`, { method: "POST" });
}
