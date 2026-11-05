# Especificación del benchmark v1

## Objetivo

Definir un conjunto reproducible de perfiles sintéticos y peticiones de entrenamiento para probar el baseline y futuras arquitecturas.

## Unidad de evaluación

Un caso = un perfil + una petición + restricciones esperadas + metadatos de evaluación.

## Esquema recomendado (JSONL)

Cada línea debe ser un objeto JSON con:

- `case_id`: identificador estable.
- `split`: `development` o `test`.
- `profile`: campos de usuario.
- `request`: petición textual en español.
- `expected`: condiciones esperadas que puede revisar el evaluador.
- `tags`: categorías para analizar cobertura.

Ejemplo:

```json
{
  "case_id": "FE-0001",
  "split": "development",
  "profile": {
    "age_years": 27,
    "experience_level": "beginner",
    "goal": "hypertrophy",
    "training_days_per_week": 3,
    "session_duration_minutes": 50,
    "equipment": ["full_gym"],
    "restrictions": []
  },
  "request": "Quiero entrenar pecho y tríceps.",
  "expected": {
    "target_muscles": ["chest", "triceps"],
    "max_duration_minutes": 50,
    "must_respect_experience_level": true,
    "clarification_expected": false
  },
  "tags": ["beginner", "hypertrophy", "normal"]
}
```

## Cobertura sugerida

- Nivel: principiante, intermedio y avanzado.
- Objetivo: hipertrofia, fuerza y acondicionamiento general de fuerza.
- Tiempo: sesiones cortas, medias y largas.
- Equipamiento: gimnasio completo y material limitado.
- Peticiones: grupo muscular, tren superior/inferior, cuerpo completo y petición con objetivo temporal.
- Casos borde: petición incompleta, conflicto entre perfil y petición, material incompatible, repetición reciente, petición de exceso no razonable y señales de alarma.

## Volumen y partición

Objetivo inicial 40–50 casos. Como punto de partida, 30 development y 20 test. El split se documenta en el repositorio y no se cambia después de congelar prompt/configuración sin registrar una nueva versión.

## Reglas de calidad

- Utilizar perfiles sintéticos; no copiar información personal real.
- Evitar que todos los casos sean simples variaciones del mismo ejemplo.
- Definir etiquetas `expected` antes de ejecutar el modelo.
- Revisar manualmente los casos y sus restricciones esperadas.
- Mantener el conjunto test separado de los experimentos de ajuste.
- Versionar cambios: `benchmark_v1`, `benchmark_v1.1`, etc.

## Minimización de datos del perfil

Para generar una sesión de fuerza no se presupone que peso y altura sean obligatorios: se recogerán solo si una decisión concreta del sistema los necesita. En el MVP, priorizar edad (para validar mayoría de edad), experiencia, objetivo, días disponibles, tiempo por sesión, equipamiento, preferencias y restricciones relevantes. Evitar almacenar diagnósticos o datos de salud reales; los escenarios de seguridad serán sintéticos.
