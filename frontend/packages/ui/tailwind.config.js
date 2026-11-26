/**
 * Shared design tokens. Apps use this file as a preset and add their own `content` paths,
 * which must include `packages/ui/src` so the library classes are generated.
 *
 * @type {import('tailwindcss').Config}
 */
const palette = require("./src/theme/palette.json");

module.exports = {
  content: ["./src/**/*.{ts,tsx}"],
  presets: [require("nativewind/preset")],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        ocean: palette.ocean,
        mint: palette.mint,
        abyss: palette.abyss,
        glass: palette.glass,
      },
      borderRadius: {
        "4xl": "2rem",
      },
      backdropBlur: {
        "4xl": "72px",
      },
    },
  },
  plugins: [],
};
