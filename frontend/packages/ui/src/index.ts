export { cn } from "./lib/cn";
export { type GradientColors, gradients, palette } from "./theme/tokens";

export {
  GlassBackdrop,
  type GlassBackdropProps,
  GlassProvider,
  useGlassBlurTarget,
} from "./glass/GlassProvider";
export { GlassSurface } from "./glass/GlassSurface";
export type { GlassSurfaceProps, GlassTint } from "./glass/types";

export { type PressAnimationOptions, usePressAnimation } from "./hooks/usePressAnimation";

export { Badge, type BadgeProps, badgeTextVariants, badgeVariants } from "./components/Badge";
export { Button, type ButtonProps, buttonTextVariants, buttonVariants } from "./components/Button";
export { Chip, type ChipProps } from "./components/Chip";
export { GlassCard, type GlassCardProps, glassCardVariants } from "./components/GlassCard";
export { Input, inputFieldVariants, type InputProps } from "./components/Input";

export { DemoScreen } from "./demo/DemoScreen";
export { GradientBackground, type GradientBackgroundProps } from "./demo/GradientBackground";

export * from "./trainer/api";
export { ResultView } from "./trainer/ResultView";
export { TrainerScreen, type TrainerScreenProps } from "./trainer/TrainerScreen";
