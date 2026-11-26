import { Pressable, Text, View } from "react-native";
import Animated from "react-native-reanimated";

import { usePressAnimation } from "../hooks/usePressAnimation";
import { cn } from "../lib/cn";

export interface ChipProps {
  label: string;
  selected?: boolean;
  disabled?: boolean;
  onPress?: () => void;
  className?: string;
}

/**
 * Selectable pill. It uses a translucent fill without blur, because forms render many chips
 * and each blur has a cost, especially on Android.
 */
export function Chip({ label, selected = false, disabled = false, onPress, className }: ChipProps) {
  const press = usePressAnimation({ disabled, pressedScale: 0.94, hoverScale: 1.04 });

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected, disabled }}
      disabled={disabled}
      onPress={onPress}
      onPressIn={press.onPressIn}
      onPressOut={press.onPressOut}
      onHoverIn={press.onHoverIn}
      onHoverOut={press.onHoverOut}
      className={cn(disabled && "opacity-40", className)}
    >
      <Animated.View style={press.animatedStyle}>
        <View
          className={cn(
            "rounded-full border px-4 py-2",
            selected
              ? "border-cyan-300/70 bg-cyan-400/20"
              : "border-white/15 bg-white/40 dark:bg-white/5",
          )}
        >
          <Text
            className={cn(
              "text-sm",
              selected
                ? "font-semibold text-slate-900 dark:text-white"
                : "text-slate-700 dark:text-slate-300",
            )}
          >
            {label}
          </Text>
        </View>
      </Animated.View>
    </Pressable>
  );
}
