import { cva } from "class-variance-authority";
import { useColorScheme } from "nativewind";
import type { ComponentRef, ReactNode, Ref } from "react";
import { StyleSheet, Text, TextInput, type TextInputProps, View } from "react-native";
import Animated, {
  ReduceMotion,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
} from "react-native-reanimated";

import { GlassSurface } from "../glass/GlassSurface";
import { cn } from "../lib/cn";
import { FILL } from "../theme/layout";

const FOCUS_TIMING = { duration: 180, reduceMotion: ReduceMotion.System };

export const inputFieldVariants = cva("min-h-12 flex-row items-center rounded-2xl px-4", {
  variants: {
    state: {
      default: "border-white/20",
      error: "border-rose-400/60",
    },
    disabled: {
      true: "opacity-50",
      false: "",
    },
  },
  defaultVariants: { state: "default", disabled: false },
});

export interface InputProps extends Omit<TextInputProps, "style"> {
  label?: string;
  hint?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  /** Classes for the text itself. */
  className?: string;
  /** Classes for the wrapper that holds label, field and message. */
  containerClassName?: string;
  ref?: Ref<ComponentRef<typeof TextInput>>;
}

export function Input({
  label,
  hint,
  error,
  leftIcon,
  rightIcon,
  className,
  containerClassName,
  editable = true,
  onFocus,
  onBlur,
  ref,
  ...textInputProps
}: InputProps) {
  const { colorScheme } = useColorScheme();
  const focus = useSharedValue(0);
  const glowStyle = useAnimatedStyle(() => ({ opacity: focus.get() }), [focus]);
  const hasError = Boolean(error);

  return (
    <View className={cn("w-full gap-1.5", containerClassName)}>
      {label ? (
        <Text className="ml-1 text-sm font-medium text-slate-700 dark:text-slate-200">{label}</Text>
      ) : null}

      <View>
        <GlassSurface
          intensity={30}
          highlight={false}
          className={inputFieldVariants({ state: hasError ? "error" : "default", disabled: !editable })}
        >
          {leftIcon ? <View className="mr-2">{leftIcon}</View> : null}
          <TextInput
            ref={ref}
            editable={editable}
            accessibilityLabel={label}
            accessibilityHint={error ?? hint}
            placeholderTextColor={colorScheme === "dark" ? "rgba(226,232,240,0.45)" : "rgba(15,23,42,0.4)"}
            className={cn("flex-1 py-3 text-base text-slate-900 dark:text-white web:outline-none", className)}
            {...textInputProps}
            onFocus={(event) => {
              focus.set(withTiming(1, FOCUS_TIMING));
              onFocus?.(event);
            }}
            onBlur={(event) => {
              focus.set(withTiming(0, FOCUS_TIMING));
              onBlur?.(event);
            }}
          />
          {rightIcon ? <View className="ml-2">{rightIcon}</View> : null}
        </GlassSurface>

        <Animated.View style={[styles.glow, hasError ? styles.glowError : styles.glowFocus, glowStyle]} />
      </View>

      {hasError ? (
        <Text className="ml-1 text-xs text-rose-600 dark:text-rose-400" accessibilityLiveRegion="polite">
          {error}
        </Text>
      ) : hint ? (
        <Text className="ml-1 text-xs text-slate-500 dark:text-slate-400">{hint}</Text>
      ) : null}
    </View>
  );
}

const styles = StyleSheet.create({
  glow: {
    ...FILL,
    borderRadius: 16,
    borderWidth: 1.5,
    pointerEvents: "none",
  },
  // Cyan edge with a mint halo.
  glowFocus: {
    borderColor: "rgba(34, 211, 238, 0.9)",
    boxShadow: "0 0 18px rgba(52, 211, 153, 0.35)",
  },
  glowError: {
    borderColor: "rgba(251, 113, 133, 0.9)",
    boxShadow: "0 0 18px rgba(251, 113, 133, 0.35)",
  },
});
