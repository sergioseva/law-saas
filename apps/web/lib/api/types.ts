/**
 * TypeScript types for API contracts.
 *
 * Phase 3.1: hand-written. Phase 3.5+: auto-generate from drf-spectacular's
 * OpenAPI schema via openapi-typescript-codegen.
 */

export type Role = "admin" | "abogado" | "secretario";

export type CaseStatus =
  | "consulta"
  | "en proceso"
  | "demanda iniciada"
  | "cerrado";

export type CaseType = "Extrajudicial" | "Judicial";

export type CaseLabel = "" | "+10" | "-10";

export interface Firm {
  id: string;
  subdomain: string;
  name: string;
  created_at: string;
}

export interface Me {
  email: string;
  role: Role | null;
  firm: Firm | null;
}

export interface ClientSummary {
  id: number;
  full_name_display: string | null;
  case_status: CaseStatus;
  case_type: CaseType;
  case_label: CaseLabel;
  first_visit_date: string | null;
  city_display: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClientDetail {
  id: number;
  full_name?: string;
  dni_cuil?: string;
  birth_date?: string | null;
  phone?: string;
  email?: string;
  address?: string;
  city?: string | null;
  employer?: string;
  insurer?: string;
  case_reason?: string;
  discharge_condition?: string;
  occupational_disease?: string;
  document_checklist?: Record<string, boolean>;
  profile_photo_path?: string | null;
  case_status: CaseStatus;
  case_type: CaseType;
  case_label: CaseLabel;
  first_visit_date: string | null;
  created_at: string;
  updated_at: string;
}

export interface ClientWriteInput {
  full_name?: string;
  dni_cuil?: string;
  birth_date?: string | null;
  phone?: string;
  email?: string;
  address?: string;
  city?: string;
  employer?: string;
  insurer?: string;
  case_reason?: string;
  discharge_condition?: string;
  occupational_disease?: string;
  case_status?: CaseStatus;
  case_type?: CaseType;
  case_label?: CaseLabel;
  first_visit_date?: string | null;
  document_checklist?: Record<string, boolean>;
}

export interface ActionSummary {
  id: number;
  client: number;
  action_date: string | null;
  next_action_date: string | null;
  next_step: string | null;
  completed: boolean;
  created_at: string;
}

export interface ActionDetail extends ActionSummary {
  description?: string;
  client_id: number;
}

export interface ActionWriteInput {
  description?: string;
  action_date?: string | null;
  next_action_date?: string | null;
  next_step?: string;
  completed?: boolean;
}

export interface DocumentSummary {
  id: number;
  client: number;
  original_name: string | null;
  description: string | null;
  stored_key: string;
  mime_type: string;
  size_bytes: number;
  uploaded_at: string;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface ApiError {
  status: number;
  detail?: string;
  errors?: Record<string, string[] | string>;
}
