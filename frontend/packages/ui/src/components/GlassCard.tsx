import { cva, type VariantProps } from "class-variance-authority";
import { LinearGradient } from "expo-linear-gradient";
import type { ReactNode } from "react";
import { Pressable, type PressableProps, StyleSheet, type ViewProps } from "react-native";
import Animated from "react-native-reanimated";

import { GlassSurface } from "../glass/GlassSurface";
import { usePressAnimation } from "../hooks/usePressAnimation";
import { cn } from "../lib/cn";
import { gradients } from "../theme/tokens";

export const glassCardVariants = cva("rounded-3xl p-5", {
  variants: {
    intensity: {
      subtle: "border-white/10",
      medium: "border-white/20",
      heavy: "border-white/30",
    },
  },
  defaultVariants: { intensity: "medium" },
});

type Intensity = NonNullable<VariantProps<typeof glassCardVariants>["intensity"]>;

const SURFACE: Record<Intensity, string> = {
  subtle: "bg-white/10 dark:bg-slate-900/20",
  medium: "bg-white/30 dark:bg-slate-900/40",
  heavy: "bg-white/50 dark:bg-slate-900/60",
};

const BLUR: Record<Intensity, number> = { subtle: 20, medium: 45, heavy: 80 };

export interface GlassCardProps extends ViewProps, VariantProps<typeof glassCardVariants> {
  /** Replaces the border with a luminous blue to green gradient. */
  glow?: boolean;
  /** Makes the card pressable, with spring feedback. */
  onPress?: PressableProps["onPress"];
  className?: string;
  children?: ReactNode;
}

export function GlassCard({
  intensity,
  glow = false,
  onPress,
  className,
  children,
  ...viewProps
}: GlassCardProps) {
  const level = intensity ?? "medium";
  const press = usePressAnimation({ pressedScale: 0.98, hoverScale: 1.01 });

  const surface = (
    <GlassSurface
      intensity={BLUR[level]}
      surfaceClassName={SURFACE[level]}
      // Inside the gradient frame, the inner radius is 1 px smaller than the outer one.
      className={cn(glassCardVariants({ intensity: level }), glow && "rounded-[23px] border-0", className)}
      {...viewProps}
    >
      {children}
    </GlassSurface>
  );

  const framed = glow ? (
    <LinearGradient
      colors={gradients.brandBorder}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.glowFrame}
    >
      {surface}
    </LinearGradient>
  ) : (
    surface
  );

  if (!onPress) return framed;

  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      onPressIn={press.onPressIn}
      onPressOut={press.onPressOut}
      onHoverIn={press.onHoverIn}
      onHoverOut={press.onHoverOut}
    >
      <Animated.View style={press.animatedStyle}>{framed}</Animated.View>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  glowFrame: {
    borderRadius: 24,
    padding: 1,
    boxShadow: "0 0 28px rgba(34, 211, 238, 0.22)",
  },
});
