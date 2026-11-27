# FitEvidence AI — TFM

**Sistema de generación de planes de entrenamiento personalizados, evaluable y fundamentado en evidencia científica.**

Este repositorio contiene el código, la documentación experimental y la planificación de la **Fase 1: definición del problema, benchmark de evaluación y baseline LLM sin recuperación científica (sin RAG)**.

## Objetivo de la Fase 1

Construir una línea base reproducible que reciba un perfil de usuario y una petición en lenguaje natural y genere una sesión de entrenamiento estructurada. Antes de añadir RAG, se definirá cómo medir la calidad de la salida y se ejecutará el mismo conjunto de casos con una configuración de modelo y prompt congelada.

> El baseline no recibe papers, fragmentos científicos recuperados, búsquedas web ni una base de conocimiento externa. El conocimiento paramétrico del propio modelo no puede eliminarse; por eso lo denominamos **LLM sin recuperación científica**.

## Alcance inicial

- Adultos sanos.
- Entrenamiento de fuerza e hipertrofia.
- Entorno de gimnasio convencional.
- Entrada: perfil estructurado + petición en español.
- Salida: una respuesta JSON de tipo `plan`, `clarification`, `safety_referral` u `out_of_scope`.
- Modelos de pesos abiertos ejecutados localmente como primera opción.
- Sin nutrición, Computer Vision, voz, RL ni aplicación final en esta fase.

### Ampliar el alcance

Los esquemas conservan los demás objetivos y modalidades (pérdida de grasa, cardio, resistencia muscular y fitness general), pero solo se activan los definidos en `ACTIVE_SCOPE` (`src/schemas/scope.py`). Para ampliar el sistema, se crea un nuevo `TrainingScope` y se asigna a `ACTIVE_SCOPE`: el prompt y las comprobaciones de alcance se actualizan a partir de él. Cualquier ampliación es un cambio experimental y requiere nueva versión de prompt, benchmark y evaluación.

## Estructura

```text
.
├── docs/                 # Documentación de fase 1, protocolo y especificaciones
├── issues/phase-1/       # Descripciones legibles de épicas y subtareas
├── data/
│   ├── evaluation/       # Especificación y ejemplos del benchmark
│   ├── exercise_catalog/ # Taxonomía de referencia para evaluar salidas (no se inyecta al baseline)
│   ├── raw/              # Datos originales locales; no subir datos personales
│   └── processed/        # Datos procesados locales
├── notebooks/            # Demostraciones de validación
├── src/
│   ├── baseline/         # Generador baseline y construcción del prompt
│   ├── evaluation/       # Métricas y evaluación
│   ├── prompts/          # Prompts versionados
│   └── schemas/          # Contratos de entrada y salida y alcance activo
└── tests/                # Pruebas
```

## Primeros pasos

1. Instalar [uv](https://docs.astral.sh/uv/), Git y Visual Studio Code.
2. Crear el entorno e instalar dependencias:

   ```bash
   uv sync --extra dev
   ```

3. Ejecutar las pruebas:

   ```bash
   uv run pytest
   ```

4. Leer `docs/Documentation/Phase 1.md` y `docs/EVALUATION_PROTOCOL.md`.
5. Consultar el estado y la correspondencia del backlog en `issues/phase-1/README.md`.

## Modelo local

El modelo concreto **no queda fijado todavía**. La tarea P1-05 seleccionará uno o más candidatos después de revisar RAM/VRAM, velocidad, capacidad en español, salida estructurada y licencia del repositorio/model card. Se registrarán el identificador y la revisión exactos. Ollama es el runtime candidato inicial, no un requisito irreversible.

## Principio experimental

Para que la comparación posterior sea interpretable, se congelarán y documentarán:

- Modelo y versión/revisión.
- Prompt de sistema y plantilla de usuario.
- Esquema de salida.
- Parámetros de generación.
- Dataset y partición.
- Código de evaluación.

En Fase 2 se añadirá recuperación de evidencia científica como variable experimental. Se procurará mantener constantes los demás elementos.

## Seguridad y privacidad

El sistema es un prototipo académico, no un dispositivo médico ni un sustituto de un entrenador o profesional sanitario. El alcance inicial excluye patologías, lesiones, embarazo, menores y prescripción clínica. Se utilizarán perfiles sintéticos o anonimizados; no se incluirán datos personales o de salud reales en el repositorio.

## Estado

- [ ] Fase 1 — Baseline y protocolo de evaluación
- [ ] Fase 2 — Corpus científico, RAG y experimentación comparativa
- [ ] Demo — Interfaz visual (opcional)
