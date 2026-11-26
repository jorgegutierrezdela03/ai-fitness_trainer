import { type ReactNode, useEffect, useState } from "react";
import { ScrollView, Text, View } from "react-native";

import { Badge } from "../components/Badge";
import { Button } from "../components/Button";
import { Chip } from "../components/Chip";
import { GlassCard } from "../components/GlassCard";
import { Input } from "../components/Input";
import { GradientBackground } from "../demo/GradientBackground";
import { GlassBackdrop, GlassProvider } from "../glass/GlassProvider";
import {
  type ExperienceLevel,
  type FormOptions,
  fetchHealth,
  fetchOptions,
  generateSession,
  type HealthStatus,
  type SessionGenerationInput,
  type SessionResult,
  type UserProfile,
} from "./api";
import { label } from "./labels";
import { ResultView } from "./ResultView";

const DAYS = [1, 2, 3, 4, 5, 6, 7] as const;
const DURATIONS = [30, 45, 60, 75, 90, 120] as const;
const MAX_GOALS = 2;

function messageOf(error: unknown): string {
  return error instanceof Error ? error.message : "Error inesperado.";
}

function toggle(values: string[], value: string, max = Number.POSITIVE_INFINITY): string[] {
  if (values.includes(value)) return values.filter((item) => item !== value);
  return values.length < max ? [...values, value] : values;
}

/** Parses an optional number within a range. Returns null when empty, undefined when invalid. */
function parseNumber(text: string, min: number, max: number): number | null | undefined {
  if (text.trim() === "") return null;
  const value = Number(text.replace(",", "."));
  return Number.isFinite(value) && value >= min && value <= max ? value : undefined;
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <GlassCard>
      <View className="gap-4">
        <Text className="text-lg font-semibold text-slate-900 dark:text-white">{title}</Text>
        {children}
      </View>
    </GlassCard>
  );
}

function Field({ title, error, children }: { title: string; error?: string; children: ReactNode }) {
  return (
    <View className="gap-2">
      <Text className="ml-1 text-sm font-medium text-slate-700 dark:text-slate-200">{title}</Text>
      <View className="flex-row flex-wrap gap-2">{children}</View>
      {error ? <Text className="ml-1 text-xs text-rose-600 dark:text-rose-400">{error}</Text> : null}
    </View>
  );
}

export interface TrainerScreenProps {
  /** API origin, e.g. "http://localhost:8000". Empty string uses the same origin (Next.js proxy). */
  apiBaseUrl: string;
}

