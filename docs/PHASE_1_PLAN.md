# Plan de trabajo — Fase 1: baseline y evaluación

**Objetivo:** definir la petición, diseñar un benchmark y evaluar un LLM local sin recuperación de documentos científicos.

**Duración orientativa:** 2–3 semanas, ajustable al calendario y al número de integrantes.

## Definición del baseline

El baseline será un modelo de lenguaje de pesos abiertos que recibe exclusivamente:

1. Un perfil de usuario estructurado.
2. Una petición en lenguaje natural.
3. Un prompt común y un esquema de salida.

No recibe papers, fragmentos recuperados, búsquedas web ni una base de conocimiento externa. Su conocimiento paramétrico permanece, como en cualquier LLM.

La evaluación puede inspeccionar la salida con reglas y referencias externas, pero esa información **no se devuelve al modelo** durante la generación.

## Work packages

### WP1 — Requisitos y protocolo de uso

- Cerrar población, objetivo y entorno.
- Definir campos del perfil y tipos de consulta.
- Definir output: una sesión estructurada.
- Documentar exclusiones y límites de seguridad.
- Fijar qué elementos permanecerán constantes en experimentos futuros.

**Salida:** carta del proyecto y especificación funcional.

### WP2 — Benchmark

- Diseñar matriz de cobertura por nivel, objetivo, grupo muscular, duración, disponibilidad y equipo.
- Crear 40–50 escenarios sintéticos.
- Añadir restricciones esperadas por caso.
- Incluir casos habituales, límites, ambigüedad y consultas que deban rechazarse/derivarse.
- Separar desarrollo y test (propuesta inicial: 30/20) y congelar el test antes de comparar sistemas.
- Validar el esquema y revisar manualmente cada caso.

**Salida:** benchmark v1 versionado y especificación JSONL.

### WP3 — Protocolo de evaluación

- Definir dimensiones y rúbricas de 1–5.
- Separar métricas automáticas de juicio humano.
- Definir fallos críticos que no se compensen con una media alta.
- Preparar instrucciones de revisión ciega.
- Planificar acuerdo entre evaluadores.

**Salida:** protocolo y plantilla de anotación.

### WP4 — Referencias de evaluación

- Definir taxonomía mínima de ejercicios, músculos, equipo y patrones de movimiento.
- Preparar reglas de comprobación post-hoc.
- Justificar umbrales con revisión bibliográfica y/o asesoramiento profesional.

La taxonomía y las reglas se usan para puntuar las salidas; no se inyectan en el prompt del baseline. Si se incorporan al input en una fase posterior, deberá registrarse como un cambio de condición experimental.

**Salida:** catálogo de referencia y reglas documentadas.

### WP5 — Modelo y entorno local

- Registrar hardware disponible.
- Comparar candidatos por licencia, español, calidad de JSON, consumo y latencia.
- Instalar runtime local.
- Ejecutar pruebas de humo.
- Congelar nombre y revisión del modelo.

**Salida:** entorno reproducible y ficha del modelo.

### WP6 — Generador baseline

- Definir esquema Pydantic del perfil y del plan.
- Escribir prompt versionado.
- Implementar cliente de inferencia local.
- Guardar prompt, parámetros, salida raw, salida parseada y metadatos.
- Hacer piloto pequeño, ajustar y congelar prompt/configuración.

**Salida:** generador baseline versionado.

### WP7 — Ejecución y análisis

- Ejecutar primero el conjunto de desarrollo.
- Congelar modelo, prompt y parámetros.
- Ejecutar el conjunto test una sola vez para la comparación principal.
- Calcular métricas automáticas.
- Realizar evaluación humana ciega cuando sea posible.
- Analizar errores y limitaciones.

**Salida:** informe de baseline con resultados y artefactos reproducibles.

## Orden y dependencias

1. WP1 precede al diseño del benchmark y la evaluación.
2. WP2 y WP3 definen qué se genera y cómo se mide.
3. WP4 permite evaluar post-hoc sin ampliar el input del baseline.
4. WP5 puede ejecutarse en paralelo con WP2–WP4.
5. WP6 depende de WP1 y WP5.
6. WP7 depende de WP2, WP3, WP4 y WP6.

## Hitos

| Hito | Criterio de salida |
|---|---|
| M1 — Alcance cerrado | Requisitos, exclusiones y esquema de entrada/salida aprobados. |
| M2 — Benchmark listo | Casos y restricciones esperadas revisados y congelados. |
| M3 — Evaluación definida | Rúbrica, métricas y protocolo de revisión disponibles. |
| M4 — Modelo operativo | Modelo local probado y versión fijada. |
| M5 — Baseline congelado | Prompt, schema y parámetros versionados. |
| M6 — Baseline evaluado | Resultados, errores y limitaciones documentados. |

## Regla de reproducibilidad

Cada ejecución debe guardar: `case_id`, `model_id`, `model_revision`, `runtime`, `prompt_version`, `schema_version`, parámetros de generación, fecha, latencia, tokens si están disponibles, output raw, output parseado y errores de parsing.

## Backlog operativo en GitHub

La planificación se desglosa en **7 épicas y 39 subtareas**. El índice está en `issues/phase-1/README.md` y el manifiesto que utiliza el bootstrap está en `project/backlog_phase1.json`. Cada subtarea tiene objetivo y Definition of Done; los avances y bloqueos se registrarán como comentarios en su GitHub Issue.
