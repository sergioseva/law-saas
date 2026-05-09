import clsx, { type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

const DATE_ONLY_RE = /^(\d{4})-(\d{2})-(\d{2})$/;

/**
 * Format a date string in dd/mm/yyyy (Argentina format).
 *
 * IMPORTANT: a plain "yyyy-mm-dd" string is parsed by `new Date()` as UTC
 * midnight, which `.getDate()` then renders in the *local* timezone — that
 * flips the day in any timezone west of UTC (e.g. Argentina UTC-3 makes
 * 1990-05-15 display as 14/05/1990). Parse the components manually to
 * preserve the date as authored.
 */
export function formatDateAr(value: string | null | undefined): string {
  if (!value) return "—";
  const dateMatch = DATE_ONLY_RE.exec(value);
  if (dateMatch) {
    const [, y, m, d] = dateMatch;
    return `${d}/${m}/${y}`;
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  return `${day}/${month}/${year}`;
}

/**
 * Format an ISO datetime as dd/mm/yyyy hh:mm (Argentina format, local time).
 *
 * Datetimes from Django carry timezone info, so `new Date()` parses them
 * unambiguously and renders in the user's local timezone — no special-case
 * needed for them.
 */
export function formatDateTimeAr(value: string | null | undefined): string {
  if (!value) return "—";
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  const day = String(d.getDate()).padStart(2, "0");
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const year = d.getFullYear();
  const hh = String(d.getHours()).padStart(2, "0");
  const mm = String(d.getMinutes()).padStart(2, "0");
  return `${day}/${month}/${year} ${hh}:${mm}`;
}
