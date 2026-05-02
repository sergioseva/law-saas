import { type LabelHTMLAttributes, forwardRef } from "react";

import { cn } from "../../lib/utils";

export const Label = forwardRef<HTMLLabelElement, LabelHTMLAttributes<HTMLLabelElement>>(
  ({ className, ...rest }, ref) => (
    <label
      ref={ref}
      className={cn("text-sm font-medium text-slate-700", className)}
      {...rest}
    />
  ),
);
Label.displayName = "Label";
