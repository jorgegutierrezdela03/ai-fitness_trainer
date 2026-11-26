import type { NextConfig } from "next";

// `.web.*` first, so platform files such as GlassSurface.web.tsx win on the web.
const WEB_EXTENSIONS = [".web.tsx", ".web.ts", ".web.jsx", ".web.js"];

const API_URL = process.env.API_URL ?? "http://127.0.0.1:8000";

const nextConfig: NextConfig = {
  // The browser calls /api on the same origin and Next.js forwards it to FastAPI (no CORS).
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/api/:path*` }];
  },
  experimental: {
    // The local model can take more than the default 30 s proxy timeout.
    proxyTimeout: 300_000,
  },
  transpilePackages: [
    "@fitevidence/ui",
    "nativewind",
    "react-native-css-interop",
    "react-native-web",
    "react-native-reanimated",
    "react-native-worklets",
    "react-native-safe-area-context",
    "expo-blur",
    "expo-linear-gradient",
    "expo-modules-core",
  ],
  // Turbopack (the default) does not apply `.web.*` extensions inside node_modules for these
  // packages, so dev and build run with webpack, as Expo's own Next.js adapter does.
  webpack: (config, { dev, isServer, webpack }) => {
    config.resolve ??= {};
    config.resolve.alias = { ...config.resolve.alias, "react-native$": "react-native-web" };
    config.resolve.extensions = [...WEB_EXTENSIONS, ...(config.resolve.extensions ?? [])];
    config.plugins.push(
      new webpack.DefinePlugin({
        // React Native libraries read these globals, which Metro defines and webpack does not.
        __DEV__: JSON.stringify(dev),
        // Node's `global` does not exist in browsers; Reanimated reads it at import time.
        ...(isServer ? {} : { global: "globalThis" }),
      }),
    );
    return config;
  },
};

export default nextConfig;
