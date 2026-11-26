import { cva, type VariantProps } from "class-variance-authority";
import { type ReactNode, useEffect } from "react";
import { StyleSheet, Text, View, type ViewProps } from "react-native";
import Animated, {
  cancelAnimation,
  Easing,
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";

import { GlassSurface } from "../glass/GlassSurface";
import { cn } from "../lib/cn";
import { palette } from "../theme/tokens";

export const badgeVariants = cva("flex-row items-center gap-1.5 self-start rounded-full px-3 py-1", {
  variants: {
    variant: {
      info: "border-ocean-400/40",
      success: "border-mint-400/40",
      glow: "border-cyan-300/50",
    },
  },
  defaultVariants: { variant: "info" },
});

export const badgeTextVariants = cva("text-xs font-semibold", {
  variants: {
    variant: {
      info: "text-ocean-700 dark:text-ocean-300",
      success: "text-mint-700 dark:text-mint-300",
      glow: "text-cyan-700 dark:text-cyan-200",
    },
  },
  defaultVariants: { variant: "info" },
});

type Variant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

const SURFACE: Record<Variant, string> = {
  info: "bg-ocean-500/15",
  success: "bg-mint-500/15",
  glow: "bg-cyan-400/10",
};

const DOT_COLOR: Record<Variant, string> = {
  info: palette.ocean["400"],
  success: palette.mint["400"],
  glow: palette.mint["400"],
};

export interface BadgeProps extends ViewProps, VariantProps<typeof badgeVariants> {
  children: ReactNode;
  /** Pulsing indicator. Shown by default for `glow`. */
  dot?: boolean;
  className?: string;
  textClassName?: string;
}

function PulsingDot({ color }: { color: string }) {
  const progress = useSharedValue(0);

  useEffect(() => {
    progress.set(
      withRepeat(
        withTiming(1, { duration: 1400, easing: Easing.out(Easing.ease), reduceMotion: ReduceMotion.System }),
        -1,
        false,
      ),
    );
    return () => cancelAnimation(progress);
  }, [progress]);

  const ringStyle = useAnimatedStyle(
    () => ({
      opacity: 0.6 * (1 - progress.get()),
      transform: [{ scale: 1 + progress.get() * 1.6 }],
    }),
    [progress],
  );

  return (
    <View style={styles.dotBox}>
      <Animated.View style={[styles.dot, styles.ring, { backgroundColor: color }, ringStyle]} />
      <View style={[styles.dot, { backgroundColor: color }]} />
    </View>
  );
}

export function Badge({ variant, children, dot, className, textClassName, ...viewProps }: BadgeProps) {
  const resolved: Variant = variant ?? "info";
  const showDot = dot ?? resolved === "glow";

  return (
    <GlassSurface
      intensity={20}
      highlight={false}
      surfaceClassName={SURFACE[resolved]}
      className={cn(badgeVariants({ variant: resolved }), className)}
      {...viewProps}
    >
      {showDot ? <PulsingDot color={DOT_COLOR[resolved]} /> : null}
      {typeof children === "string" ? (
        <Text className={cn(badgeTextVariants({ variant: resolved }), textClassName)}>{children}</Text>
      ) : (
        children
      )}
    </GlassSurface>
  );
}

const styles = StyleSheet.create({
  dotBox: { width: 8, height: 8, alignItems: "center", justifyContent: "center" },
  dot: { width: 8, height: 8, borderRadius: 4 },
  ring: { position: "absolute" },
});
