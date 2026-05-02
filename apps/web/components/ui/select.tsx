import { type SelectHTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Select = forwardRef<HTMLSelectElement, SelectHTMLAttributes<HTMLSelectElement>>(
  ({ className, ...rest }, ref) => (
    <select
      ref={ref}
      className={cn(
        "h-10 w-full rounded-md border border-slate-300 bg-white px-3 text-sm text-slate-900 focus:border-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-700 disabled:opacity-50",
        className,
      )}
      {...rest}
    />
  ),
);
Select.displayName = "Select";
