import { api } from "./client";
import type {
  ClientDetail,
  ClientSummary,
  ClientWriteInput,
  Paginated,
} from "./types";

export interface ClientListParams {
  q?: string;
  case_status?: string;
  case_type?: string;
  city?: string;
  page?: number;
}

export function listClients(params: ClientListParams = {}) {
  return api<Paginated<ClientSummary>>("/api/clients", { query: params });
}

export function getClient(id: number) {
  return api<ClientDetail>(`/api/clients/${id}`);
}

export function createClient(data: ClientWriteInput) {
  return api<ClientDetail>("/api/clients", { method: "POST", body: data });
}

export function updateClient(id: number, data: ClientWriteInput) {
  return api<ClientDetail>(`/api/clients/${id}`, { method: "PATCH", body: data });
}

export function deleteClient(id: number) {
  return api<void>(`/api/clients/${id}`, { method: "DELETE" });
}
