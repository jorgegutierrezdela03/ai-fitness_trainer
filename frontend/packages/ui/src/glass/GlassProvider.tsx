import { BlurTargetView } from "expo-blur";
import { type ComponentRef, createContext, type ReactNode, type RefObject, useContext, useRef } from "react";
import { StyleSheet, View } from "react-native";

import { cn } from "../lib/cn";

type BlurTargetRef = RefObject<ComponentRef<typeof View> | null>;

const GlassTargetContext = createContext<BlurTargetRef | null>(null);

/**
 * Shares the blur target between the backdrop and every glass surface.
 * Android only blurs what is inside `GlassBackdrop`; iOS and Web ignore the target.
 */
export function GlassProvider({ children }: { children: ReactNode }) {
  const targetRef = useRef<ComponentRef<typeof View>>(null);
  return <GlassTargetContext.Provider value={targetRef}>{children}</GlassTargetContext.Provider>;
}

export function useGlassBlurTarget(): BlurTargetRef | null {
  return useContext(GlassTargetContext);
}

export interface GlassBackdropProps {
  className?: string;
  children?: ReactNode;
}

/**
 * Content that glass surfaces blur. It must be a sibling of the glass surfaces, never their
 * ancestor: a surface inside its own blur target would blur itself.
 */
export function GlassBackdrop({ className, children }: GlassBackdropProps) {
  const targetRef = useGlassBlurTarget();
  return (
    <View className={cn("absolute inset-0", className)}>
      <BlurTargetView ref={targetRef ?? undefined} style={StyleSheet.absoluteFill}>
        {children}
      </BlurTargetView>
    </View>
  );
}