export function TrainerScreen({ apiBaseUrl }: TrainerScreenProps) {
  const [options, setOptions] = useState<FormOptions | null>(null);
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [reloadKey, setReloadKey] = useState(0);

  // Required profile fields.
  const [age, setAge] = useState("");
  const [experience, setExperience] = useState<ExperienceLevel>("Intermediate");
  const [goals, setGoals] = useState<string[]>(["Hypertrophy"]);
  const [days, setDays] = useState(3);
  const [duration, setDuration] = useState(60);
  const [hasLimitations, setHasLimitations] = useState(false);
  const [areas, setAreas] = useState<string[]>([]);
  const [limitationText, setLimitationText] = useState("");

  // Optional profile fields.
  const [showOptional, setShowOptional] = useState(false);
  const [sex, setSex] = useState<string | null>(null);
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [avoid, setAvoid] = useState("");
  const [noEquipment, setNoEquipment] = useState<string[]>([]);
  const [style, setStyle] = useState<string | null>(null);

  const [request, setRequest] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [result, setResult] = useState<SessionResult | null>(null);

  useEffect(() => {
    let active = true;
    setLoadError(null);
    fetchOptions(apiBaseUrl)
      .then((loaded) => {
        if (active) setOptions(loaded);
      })
      .catch((error: unknown) => {
        if (active) setLoadError(messageOf(error));
      });
    fetchHealth(apiBaseUrl)
      .then((status) => {
        if (active) setHealth(status);
      })
      .catch(() => {
        if (active) setHealth(null);
      });
    return () => {
      active = false;
    };
  }, [apiBaseUrl, reloadKey]);

  const ageValue = parseNumber(age, 18, 100);
  const heightValue = parseNumber(height, 100, 250);
  const weightValue = parseNumber(weight, 30, 300);
  const trimmedRequest = request.trim();

  const errors = {
    age: ageValue == null ? "Indica una edad entre 18 y 100 años." : undefined,
    goals: goals.length === 0 ? "Elige al menos un objetivo." : undefined,
    areas: hasLimitations && areas.length === 0 ? "Elige al menos una zona." : undefined,
    height: heightValue === undefined ? "Entre 100 y 250 cm." : undefined,
    weight: weightValue === undefined ? "Entre 30 y 300 kg." : undefined,
    request: trimmedRequest.length < 3 ? "Describe la sesión con al menos 3 caracteres." : undefined,
  };
  const isValid = Object.values(errors).every((error) => error === undefined);
  const visible = (error: string | undefined) => (submitted ? error : undefined);

  function buildInput(): SessionGenerationInput {
    const profile: UserProfile = {
      age: ageValue ?? 0,
      experience_level: experience,
      primary_goals: goals,
      available_days_per_week: days,
      session_duration_minutes: duration,
      physical_limitations: hasLimitations
        ? {
            has_limitations: true,
            affected_areas: areas,
            ...(limitationText.trim() ? { description: limitationText.trim() } : {}),
          }
        : { has_limitations: false },
    };
    if (sex) profile.sex = sex;
    if (heightValue != null) profile.height_cm = heightValue;
    if (weightValue != null) profile.weight_kg = weightValue;
    const avoidList = avoid.split(",").map((item) => item.trim()).filter(Boolean);
    if (avoidList.length > 0) profile.exercises_to_avoid = avoidList;
    if (noEquipment.length > 0) profile.equipment_limitations = noEquipment;
    if (style) profile.preferred_training_style = style;
    return { user_profile: profile, session_request: trimmedRequest };
  }

  async function submit() {
    setSubmitted(true);
    if (!isValid) return;
    setIsGenerating(true);
    setSubmitError(null);
    setResult(null);
    try {
      setResult(await generateSession(apiBaseUrl, buildInput()));
    } catch (error) {
      setSubmitError(messageOf(error));
    } finally {
      setIsGenerating(false);
    }
  }

  const modelProblem =
    health === null
      ? null
      : health.ollama !== "ok"
        ? "Ollama no responde. Arráncalo con `ollama serve` o la app de Ollama."
        : !health.model_available
          ? `El modelo ${health.model} no está descargado. Ejecuta \`ollama pull ${health.model}\`.`
          : null;

  return (
    <GlassProvider>
      <View className="flex-1 bg-abyss-950 web:min-h-screen">
        <GlassBackdrop>
          <GradientBackground animated={false} />
        </GlassBackdrop>

        <ScrollView
          className="flex-1"
          keyboardShouldPersistTaps="handled"
          contentContainerClassName="mx-auto w-full max-w-2xl gap-5 px-5 pb-20 pt-16"
        >
          <View className="gap-2">
            <Badge variant="glow">{health ? `Modelo: ${health.model}` : "Entrenador IA"}</Badge>
            <Text className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Genera tu sesión
            </Text>
            <Text className="text-base text-slate-600 dark:text-slate-300">
              Completa tu perfil y describe qué quieres entrenar hoy.
            </Text>
          </View>

          {loadError ? (
            <GlassCard>
              <View className="gap-3">
                <Text className="text-sm text-rose-600 dark:text-rose-300">{loadError}</Text>
                <Button variant="glass" size="sm" onPress={() => setReloadKey((key) => key + 1)}>
                  Reintentar
                </Button>
              </View>
            </GlassCard>
          ) : null}

          {modelProblem ? (
            <GlassCard intensity="subtle">
              <Text className="text-sm text-amber-700 dark:text-amber-300">{modelProblem}</Text>
            </GlassCard>
          ) : null}

          {options ? (
            <>
              <Section title="Tu perfil">
                <Input
                  label="Edad"
                  placeholder="Ej. 28"
                  keyboardType="number-pad"
                  maxLength={3}
                  value={age}
                  onChangeText={setAge}
                  error={visible(errors.age)}
                />
                <Field title="Nivel de experiencia">
                  {options.experience_levels.map((level) => (
                    <Chip
                      key={level}
                      label={label(level)}
                      selected={experience === level}
                      onPress={() => setExperience(level)}
                    />
                  ))}
                </Field>
                <Field title={`Objetivos (máximo ${MAX_GOALS})`} error={visible(errors.goals)}>
                  {options.goals.map((goal) => (
                    <Chip
                      key={goal}
                      label={label(goal)}
                      selected={goals.includes(goal)}
                      onPress={() => setGoals((current) => toggle(current, goal, MAX_GOALS))}
                    />
                  ))}
                </Field>
                <Field title="Días disponibles por semana">
                  {DAYS.map((value) => (
                    <Chip key={value} label={String(value)} selected={days === value} onPress={() => setDays(value)} />
                  ))}
                </Field>
                <Field title="Duración de la sesión">
                  {DURATIONS.map((value) => (
                    <Chip
                      key={value}
                      label={`${value} min`}
                      selected={duration === value}
                      onPress={() => setDuration(value)}
                    />
                  ))}
                </Field>
              </Section>

              <Section title="Limitaciones físicas">
                <Field title="¿Tienes alguna limitación física que pueda afectar a tu entrenamiento?">
                  <Chip label="No" selected={!hasLimitations} onPress={() => setHasLimitations(false)} />
                  <Chip label="Sí" selected={hasLimitations} onPress={() => setHasLimitations(true)} />
                </Field>
                {hasLimitations ? (
                  <>
                    <Field title="Zonas afectadas" error={visible(errors.areas)}>
                      {options.body_areas.map((area) => (
                        <Chip
                          key={area}
                          label={label(area)}
                          selected={areas.includes(area)}
                          onPress={() => setAreas((current) => toggle(current, area))}
                        />
                      ))}
                    </Field>
                    <Input
                      label="Descripción (opcional)"
                      placeholder="Ej. molestia al presionar por encima de la cabeza"
                      maxLength={300}
                      value={limitationText}
                      onChangeText={setLimitationText}
                    />
                  </>
                ) : null}
              </Section>

              <Section title="Más detalles (opcional)">
                <Button variant="ghost" size="sm" onPress={() => setShowOptional((value) => !value)}>
                  {showOptional ? "Ocultar" : "Añadir preferencias, equipo y datos corporales"}
                </Button>
                {showOptional ? (
                  <>
                    <Field title="Sexo">
                      {options.sexes.map((value) => (
                        <Chip
                          key={value}
                          label={label(value)}
                          selected={sex === value}
                          onPress={() => setSex((current) => (current === value ? null : value))}
                        />
                      ))}
                    </Field>
                    <View className="flex-row gap-3">
                      <View className="flex-1">
                        <Input
                          label="Altura (cm)"
                          keyboardType="decimal-pad"
                          value={height}
                          onChangeText={setHeight}
                          error={errors.height}
                        />
                      </View>
                      <View className="flex-1">
                        <Input
                          label="Peso (kg)"
                          keyboardType="decimal-pad"
                          value={weight}
                          onChangeText={setWeight}
                          error={errors.weight}
                        />
                      </View>
                    </View>
                    <Input
                      label="Ejercicios que prefieres evitar"
                      placeholder="Separados por comas"
                      value={avoid}
                      onChangeText={setAvoid}
                    />
                    <Field title="Equipo no disponible">
                      {options.equipment.map((item) => (
                        <Chip
                          key={item}
                          label={label(item)}
                          selected={noEquipment.includes(item)}
                          onPress={() => setNoEquipment((current) => toggle(current, item))}
                        />
                      ))}
                    </Field>
                    <Field title="Estilo preferido">
                      {options.training_styles.map((value) => (
                        <Chip
                          key={value}
                          label={label(value)}
                          selected={style === value}
                          onPress={() => setStyle((current) => (current === value ? null : value))}
                        />
                      ))}
                    </Field>
                  </>
                ) : null}
              </Section>

              <Section title="¿Qué quieres entrenar hoy?">
                <Input
                  placeholder="Ej. empuje de tren superior, centrado en pecho y tríceps"
                  multiline
                  maxLength={500}
                  value={request}
                  onChangeText={setRequest}
                  error={visible(errors.request)}
                  hint="Puedes indicar grupo muscular, tiempo, energía o movimientos a evitar."
                  className="min-h-20"
                />
                <Button size="lg" fullWidth isLoading={isGenerating} onPress={() => void submit()}>
                  {isGenerating ? "Generando…" : "Generar sesión"}
                </Button>
                {isGenerating ? (
                  <Text className="text-center text-xs text-slate-500 dark:text-slate-400">
                    El modelo local puede tardar hasta un minuto.
                  </Text>
                ) : null}
                {submitted && !isValid ? (
                  <Text className="text-center text-xs text-rose-600 dark:text-rose-400">
                    Revisa los campos marcados.
                  </Text>
                ) : null}
                {submitError ? (
                  <Text className="text-sm text-rose-600 dark:text-rose-300">{submitError}</Text>
                ) : null}
              </Section>

              {result ? <ResultView result={result} /> : null}
            </>
          ) : null}
        </ScrollView>
      </View>
    </GlassProvider>
  );
}
