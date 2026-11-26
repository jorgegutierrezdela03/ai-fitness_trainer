const LABELS: Record<string, string> = {
  Beginner: "Principiante",
  Intermediate: "Intermedio",
  Advanced: "Avanzado",
  Strength: "Fuerza",
  Hypertrophy: "Hipertrofia",
  "Fat loss": "Pérdida de grasa",
  "Cardiovascular fitness": "Cardiovascular",
  "Muscular endurance": "Resistencia muscular",
  "General fitness": "Forma física general",
  Male: "Hombre",
  Female: "Mujer",
  Other: "Otro",
  "Prefer not to say": "Prefiero no decirlo",
  "Resistance training": "Entrenamiento con cargas",
  "No preference": "Sin preferencia",
  Dumbbells: "Mancuernas",
  Barbells: "Barras",
  "Resistance machines": "Máquinas",
  "Cable machines": "Poleas",
  "Cardiovascular equipment": "Máquinas de cardio",
  Shoulder: "Hombro",
  Elbow: "Codo",
  Wrist: "Muñeca",
  Back: "Espalda",
  Hip: "Cadera",
  Knee: "Rodilla",
  Ankle: "Tobillo",
  Primary: "Principal",
  Secondary: "Secundario",
  Accessory: "Accesorio",
  Cardio: "Cardio",
  Mobility: "Movilidad",
};

/** Spanish label for a schema value. Unknown values are shown as they are. */
export function label(value: string): string {
  return LABELS[value] ?? value;
}
