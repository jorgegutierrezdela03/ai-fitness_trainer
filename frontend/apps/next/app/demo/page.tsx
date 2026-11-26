"use client";

import dynamic from "next/dynamic";

const DemoScreen = dynamic(() => import("@fitevidence/ui").then((module) => module.DemoScreen), {
  ssr: false,
});

export default function DemoPage() {
  return <DemoScreen />;
}
