import { View } from "react-native";

import { cn } from "../lib/cn";
import { GlassHighlight } from "./GlassHighlight";
import { GLASS_BASE_CLASS, type GlassSurfaceProps, SURFACE_BY_TINT } from "./types";

function blurClass(intensity: number): string {
  if (intensity <= 0) return "";
  if (intensity < 25) return "backdrop-blur-md";
  if (intensity < 60) return "backdrop-blur-xl";
  return "backdrop-blur-3xl";
}

/** Web: CSS `backdrop-filter`, which blurs whatever is behind the element without a target. */
export function GlassSurface({
  intensity = 40,
  tint = "auto",
  className,
  surfaceClassName,
  highlight = true,
  children,
  ...viewProps
}: GlassSurfaceProps) {
  return (
    <View
      className={cn(
        GLASS_BASE_CLASS,
        blurClass(intensity),
        intensity > 0 && "backdrop-saturate-150",
        SURFACE_BY_TINT[tint],
        surfaceClassName,
        className,
      )}
      {...viewProps}
    >
      {highlight ? <GlassHighlight /> : null}
      {children}
    </View>
  );
}
