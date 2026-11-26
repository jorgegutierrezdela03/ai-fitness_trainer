import { useEffect, useState } from "react";
import { ScrollView, Text, View } from "react-native";

import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { GlassCard } from "../components/GlassCard";
import { Input } from "../components/Input";
import { GlassBackdrop, GlassProvider } from "../glass/GlassProvider";
import { GradientBackground } from "./GradientBackground";

function SearchGlyph() {
  return (
    <View className="h-4 w-4">
      <View className="h-3 w-3 rounded-full border-2 border-cyan-300" />
      <View className="absolute bottom-0 right-0 h-1.5 w-0.5 -rotate-45 rounded-full bg-cyan-300" />
    </View>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View className="flex-1 items-center gap-0.5">
      <Text className="text-lg font-bold text-slate-900 dark:text-white">{value}</Text>
      <Text className="text-xs text-slate-600 dark:text-slate-300">{label}</Text>
    </View>
  );
}

const INTENSITIES = ["subtle", "medium", "heavy"] as const;

export function DemoScreen() {
  const [request, setRequest] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);

  useEffect(() => {
    if (!isGenerating) return;
    const timer = setTimeout(() => setIsGenerating(false), 1600);
    return () => clearTimeout(timer);
  }, [isGenerating]);

  const trimmed = request.trim();
  const error =
    request.length > 0 && trimmed.length < 3 ? "Describe la sesión con al menos 3 caracteres." : undefined;

  return (
    <GlassProvider>
      <View className="flex-1 bg-abyss-950 web:min-h-screen">
        {/* The backdrop is a sibling of the glass, never its parent. */}
        <GlassBackdrop>
          <GradientBackground />
        </GlassBackdrop>

        <ScrollView className="flex-1" contentContainerClassName="mx-auto w-full max-w-xl gap-6 px-5 pb-16 pt-20">
          <View className="gap-3">
            <Badge variant="glow">Entrenador IA · En vivo</Badge>
            <Text className="text-4xl font-bold tracking-tight text-slate-900 dark:text-white">
              Tu sesión de hoy
            </Text>
            <Text className="text-base text-slate-600 dark:text-slate-300">
              Cristal translúcido sobre un fondo vivo en azul y verde.
            </Text>
          </View>

          <GlassCard intensity="heavy" glow>
            <View className="gap-4">
              <View className="flex-row flex-wrap gap-2">
                <Badge variant="info">Hipertrofia</Badge>
                <Badge variant="success">Plan validado</Badge>
              </View>
              <Text className="text-2xl font-semibold text-slate-900 dark:text-white">
                Empuje · Pecho y tríceps
              </Text>
              <View className="flex-row rounded-2xl bg-white/5 py-3">
                <Stat value="45 min" label="Duración" />
                <Stat value="5" label="Ejercicios" />
                <Stat value="RPE 7–8" label="Intensidad" />
              </View>
              <Button size="lg" fullWidth>
                Empezar entrenamiento
              </Button>
            </View>
          </GlassCard>

          <GlassCard>
            <View className="gap-4">
              <Input
                label="¿Qué quieres entrenar hoy?"
                placeholder="Ej. espalda y bíceps, 40 minutos"
                value={request}
                onChangeText={setRequest}
                leftIcon={<SearchGlyph />}
                error={error}
                hint="Incluye grupo muscular, tiempo o restricciones."
                returnKeyType="send"
              />
              <View className="flex-row flex-wrap gap-3">
                <Button
                  isLoading={isGenerating}
                  disabled={trimmed.length < 3}
                  onPress={() => setIsGenerating(true)}
                >
                  Generar sesión
                </Button>
                <Button variant="glass">Historial</Button>
                <Button variant="ghost" onPress={() => setRequest("")}>
                  Limpiar
                </Button>
              </View>
            </View>
          </GlassCard>

          <View className="flex-row gap-3">
            {INTENSITIES.map((intensity) => (
              <GlassCard key={intensity} intensity={intensity} className="flex-1 items-center p-4" onPress={() => {}}>
                <Text className="text-sm font-semibold text-slate-900 dark:text-white">{intensity}</Text>
              </GlassCard>
            ))}
          </View>
        </ScrollView>
      </View>
    </GlassProvider>
  );
}
