import { cn } from "../../lib/utils";

export function FieldError({ message, className }: { message?: string; className?: string }) {
  if (!message) return null;
  return <p className={cn("mt-1 text-sm text-red-600", className)}>{message}</p>;
}
