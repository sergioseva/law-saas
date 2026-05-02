/**
 * Resolve the API base URL.
 *
 * Dev: Next.js runs at <subdomain>.lvh.me:3000, Django at <subdomain>.lvh.me:8000.
 *      Same hostname, different port — TenantMiddleware reads the firm from Host.
 * Prod: NEXT_PUBLIC_API_BASE is set to https://api.lawsaas.app (or similar).
 *       NOTE: cross-subdomain calls there mean Django sees Host=api.lawsaas.app,
 *       which is in the reserved/public list, so request.firm is None. Phase 5
 *       hardening adds an X-Firm-Subdomain header that the middleware honors.
 */
export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const override = process.env.NEXT_PUBLIC_API_BASE;
    if (override) return override;
    const { protocol, hostname } = window.location;
    return `${protocol}//${hostname}:8000`;
  }
  return process.env.NEXT_PUBLIC_API_BASE ?? "http://api:8000";
}

export function getCurrentSubdomain(): string {
  if (typeof window === "undefined") return "";
  const host = window.location.hostname;
  const parts = host.split(".");
  if (parts.length < 2) return "";
  // For lvh.me: ['acme', 'lvh', 'me'] → 'acme'
  // For lawsaas.app: ['acme', 'lawsaas', 'app'] → 'acme'
  // For lvh.me alone (no subdomain): ['lvh', 'me'] → '' (sub === base label)
  return parts.length >= 3 ? parts[0] : "";
}

export const PUBLIC_SUBDOMAINS = new Set(["", "app", "www"]);

export function isPublicHost(): boolean {
  const sub = getCurrentSubdomain();
  return PUBLIC_SUBDOMAINS.has(sub);
}

export function getPublicSignupUrl(): string {
  if (typeof window === "undefined") return "/signup";
  const base = process.env.NEXT_PUBLIC_BASE_DOMAIN ?? "lvh.me:3000";
  const protocol = window.location.protocol;
  return `${protocol}//app.${base}/signup`;
}

export function getFirmUrl(subdomain: string): string {
  if (typeof window === "undefined") return `https://${subdomain}.lawsaas.app`;
  const base = process.env.NEXT_PUBLIC_BASE_DOMAIN ?? "lvh.me:3000";
  const protocol = window.location.protocol;
  return `${protocol}//${subdomain}.${base}`;
}
