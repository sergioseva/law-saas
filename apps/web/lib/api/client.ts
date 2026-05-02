/**
 * Thin fetch wrapper for the Django API.
 *
 * Phase 3 will replace this with a generated client from the OpenAPI schema
 * (see drf-spectacular + openapi-typescript-codegen). For now, this is a
 * placeholder that handles cookie-based auth and CSRF.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://api.lvh.me:8000";

export async function api(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  return fetch(`${API_BASE}${path}`, {
    ...init,
    credentials: "include",
    headers,
  });
}
