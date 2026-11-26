import { cva, type VariantProps } from "class-variance-authority";
import { LinearGradient } from "expo-linear-gradient";
import type { ReactNode } from "react";
import { ActivityIndicator, Pressable, type PressableProps, StyleSheet, Text, View } from "react-native";
import Animated from "react-native-reanimated";

import { GlassSurface } from "../glass/GlassSurface";
import { usePressAnimation } from "../hooks/usePressAnimation";
import { cn } from "../lib/cn";
import { gradients, palette } from "../theme/tokens";

export const buttonVariants = cva(
  "flex-row items-center justify-center gap-2 overflow-hidden rounded-full border",
  {
    variants: {
      variant: {
        primary: "border-white/25",
        glass: "border-cyan-300/40",
        ghost: "border-transparent",
      },
      size: {
        sm: "h-9 px-4",
        md: "h-11 px-5",
        lg: "h-14 px-7",
      },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export const buttonTextVariants = cva("font-semibold tracking-tight", {
  variants: {
    variant: {
      primary: "text-white",
      glass: "text-slate-900 dark:text-white",
      ghost: "text-ocean-600 dark:text-cyan-300",
    },
    size: {
      sm: "text-sm",
      md: "text-base",
      lg: "text-lg",
    },
  },
  defaultVariants: { variant: "primary", size: "md" },
});

type Variant = NonNullable<VariantProps<typeof buttonVariants>["variant"]>;

const SPINNER_COLOR: Record<Variant, string> = {
  primary: "#FFFFFF",
  glass: palette.mint["300"],
  ghost: palette.ocean["400"],
};

export interface ButtonProps
  extends Omit<PressableProps, "children" | "style">,
    VariantProps<typeof buttonVariants> {
  children: ReactNode;
  isLoading?: boolean;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
  fullWidth?: boolean;
  className?: string;
  textClassName?: string;
}

export function Button({
  variant,
  size,
  children,
  isLoading = false,
  disabled,
  leftIcon,
  rightIcon,
  fullWidth = false,
  className,
  textClassName,
  onPressIn,
  onPressOut,
  onHoverIn,
  onHoverOut,
  ...pressableProps
}: ButtonProps) {
  const resolved: Variant = variant ?? "primary";
  const isDisabled = Boolean(disabled) || isLoading;
  const press = usePressAnimation({ disabled: isDisabled });
  const containerClassName = cn(buttonVariants({ variant: resolved, size }), className);

  const content = (
    <>
      {isLoading ? <ActivityIndicator size="small" color={SPINNER_COLOR[resolved]} /> : leftIcon}
      {typeof children === "string" ? (
        <Text className={cn(buttonTextVariants({ variant: resolved, size }), textClassName)}>
          {children}
        </Text>
      ) : (
        children
      )}
      {rightIcon}
    </>
  );

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ disabled: isDisabled, busy: isLoading }}
      disabled={isDisabled}
      className={cn(fullWidth ? "w-full" : "self-start", isDisabled && "opacity-50")}
      {...pressableProps}
      onPressIn={(event) => {
        press.onPressIn();
        onPressIn?.(event);
      }}
      onPressOut={(event) => {
        press.onPressOut();
        onPressOut?.(event);
      }}
      onHoverIn={(event) => {
        press.onHoverIn();
        onHoverIn?.(event);
      }}
      onHoverOut={(event) => {
        press.onHoverOut();
        onHoverOut?.(event);
      }}
    >
      <Animated.View style={press.animatedStyle}>
        {resolved === "glass" ? (
          <GlassSurface intensity={30} className={containerClassName}>
            {content}
          </GlassSurface>
        ) : resolved === "primary" ? (
          <View className={cn(containerClassName, "web:shadow-lg web:shadow-cyan-500/40")}>
            <LinearGradient
              colors={gradients.brand}
              start={{ x: 0, y: 0 }}
              end={{ x: 1, y: 1 }}
              style={StyleSheet.absoluteFill}
            />
            {content}
          </View>
        ) : (
          <View className={containerClassName}>{content}</View>
        )}
      </Animated.View>
    </Pressable>
  );
}
