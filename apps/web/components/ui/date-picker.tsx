"use client";

import { es } from "date-fns/locale";
import { forwardRef, useEffect, useRef, useState } from "react";
import { DayPicker } from "react-day-picker";
import "react-day-picker/style.css";

import { arToIso, dateToIso, formatTyping, isoToAr, isoToDate } from "../../lib/dates";
import { cn } from "../../lib/utils";

/**
 * Date picker that always speaks ISO yyyy-mm-dd to its consumer (form state,
 * API) but always shows the user dd/mm/yyyy + a Spanish-locale calendar.
 *
 * Two ways to enter a date:
 *   1. Type — auto-inserts slashes, validates real calendar date.
 *   2. Click the calendar icon — popover with month/year navigation.
 *
 * Wire via react-hook-form's <Controller>. See ClientForm / ActionForm.
 */

export interface DatePickerProps {
  id?: string;
  name?: string;
  value?: string | null;
  onChange?: (iso: string) => void;
  onBlur?: () => void;
  disabled?: boolean;
  className?: string;
  placeholder?: string;
}

export const DatePicker = forwardRef<HTMLInputElement, DatePickerProps>(
  ({ id, name, value, onChange, onBlur, disabled, className, placeholder }, ref) => {
    const [text, setText] = useState<string>(() => isoToAr(value));
    const [open, setOpen] = useState(false);
    const wrapperRef = useRef<HTMLDivElement>(null);

    // Sync external value changes into local display unless the user is mid-typing.
    useEffect(() => {
      const desired = isoToAr(value);
      const currentIso = arToIso(text);
      if (currentIso !== (value ?? "")) {
        setText(desired);
      }
      // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [value]);

    // Close popover on outside click + Escape.
    useEffect(() => {
      if (!open) return;
      function handleMouseDown(e: MouseEvent) {
        if (
          wrapperRef.current &&
          !wrapperRef.current.contains(e.target as Node)
        ) {
          setOpen(false);
        }
      }
      function handleKey(e: KeyboardEvent) {
        if (e.key === "Escape") setOpen(false);
      }
      document.addEventListener("mousedown", handleMouseDown);
      document.addEventListener("keydown", handleKey);
      return () => {
        document.removeEventListener("mousedown", handleMouseDown);
        document.removeEventListener("keydown", handleKey);
      };
    }, [open]);

    function handleTextChange(e: React.ChangeEvent<HTMLInputElement>) {
      const next = formatTyping(e.target.value);
      setText(next);
      onChange?.(arToIso(next));
    }

    function handleSelect(date: Date | undefined) {
      if (!date) {
        setText("");
        onChange?.("");
      } else {
        const iso = dateToIso(date);
        setText(isoToAr(iso));
        onChange?.(iso);
      }
      setOpen(false);
    }

    const selectedDate = isoToDate(value ?? undefined);

    return (
      <div ref={wrapperRef} className={cn("relative", className)}>
        <div className="flex">
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
            value={text}
            onChange={handleTextChange}
            onBlur={onBlur}
            className="h-10 w-full rounded-l-md border border-r-0 border-slate-300 bg-white px-3 text-sm tabular-nums text-slate-900 placeholder:text-slate-400 focus:border-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-700 disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setOpen((v) => !v)}
            disabled={disabled}
            aria-label="Abrir calendario"
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-r-md border border-slate-300 bg-white text-slate-600 hover:bg-slate-50 focus:outline-none focus:ring-1 focus:ring-slate-700 disabled:opacity-50"
          >
            <CalendarIcon />
          </button>
        </div>

        {open ? (
          <div className="absolute left-0 top-full z-50 mt-1 rounded-md border border-slate-200 bg-white p-2 shadow-lg">
            <DayPicker
              mode="single"
              selected={selectedDate}
              onSelect={handleSelect}
              locale={es}
              captionLayout="dropdown"
              startMonth={new Date(1900, 0)}
              endMonth={new Date(2100, 11)}
              defaultMonth={selectedDate ?? new Date()}
              weekStartsOn={1}
              showOutsideDays
            />
          </div>
        ) : null}
      </div>
    );
  },
);
DatePicker.displayName = "DatePicker";

function CalendarIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <rect x="3" y="4" width="18" height="18" rx="2" ry="2" />
      <line x1="16" y1="2" x2="16" y2="6" />
      <line x1="8" y1="2" x2="8" y2="6" />
      <line x1="3" y1="10" x2="21" y2="10" />
    </svg>
  );
}
