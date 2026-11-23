# Evaluation

Métricas post-hoc del sistema. Las definiciones y su estado están en `docs/EVALUATION_PROTOCOL.md`. La evaluación nunca modifica la salida original.

`metrics.py` implementa las medidas que no dependen del benchmark, del catálogo ni de umbrales expertos: JSON válido, esquema, distribución de respuestas, alcance, coherencia del tiempo y orden de ejercicios.

```python
from evaluation.metrics import evaluate_output, summarize

results = [evaluate_output(raw_output) for raw_output in raw_outputs]
summary = summarize(results)
```

Pendiente: validación del benchmark, métricas que dependen de etiquetas o catálogo, exportación de la hoja de anotación y análisis de resultados.
