# Evaluation

Las definiciones y el estado de las medidas están en `docs/EVALUATION_PROTOCOL.md`. La
evaluación no modifica la salida original.

## Métricas deterministas

`metrics.py` implementa las medidas deterministas del plan: JSON y esquema válidos,
distribución de respuestas, alcance, coherencia temporal, orden, volumen, duplicados y
comprobaciones disponibles cuando también se proporciona el perfil.

```python
from evaluation.metrics import evaluate_output, summarize

results = [evaluate_output(raw_output) for raw_output in raw_outputs]
summary = summarize(results)
```

## LLM-as-a-Judge (beta)

`judge.py` ofrece una evaluación cualitativa local con Ollama. Su rúbrica se mantiene en
`src/prompts/judge_system_prompt.md`. Debe ejecutarse después de la validación determinista
y recibir un `TrainingPlanLLM` ya validado. No se integra automáticamente con la API ni
persiste los juicios. Puntúa `profile_alignment`, `request_adherence`, `programming_quality`
y `safety_and_compatibility` de 0 a 5; el razonamiento y los demás textos del juez se
generan en inglés.

```python
from evaluation.judge import JudgeConfig, judge_plan

result = judge_plan(session_input, validated_plan, JudgeConfig.from_env())
```

Por defecto usa el modelo `gemma4`. Se puede cambiar con `JUDGE_MODEL`; la URL se comparte
con el baseline mediante `OLLAMA_BASE_URL`. Los resultados válidos se pueden agregar con
`summarize_judgments`.

Pendiente: benchmark etiquetado y su runner, exportación/persistencia de ejecuciones,
métricas que dependen de catálogo o etiquetas y análisis de resultados.
