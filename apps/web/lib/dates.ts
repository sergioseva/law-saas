/**
 * Date conversion helpers — ISO yyyy-mm-dd ↔ AR dd/mm/yyyy.
 *
 * Internal/storage format is always ISO. Display/input format is always AR.
 */

const ISO_RE = /^(\d{4})-(\d{2})-(\d{2})$/;
const AR_RE = /^(\d{2})\/(\d{2})\/(\d{4})$/;

export function isoToAr(iso: string | null | undefined): string {
  if (!iso) return "";
  const m = ISO_RE.exec(iso);
  if (!m) return "";
  return `${m[3]}/${m[2]}/${m[1]}`;
}

export function isValidCalendarDate(year: number, month: number, day: number): boolean {
  if (year < 1000 || year > 9999) return false;
  if (month < 1 || month > 12) return false;
  if (day < 1 || day > 31) return false;
  const d = new Date(year, month - 1, day);
  return (
    d.getFullYear() === year &&
    d.getMonth() === month - 1 &&
    d.getDate() === day
  );
}

export function arToIso(ar: string): string {
  const m = AR_RE.exec(ar);
  if (!m) return "";
  const day = Number(m[1]);
  const month = Number(m[2]);
  const year = Number(m[3]);
  if (!isValidCalendarDate(year, month, day)) return "";
  return `${m[3]}-${m[2]}-${m[1]}`;
}

/** Auto-format a typed string into "dd/mm/yyyy" with slashes inserted. */
export function formatTyping(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
}

/** Build a local-tz Date from a yyyy-mm-dd string (avoids UTC parsing surprises). */
export function isoToDate(iso: string | null | undefined): Date | undefined {
  if (!iso) return undefined;
  const m = ISO_RE.exec(iso);
  if (!m) return undefined;
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
}

/** Inverse of isoToDate — render a Date as yyyy-mm-dd in its local-tz components. */
export function dateToIso(date: Date): string {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, "0");
  const d = String(date.getDate()).padStart(2, "0");
  return `${y}-${m}-${d}`;
}
