import { useState } from "react";
import { Platform, Text, View } from "react-native";

import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { GlassCard } from "../components/GlassCard";
import { cn } from "../lib/cn";
import type { Exercise, SessionResult, TrainingPlan } from "./api";
import { label } from "./labels";

const MONO = Platform.select({ web: "ui-monospace, Menlo, monospace", ios: "Menlo", default: "monospace" });

function Heading({ children }: { children: string }) {
  return <Text className="text-xs font-semibold uppercase tracking-widest text-cyan-700 dark:text-cyan-300">{children}</Text>;
}

function Body({ children, className }: { children: string; className?: string }) {
  return <Text className={cn("text-sm leading-5 text-slate-700 dark:text-slate-200", className)}>{children}</Text>;
}

function BulletList({ items }: { items: string[] }) {
  return (
    <View className="gap-1">
      {items.map((item, index) => (
        <Body key={`${index}-${item}`}>{`•  ${item}`}</Body>
      ))}
    </View>
  );
}

function prescription(exercise: Exercise): string {
  const parts: string[] = [];
  if (exercise.sets != null && exercise.reps != null) parts.push(`${exercise.sets} × ${exercise.reps}`);
  else if (exercise.reps != null) parts.push(`${exercise.reps} reps`);
  if (exercise.duration_minutes != null) parts.push(`${exercise.duration_minutes} min`);
  if (exercise.rest_seconds != null) parts.push(`descanso ${exercise.rest_seconds} s`);
  if (exercise.rpe != null) parts.push(`RPE ${exercise.rpe}`);
  return parts.join(" · ");
}

function ExerciseRow({ exercise, index }: { exercise: Exercise; index: number }) {
  return (
    <View className="gap-1.5 rounded-2xl border border-white/10 bg-white/40 p-3 dark:bg-white/5">
      <View className="flex-row items-center justify-between gap-2">
        <Text className="flex-1 text-base font-semibold text-slate-900 dark:text-white">
          {`${index + 1}. ${exercise.name}`}
        </Text>
        <Text className="text-xs text-slate-500 dark:text-slate-400">{label(exercise.priority)}</Text>
      </View>
      <Text className="text-sm font-medium text-mint-700 dark:text-mint-300">{prescription(exercise)}</Text>
      <BulletList items={exercise.instructions} />
    </View>
  );
}

function PlanView({ plan }: { plan: TrainingPlan }) {
  const warmUp = [
    ...(plan.warm_up?.general_activation ?? []),
    ...(plan.warm_up?.specific_warmup ?? []),
    ...(plan.warm_up?.warmup_sets ?? []),
  ];
  return (
    <View className="gap-4">
      <View className="gap-2">
        <Text className="text-2xl font-semibold text-slate-900 dark:text-white">{plan.title}</Text>
        <View className="flex-row flex-wrap gap-2">
          <Badge variant="info">{label(plan.main_focus)}</Badge>
          <Badge variant="success">{`${plan.estimated_duration_minutes} min`}</Badge>
        </View>
      </View>

      {warmUp.length > 0 ? (
        <View className="gap-2">
          <Heading>Calentamiento</Heading>
          <BulletList items={warmUp} />
        </View>
      ) : null}

      <View className="gap-2">
        <Heading>Bloque principal</Heading>
        {plan.main_block.map((exercise, index) => (
          <ExerciseRow key={`${index}-${exercise.name}`} exercise={exercise} index={index} />
        ))}
      </View>

      {plan.cool_down ? (
        <View className="gap-2">
          <Heading>Vuelta a la calma</Heading>
          <BulletList items={plan.cool_down.exercises} />
          {plan.cool_down.instructions ? <Body>{plan.cool_down.instructions}</Body> : null}
        </View>
      ) : null}

      {plan.general_notes ? (
        <View className="gap-2">
          <Heading>Notas</Heading>
          <Body>{plan.general_notes}</Body>
        </View>
      ) : null}
    </View>
  );
}

function Notice({ tone, title, children }: { tone: "warning" | "info"; title: string; children: string }) {
  return (
    <View
      className={cn(
        "gap-1 rounded-2xl border p-3",
        tone === "warning" ? "border-amber-400/50 bg-amber-400/10" : "border-cyan-300/40 bg-cyan-400/10",
      )}
    >
      <Text className="text-sm font-semibold text-slate-900 dark:text-white">{title}</Text>
      <Body>{children}</Body>
    </View>
  );
}

export function ResultView({ result }: { result: SessionResult }) {
  const [showRaw, setShowRaw] = useState(!result.is_valid);
  const { response, time_coherence: coherence } = result;

  return (
    <GlassCard intensity="heavy" glow={result.is_valid}>
      <View className="gap-4">
        {response?.response_type === "plan" ? <PlanView plan={response.plan} /> : null}

        {response?.response_type === "clarification" ? (
          <View className="gap-2">
            <Heading>Necesito un poco más de información</Heading>
            <BulletList items={response.questions} />
          </View>
        ) : null}

        {response?.response_type === "safety_referral" ? (
          <Notice tone="warning" title="No es seguro generar esta sesión">
            {response.message}
          </Notice>
        ) : null}

        {response?.response_type === "out_of_scope" ? (
          <Notice tone="info" title="Fuera del alcance actual">
            {response.message}
          </Notice>
        ) : null}

        {!result.is_valid ? (
          <Notice tone="warning" title="La respuesta del modelo no cumple el esquema">
            {result.validation_errors.map((error) => `${error.location}: ${error.message}`).join("\n")}
          </Notice>
        ) : null}

        {result.scope_violations.length > 0 ? (
          <Notice tone="warning" title="Fuera del alcance activo">
            {result.scope_violations.join("\n")}
          </Notice>
        ) : null}

        {coherence && !coherence.within_tolerance ? (
          <Notice tone="info" title="La duración declarada no cuadra">
            {`El plan declara ${coherence.declared_minutes} min, pero la estimación da ${Math.round(coherence.calculated_minutes)} min.`}
          </Notice>
        ) : null}

        <View className="flex-row flex-wrap items-center justify-between gap-2">
          <Text className="text-xs text-slate-500 dark:text-slate-400">
            {`${result.metadata.model} · ${result.metadata.latency_seconds.toFixed(1)} s`}
          </Text>
          <Button variant="ghost" size="sm" onPress={() => setShowRaw((value) => !value)}>
            {showRaw ? "Ocultar JSON" : "Ver JSON del modelo"}
          </Button>
        </View>

        {showRaw ? (
          <View className="rounded-2xl bg-abyss-950/70 p-3">
            <Text selectable style={{ fontFamily: MONO }} className="text-xs leading-4 text-slate-200">
              {result.raw_output || "(respuesta vacía)"}
            </Text>
          </View>
        ) : null}
      </View>
    </GlassCard>
  );
}
