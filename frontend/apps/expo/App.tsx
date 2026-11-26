import "./global.css";

import { TrainerScreen } from "@fitevidence/ui";
import { StatusBar } from "expo-status-bar";
import { colorScheme } from "nativewind";

// Dark is the primary theme. Remove this line to follow the system setting.
colorScheme.set("dark");

// iOS simulator and web: localhost. Android emulator: http://10.0.2.2:8000.
// Physical device: your computer's LAN address, e.g. http://192.168.1.20:8000.
const API_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

export default function App() {
  return (
    <>
      <TrainerScreen apiBaseUrl={API_URL} />
      <StatusBar style="light" />
    </>
  );
}
