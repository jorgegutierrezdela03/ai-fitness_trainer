import palette from "./palette.json";

export { palette };

/** expo-linear-gradient needs at least two colours. */
export type GradientColors = readonly [string, string, ...string[]];

export const gradients = {
  brand: [palette.ocean["600"], palette.ocean["500"], palette.mint["400"]],
  brandBorder: [palette.cyan["300"], palette.ocean["500"], palette.mint["400"]],
  backdropDark: [palette.abyss["950"], palette.ocean["950"], palette.mint["950"]],
  backdropLight: ["#E0F2FE", "#ECFEFF", "#D1FAE5"],
  highlightHorizontal: ["rgba(255,255,255,0)", palette.glass.highlight, "rgba(255,255,255,0)"],
  highlightVertical: ["rgba(255,255,255,0.55)", "rgba(255,255,255,0)"],
} as const satisfies Record<string, GradientColors>;
