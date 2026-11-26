/**
 * Client for the FitEvidence API. Types mirror the Pydantic schemas in src/schemas.
 * They are written by hand for now; generating them from the JSON schema would keep them in sync.
 */

export type ExperienceLevel = "Beginner" | "Intermediate" | "Advanced";

export interface PhysicalLimitations {
  has_limitations: boolean;
  affected_areas?: string[];
  description?: string;
}

export interface UserProfile {
  age: number;
  sex?: string;
  height_cm?: number;
  weight_kg?: number;
  experience_level: ExperienceLevel;
  primary_goals: string[];
  available_days_per_week: number;
  session_duration_minutes: number;
  exercises_to_avoid?: string[];
  equipment_limitations?: string[];
  preferred_training_style?: string;
  physical_limitations: PhysicalLimitations;
}

export interface SessionGenerationInput {
  user_profile: UserProfile;
  session_request: string;
}

export interface Exercise {
  name: string;
  modality: "Strength" | "Cardio" | "Mobility";
  priority: "Primary" | "Secondary" | "Accessory";
  primary_muscle_group?: string | null;
  secondary_muscle_groups?: string[] | null;
  sets?: number | null;
  reps?: string | null;
  rest_seconds?: number | null;
  rpe?: number | null;
  duration_minutes?: number | null;
  cardio_intensity?: string | null;
  instructions: string[];
}

export interface TrainingPlan {
  title: string;
  main_focus: string;
  estimated_duration_minutes: number;
  warm_up?: {
    general_activation?: string[] | null;
    specific_warmup?: string[] | null;
    warmup_sets?: string[] | null;
  } | null;
  main_block: Exercise[];
  additional_cardio?: {
    activity_type: string;
    duration_minutes: number;
    intensity: string;
    instructions?: string | null;
  } | null;
  cool_down?: {
    exercises: string[];
    estimated_duration_minutes?: number | null;
    instructions?: string | null;
  } | null;
  general_notes?: string | null;
}

export type LLMResponse =
  | { response_type: "plan"; plan: TrainingPlan }
  | { response_type: "clarification"; questions: string[] }
  | { response_type: "safety_referral"; reason: string; message: string }
  | { response_type: "out_of_scope"; message: string };

export interface SessionResult {
  is_valid: boolean;
  response: LLMResponse | null;
  validation_errors: { location: string; message: string }[];
  raw_output: string;
  metadata: { model: string; latency_seconds: number };
  scope_violations: string[];
  time_coherence: {
    declared_minutes: number;
    calculated_minutes: number;
    relative_error: number;
    within_tolerance: boolean;
  } | null;
}

export interface FormOptions {
  scope_version: string;
  goals: string[];
  training_styles: string[];
  experience_levels: ExperienceLevel[];
  sexes: string[];
  equipment: string[];
  body_areas: string[];
}

export interface HealthStatus {
  api: string;
  ollama: "ok" | "unreachable";
  model: string;
  model_available: boolean;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

interface FastApiValidationItem {
  loc?: (string | number)[];
  msg?: string;
}

function describeError(status: number, body: unknown): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const { detail } = body as { detail: unknown };
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) {
      return (detail as FastApiValidationItem[])
        .map((item) => `${(item.loc ?? []).slice(1).join(".")}: ${item.msg ?? ""}`)
        .join("\n");
    }
  }
  return `Error ${status} de la API.`;
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(url, init);
  } catch {
    throw new ApiError("No se puede conectar con la API. ¿Está arrancada en el puerto 8000?", 0);
  }
  const body: unknown = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(describeError(response.status, body), response.status);
  return body as T;
}

export function fetchOptions(baseUrl: string): Promise<FormOptions> {
  return request<FormOptions>(`${baseUrl}/api/options`);
}

export function fetchHealth(baseUrl: string): Promise<HealthStatus> {
  return request<HealthStatus>(`${baseUrl}/api/health`);
}

export function generateSession(baseUrl: string, input: SessionGenerationInput): Promise<SessionResult> {
  return request<SessionResult>(`${baseUrl}/api/sessions`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
  });
}
