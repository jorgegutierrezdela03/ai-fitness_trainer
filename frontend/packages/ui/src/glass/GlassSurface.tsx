import { BlurView } from "expo-blur";
import { useColorScheme } from "nativewind";
import { StyleSheet, View } from "react-native";

import { cn } from "../lib/cn";
import { FILL } from "../theme/layout";
import { GlassHighlight } from "./GlassHighlight";
import { useGlassBlurTarget } from "./GlassProvider";
import { GLASS_BASE_CLASS, type GlassSurfaceProps, SURFACE_BY_TINT } from "./types";

/**
 * iOS and Android: native blur with `BlurView`, a translucent fill and the edge highlight.
 * Web resolves `GlassSurface.web.tsx` instead.
 */
export function GlassSurface({
  intensity = 40,
  tint = "auto",
  className,
  surfaceClassName,
  highlight = true,
  children,
  ...viewProps
}: GlassSurfaceProps) {
  const { colorScheme } = useColorScheme();
  const blurTarget = useGlassBlurTarget();
  const blurTint = tint === "auto" ? (colorScheme === "dark" ? "dark" : "light") : tint;

  return (
    <View className={cn(GLASS_BASE_CLASS, className)} {...viewProps}>
      <BlurView
        intensity={intensity}
        tint={blurTint}
        // Without a target, Android renders a translucent view instead of a real blur.
        blurTarget={blurTarget ?? undefined}
        blurMethod={blurTarget ? "dimezisBlurViewSdk31Plus" : "none"}
        style={styles.layer}
      />
      <View className={cn("pointer-events-none absolute inset-0", SURFACE_BY_TINT[tint], surfaceClassName)} />
      {highlight ? <GlassHighlight /> : null}
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  layer: { ...FILL, pointerEvents: "none" },
});
