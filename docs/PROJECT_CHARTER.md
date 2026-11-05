# Carta del proyecto

## Título provisional

**FitEvidence AI: generación y evaluación de planes de entrenamiento personalizados mediante modelos de lenguaje y recuperación de evidencia científica.**

## Problema

Los modelos de lenguaje pueden generar sesiones de entrenamiento convincentes, pero una respuesta fluida no demuestra que el plan sea adecuado para el perfil, viable, consistente o respaldado por evidencia. El proyecto investigará si un sistema que recupera conocimiento científico y aplica controles explícitos mejora una línea base LLM.

## Pregunta de investigación

¿En qué medida la incorporación de recuperación de evidencia científica y mecanismos de validación mejora la calidad, personalización, fundamentación y fiabilidad de planes de entrenamiento generados por un LLM sin recuperación?

## Hipótesis

- **H1 — Fundamentación:** la recuperación de evidencia relevante aumentará la proporción de afirmaciones y decisiones justificadas por fuentes pertinentes.
- **H2 — Personalización:** incorporar evidencia contextual y restricciones estructuradas mejorará el cumplimiento de las necesidades del perfil.
- **H3 — Fiabilidad:** los controles deterministas reducirán errores estructurales y violaciones de restricciones verificables.

Las hipótesis se contrastarán mediante experimentos comparativos; no se presupone que todas se confirmen.

## Alcance del MVP de investigación

- Adultos sanos.
- Entrenamiento de fuerza e hipertrofia.
- Gimnasio convencional.
- Petición en español y perfil estructurado.
- Generación de una sesión, no una planificación anual ni una prescripción clínica.
- Modelos de pesos abiertos/locales como primera opción.
- La evaluación de entrenamiento será central; la nutrición se pospone.

## Fuera de alcance inicial

Nutrición individualizada completa, patologías o rehabilitación, menores, embarazo, análisis de vídeo/postura, voz, aprendizaje por refuerzo, fine-tuning y aplicación móvil de producción.

## Aportación esperada

1. Benchmark controlado de perfiles y peticiones.
2. Línea base reproducible con LLM sin recuperación científica.
3. Corpus científico curado y estructura de evidencia en una fase posterior.
4. Comparación de arquitecturas de recuperación y generación.
5. Protocolo de evaluación que combine métricas automáticas y revisión experta.

## Criterios de éxito de Fase 1

- Requisitos y límites de uso aprobados.
- Dataset v1 con casos y restricciones esperadas documentadas.
- Protocolo de evaluación y rúbrica versionados.
- Modelo local seleccionado con licencia y revisión registradas.
- Baseline ejecutable que genere y guarde salidas estructuradas.
- Resultados y errores del baseline reproducibles.

## Principios

- Open-source/open-weight primero, verificando licencia de cada componente.
- No confundir el conocimiento paramétrico de un LLM con evidencia recuperada.
- No presentar referencias inventadas como soporte científico.
- Separar generación, validación y evaluación.
- Registrar cambios y decisiones experimentales.
- Minimizar datos personales y utilizar perfiles sintéticos.
