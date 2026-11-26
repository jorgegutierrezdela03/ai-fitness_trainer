import { LinearGradient } from "expo-linear-gradient";
import { StyleSheet } from "react-native";

import { gradients } from "../theme/tokens";

/** Thin light lines on the top and left edges that imitate light catching on glass. */
export function GlassHighlight() {
  return (
    <>
      <LinearGradient
        colors={gradients.highlightHorizontal}
        start={{ x: 0, y: 0.5 }}
        end={{ x: 1, y: 0.5 }}
        style={styles.top}
      />
      <LinearGradient
        colors={gradients.highlightVertical}
        start={{ x: 0.5, y: 0 }}
        end={{ x: 0.5, y: 1 }}
        style={styles.left}
      />
    </>
  );
}

const styles = StyleSheet.create({
  top: {
    position: "absolute",
    top: 0,
    left: 12,
    right: 12,
    height: 1,
    pointerEvents: "none",
  },
  left: {
    position: "absolute",
    top: 10,
    bottom: "45%",
    left: 0,
    width: 1,
    pointerEvents: "none",
  },
});
