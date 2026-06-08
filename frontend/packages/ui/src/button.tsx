import type { ButtonHTMLAttributes } from "react";

import { cn } from "@yurpass/utils";

export type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement>;

/** Placeholder button — design system foundation only. */
export function Button({ className, children, ...props }: ButtonProps) {
  return (
    <button
      type="button"
      className={cn(
        "inline-flex items-center justify-center rounded-md bg-brand px-4 py-2 text-sm font-medium text-brand-foreground",
        className,
      )}
      {...props}
    >
      {children}
    </button>
  );
}
