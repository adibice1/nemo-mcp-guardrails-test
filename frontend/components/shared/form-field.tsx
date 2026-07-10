import { type ReactNode } from "react";
import { cn } from "@/lib/utils";

type FormFieldProps = {
  label: ReactNode;
  required?: boolean;
  className?: string;
  children: ReactNode;
};

export function FormField({
  label,
  required = false,
  className,
  children
}: FormFieldProps) {
  return (
    <label className={cn("block text-sm font-bold text-gms-text", className)}>
      <span className="inline-flex items-center gap-1 whitespace-nowrap">
        {label}
        {required && <span className="text-gms-danger">*</span>}
      </span>
      <div className="mt-2">{children}</div>
    </label>
  );
}
