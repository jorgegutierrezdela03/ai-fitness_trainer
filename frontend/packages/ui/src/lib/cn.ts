import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/** Joins conditional classes and resolves Tailwind conflicts, keeping the last one. */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
