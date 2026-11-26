import type { ReactNode } from "react";
import type { ViewProps } from "react-native";

export type GlassTint = "auto" | "light" | "dark";

export interface GlassSurfaceProps extends ViewProps {
  /** Blur strength from 0 to 100. */
  intensity?: number;
  /** `auto` follows the active colour scheme. */
  tint?: GlassTint;
  /** Layout, radius, border and padding of the surface. */
  className?: string;
  /** Translucent fill drawn above the blur. Overrides the default for the tint. */
  surfaceClassName?: string;
  /** Draws the light reflection on the top and left edges. */
  highlight?: boolean;
  children?: ReactNode;
}

export const SURFACE_BY_TINT: Record<GlassTint, string> = {
  auto: "bg-white/30 dark:bg-slate-900/40",
  light: "bg-white/30",
  dark: "bg-slate-900/40",
};

export const GLASS_BASE_CLASS = "overflow-hidden border border-white/20";
