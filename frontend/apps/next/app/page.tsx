"use client";

import dynamic from "next/dynamic";

// Reanimated needs browser APIs such as requestAnimationFrame, so animated
// screens render on the client only.
const TrainerScreen = dynamic(
  () => import("@fitevidence/ui").then((module) => module.TrainerScreen),
  { ssr: false },
);

export default function Page() {
  // Empty base URL: requests go to /api on this origin and Next.js proxies them.
  return <TrainerScreen apiBaseUrl="" />;
}
