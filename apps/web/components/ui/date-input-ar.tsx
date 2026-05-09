"use client";

import { forwardRef, useEffect, useState } from "react";

import { cn } from "../../lib/utils";

/**
 * Date input that always displays dd/mm/yyyy (Argentina format), regardless
 * of the browser/OS locale.
 *
 * Internally it stores ISO yyyy-mm-dd (so the form field's value matches
 * what the API expects). The component:
 *   - Renders a text input with auto-inserting slashes as the user types
 *   - Validates the typed value parses to a real calendar date
 *   - Emits an empty string while the input is incomplete or invalid
 *
 * Integrates with react-hook-form via <Controller> — see ClientForm.
 */

const ISO_RE = /^(\d{4})-(\d{2})-(\d{2})$/;
const AR_RE = /^(\d{2})\/(\d{2})\/(\d{4})$/;

export interface DateInputArProps {
  id?: string;
  name?: string;
  value?: string | null;
  onChange?: (iso: string) => void;
  onBlur?: () => void;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
}

function isoToAr(iso: string | null | undefined): string {
  if (!iso) return "";
  const m = ISO_RE.exec(iso);
  if (!m) return "";
  return `${m[3]}/${m[2]}/${m[1]}`;
}

function isValidCalendarDate(year: number, month: number, day: number): boolean {
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

function arToIso(ar: string): string {
  const m = AR_RE.exec(ar);
  if (!m) return "";
  const day = Number(m[1]);
  const month = Number(m[2]);
  const year = Number(m[3]);
  if (!isValidCalendarDate(year, month, day)) return "";
  return `${m[3]}-${m[2]}-${m[1]}`;
}

function formatTyping(raw: string): string {
  const digits = raw.replace(/\D/g, "").slice(0, 8);
  if (digits.length <= 2) return digits;
  if (digits.length <= 4) return `${digits.slice(0, 2)}/${digits.slice(2)}`;
  return `${digits.slice(0, 2)}/${digits.slice(2, 4)}/${digits.slice(4)}`;
}

export const DateInputAr = forwardRef<HTMLInputElement, DateInputArProps>(
  ({ id, name, value, onChange, onBlur, disabled, className, placeholder }, ref) => {
    const [display, setDisplay] = useState<string>(() => isoToAr(value));

    // Sync external value changes (e.g. form reset, async load) into local display.
    useEffect(() => {
      const expected = isoToAr(value);
      // Don't clobber a partial entry the user is currently typing.
      const currentIso = arToIso(display);
      if (currentIso !== (value ?? "")) {
        setDisplay(expected);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [value]);

    function handleChange(e: React.ChangeEvent<HTMLInputElement>) {
      const next = formatTyping(e.target.value);
      setDisplay(next);
      const iso = arToIso(next);
      onChange?.(iso);
    }

    return (
      <input
        ref={ref}
        id={id}
        name={name}
        type="text"
        inputMode="numeric"
        autoComplete="off"
        placeholder={placeholder ?? "dd/mm/aaaa"}
        maxLength={10}
        disabled={disabled}
        value={display}
        onChange={handleChange}
        onBlur={onBlur}
        className={cn(
          "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm tabular-nums text-slate-900 placeholder:text-slate-400 focus:border-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-700 disabled:opacity-50",
          className,
        )}
      />
    );
  },
);
DateInputAr.displayName = "DateInputAr";
