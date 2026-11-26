import { useCallback } from "react";
import {
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  type WithSpringConfig,
  withSpring,
} from "react-native-reanimated";

export const PRESS_SPRING: WithSpringConfig = {
  damping: 14,
  stiffness: 260,
  mass: 0.6,
  reduceMotion: ReduceMotion.System,
};

export interface PressAnimationOptions {
  pressedScale?: number;
  hoverScale?: number;
  disabled?: boolean;
}

/** Spring scale for press (touch and click) and hover (web and pointer devices). */
export function usePressAnimation({
  pressedScale = 0.96,
  hoverScale = 1.02,
  disabled = false,
}: PressAnimationOptions = {}) {
  const scale = useSharedValue(1);

  // The dependency array keeps the style reactive on web, where no worklets plugin runs.
  const animatedStyle = useAnimatedStyle(() => ({ transform: [{ scale: scale.get() }] }), [scale]);

  const animateTo = useCallback(
    (value: number) => {
      scale.set(withSpring(value, PRESS_SPRING));
    },
    [scale],
  );

  return {
    animatedStyle,
    onPressIn: () => {
      if (!disabled) animateTo(pressedScale);
    },
    onPressOut: () => animateTo(1),
    onHoverIn: () => {
      if (!disabled) animateTo(hoverScale);
    },
    onHoverOut: () => animateTo(1),
  };
}
