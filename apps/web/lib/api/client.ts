/**
 * Fetch wrapper for the Django API.
 *
 * Handles:
 *   - cookie-based session auth (credentials: include)
 *   - CSRF: reads csrftoken cookie + attaches X-CSRFToken header on mutating verbs
 *   - typed ApiError shape
 *
 * The csrftoken cookie is set on the first GET to /api/auth/csrf — call
 * `ensureCsrf()` once at app boot.
 */
import type { ApiError } from "./types";
import { getApiBase } from "../env";

const MUTATING_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function readCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const match = document.cookie.match(
    new RegExp("(?:^|; )" + name.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "=([^;]*)"),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export class HttpError extends Error implements ApiError {
  status: number;
  detail?: string;
  errors?: Record<string, string[] | string>;

  constructor(status: number, body: unknown) {
    let detail: string | undefined;
    let errors: Record<string, string[] | string> | undefined;
    if (body && typeof body === "object") {
      const b = body as Record<string, unknown>;
      if (typeof b.detail === "string") detail = b.detail;
      // Anything that's not `detail` is a field error from DRF.
      const rest: Record<string, string[] | string> = {};
      for (const [k, v] of Object.entries(b)) {
        if (k === "detail") continue;
        if (Array.isArray(v) && v.every((x) => typeof x === "string")) {
          rest[k] = v as string[];
        } else if (typeof v === "string") {
          rest[k] = v;
        }
      }
      if (Object.keys(rest).length > 0) errors = rest;
    }
    super(detail ?? `HTTP ${status}`);
    this.status = status;
    this.detail = detail;
    this.errors = errors;
  }
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

export async function api<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const method = (options.method ?? "GET").toUpperCase();
  const url = new URL(path, getApiBase());
  if (options.query) {
    for (const [k, v] of Object.entries(options.query)) {
      if (v === undefined || v === null) continue;
      url.searchParams.set(k, String(v));
    }
  }

  const headers = new Headers({ Accept: "application/json" });
  if (options.body !== undefined) {
    headers.set("Content-Type", "application/json");
  }
  if (MUTATING_METHODS.has(method)) {
    const csrf = readCookie("csrftoken");
    if (csrf) headers.set("X-CSRFToken", csrf);
  }

  const response = await fetch(url.toString(), {
    method,
    headers,
    credentials: "include",
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    signal: options.signal,
  });

  if (response.status === 204) return undefined as T;

  let payload: unknown = null;
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    payload = await response.json();
  } else {
    payload = await response.text();
  }

  if (!response.ok) {
    throw new HttpError(response.status, payload);
  }

  return payload as T;
}

let _csrfReady: Promise<void> | null = null;

export function ensureCsrf(): Promise<void> {
  if (!_csrfReady) {
    _csrfReady = api<{ csrfToken: string }>("/api/auth/csrf").then(() => undefined);
  }
  return _csrfReady;
}
