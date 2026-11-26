import "./globals.css";

import type { Metadata } from "next";
import type { ReactNode } from "react";

export const metadata: Metadata = {
  title: "FitEvidence UI",
  description: "Glass component library demo",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    // The `dark` class enables the dark theme, which is the primary one.
    <html lang="es" className="dark">
      <body>{children}</body>
    </html>
  );
}
