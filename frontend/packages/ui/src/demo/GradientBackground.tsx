import { LinearGradient } from "expo-linear-gradient";
import { useColorScheme } from "nativewind";
import { useEffect } from "react";
import { type DimensionValue, Platform, StyleSheet, View } from "react-native";
import Animated, {
  cancelAnimation,
  Easing,
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withRepeat,
  withTiming,
} from "react-native-reanimated";

import { type GradientColors, gradients, palette } from "../theme/tokens";

interface BlobProps {
  colors: GradientColors;
  size: number;
  left: DimensionValue;
  top: DimensionValue;
  drift: number;
  duration: number;
  animated: boolean;
}

function Blob({ colors, size, left, top, drift, duration, animated }: BlobProps) {
  const progress = useSharedValue(0);

  useEffect(() => {
    if (!animated) return;
    progress.set(
      withRepeat(
        withTiming(1, { duration, easing: Easing.inOut(Easing.sin), reduceMotion: ReduceMotion.System }),
        -1,
        true,
      ),
    );
    return () => cancelAnimation(progress);
  }, [animated, duration, progress]);

  const driftStyle = useAnimatedStyle(
    () => ({
      transform: [
        { translateX: drift * progress.get() },
        { translateY: -drift * 0.6 * progress.get() },
        { scale: 1 + 0.08 * progress.get() },
      ],
    }),
    [drift, progress],
  );

  return (
    <Animated.View
      style={[styles.blob, { left, top, width: size, height: size, borderRadius: size / 2 }, driftStyle]}
    >
      <LinearGradient colors={colors} start={{ x: 0.2, y: 0.1 }} end={{ x: 0.9, y: 0.9 }} style={StyleSheet.absoluteFill} />
    </Animated.View>
  );
}

export interface GradientBackgroundProps {
  /**
   * Slow drift of the colour blobs. Disabled on Android by default, because every frame
   * behind a blur forces the blur to be recalculated.
   */
  animated?: boolean;
}

/** Organic blue and green backdrop that makes the glass translucency visible. */
export function GradientBackground({ animated = Platform.OS !== "android" }: GradientBackgroundProps) {
  const { colorScheme } = useColorScheme();
  const isDark = colorScheme === "dark";

  return (
    <View style={StyleSheet.absoluteFill}>
      <LinearGradient
        colors={isDark ? gradients.backdropDark : gradients.backdropLight}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />
      <Blob
        colors={[palette.ocean["500"], "rgba(14,165,233,0)"]}
        size={420}
        left="-15%"
        top="-8%"
        drift={48}
        duration={9000}
        animated={animated}
      />
      <Blob
        colors={[palette.mint["400"], "rgba(52,211,153,0)"]}
        size={360}
        left="45%"
        top="28%"
        drift={-40}
        duration={11000}
        animated={animated}
      />
      <Blob
        colors={[palette.ocean["600"], palette.cyan["400"], "rgba(34,211,238,0)"]}
        size={300}
        left="-5%"
        top="62%"
        drift={36}
        duration={13000}
        animated={animated}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  blob: {
    position: "absolute",
    overflow: "hidden",
    opacity: 0.55,
    ...Platform.select({ web: { filter: "blur(72px)" }, default: {} }),
  },
});
