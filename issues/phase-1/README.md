# Backlog Fase 1 — índice de épicas y subtareas

Estos Markdown son la copia documental local del backlog.

## Correspondencia con `docs/Documentation/Phase 1.md`

La documentación y el backlog usan numeraciones distintas. Los identificadores de este backlog son la referencia para planificar; esta tabla indica dónde está documentado cada trabajo.

| Sección en la documentación | Contenido | Tarea del backlog |
|---|---|---|
| P1-01.1 | Población y alcance | P1-01.1 |
| P1-01.2 | Perfil de usuario | P1-01.2 |
| P1-01.3 | Modelo de datos del perfil | P1-06.2 |
| P1-02.1 | Estructura del plan | P1-01.3 |
| P1-02.2 | Esquema JSON de salida | P1-06.2 |
| P1-03.1 | Interacción por chat | P1-01.2 |
| P1-03.2 | Estructura de entrada y prioridades | P1-01.2 |
| P1-03.3 | Prompt base | P1-06.1 |
| P1-03.4 | Contrato de respuesta y alcance activo | P1-01.1, P1-01.3 y P1-06.2 |

## P1-01 — [P1-01] Definir alcance, usuarios y requisitos del baseline
Épica: [P1-01.md](P1-01.md) · Prioridad: **P0** · Área: **Research**
- [P1-01.1 — [P1-01.1] Definir población objetivo y alcance funcional](P1-01.1.md) · P0 · Research
- [P1-01.2 — [P1-01.2] Especificar el perfil de usuario y las peticiones](P1-01.2.md) · P0 · Data
- [P1-01.3 — [P1-01.3] Definir formato de salida y alcance de una sesión](P1-01.3.md) · P0 · Model
- [P1-01.4 — [P1-01.4] Documentar exclusiones, salvaguardas y privacidad](P1-01.4.md) · P0 · Safety
- [P1-01.5 — [P1-01.5] Fijar condiciones comunes de comparación experimental](P1-01.5.md) · P0 · Research
- [P1-01.6 — [P1-01.6] Revisar y aprobar la carta del proyecto](P1-01.6.md) · P1 · Documentation

## P1-02 — [P1-02] Diseñar y construir el benchmark de perfiles y peticiones
Épica: [P1-02.md](P1-02.md) · Prioridad: **P0** · Área: **Data**
- [P1-02.1 — [P1-02.1] Diseñar la matriz de cobertura del benchmark](P1-02.1.md) · P0 · Data
- [P1-02.2 — [P1-02.2] Crear 40–50 perfiles y peticiones sintéticas](P1-02.2.md) · P0 · Data
- [P1-02.3 — [P1-02.3] Etiquetar restricciones y condiciones esperadas por caso](P1-02.3.md) · P0 · Evaluation
- [P1-02.4 — [P1-02.4] Añadir casos límite, ambiguos y de seguridad](P1-02.4.md) · P1 · Safety
- [P1-02.5 — [P1-02.5] Definir split development/test y congelar benchmark](P1-02.5.md) · P0 · Data
- [P1-02.6 — [P1-02.6] Validar esquema y revisar calidad del benchmark](P1-02.6.md) · P0 · Data

## P1-03 — [P1-03] Definir el protocolo y la rúbrica de evaluación
Épica: [P1-03.md](P1-03.md) · Prioridad: **P0** · Área: **Evaluation**
- [P1-03.1 — [P1-03.1] Definir dimensiones y rúbrica humana 1–5](P1-03.1.md) · P0 · Evaluation
- [P1-03.2 — [P1-03.2] Definir métricas automáticas de estructura y restricciones](P1-03.2.md) · P0 · Evaluation
- [P1-03.3 — [P1-03.3] Crear taxonomía de errores críticos de seguridad](P1-03.3.md) · P0 · Safety
- [P1-03.4 — [P1-03.4] Preparar instrucciones de evaluación ciega](P1-03.4.md) · P1 · Evaluation
- [P1-03.5 — [P1-03.5] Definir acuerdo entre evaluadores y adjudicación](P1-03.5.md) · P1 · Evaluation
- [P1-03.6 — [P1-03.6] Crear plantilla de anotación y cálculo de métricas](P1-03.6.md) · P1 · Evaluation

## P1-04 — [P1-04] Crear referencias de evaluación post-hoc
Épica: [P1-04.md](P1-04.md) · Prioridad: **P1** · Área: **Data**
- [P1-04.1 — [P1-04.1] Definir esquema de referencia para ejercicios](P1-04.1.md) · P1 · Data
- [P1-04.2 — [P1-04.2] Construir catálogo inicial para scoring](P1-04.2.md) · P1 · Data
- [P1-04.3 — [P1-04.3] Definir reglas post-hoc sin alterar la salida](P1-04.3.md) · P1 · Evaluation
- [P1-04.4 — [P1-04.4] Revisar taxonomía y reglas con criterio experto](P1-04.4.md) · P2 · Research

## P1-05 — [P1-05] Seleccionar modelo open-weight y configurar inferencia local
Épica: [P1-05.md](P1-05.md) · Prioridad: **P0** · Área: **Model**
- [P1-05.1 — [P1-05.1] Inventariar hardware y sistema operativo](P1-05.1.md) · P0 · Model
- [P1-05.2 — [P1-05.2] Comparar candidatos y verificar licencias](P1-05.2.md) · P0 · Research
- [P1-05.3 — [P1-05.3] Instalar runtime local y descargar el modelo elegido](P1-05.3.md) · P0 · Model
- [P1-05.4 — [P1-05.4] Ejecutar pruebas de humo en español y JSON](P1-05.4.md) · P0 · Model
- [P1-05.5 — [P1-05.5] Registrar entorno y configuración reproducible](P1-05.5.md) · P1 · Documentation

## P1-06 — [P1-06] Implementar el generador baseline sin RAG
Épica: [P1-06.md](P1-06.md) · Prioridad: **P0** · Área: **Model**
- [P1-06.1 — [P1-06.1] Diseñar y versionar el prompt baseline](P1-06.1.md) · P0 · Model
- [P1-06.2 — [P1-06.2] Completar esquemas Pydantic de entrada y salida](P1-06.2.md) · P0 · Model
- [P1-06.3 — [P1-06.3] Implementar cliente de inferencia local](P1-06.3.md) · P0 · Model
- [P1-06.4 — [P1-06.4] Persistir prompts, outputs y metadatos por caso](P1-06.4.md) · P0 · Data
- [P1-06.5 — [P1-06.5] Ejecutar piloto con 5 casos development](P1-06.5.md) · P1 · Evaluation
- [P1-06.6 — [P1-06.6] Congelar versión del baseline y parámetros](P1-06.6.md) · P0 · Documentation

## P1-07 — [P1-07] Ejecutar, evaluar y documentar el baseline
Épica: [P1-07.md](P1-07.md) · Prioridad: **P0** · Área: **Evaluation**
- [P1-07.1 — [P1-07.1] Ejecutar baseline sobre development](P1-07.1.md) · P1 · Evaluation
- [P1-07.2 — [P1-07.2] Ejecutar baseline sobre test sin ajustar el prompt](P1-07.2.md) · P0 · Evaluation
- [P1-07.3 — [P1-07.3] Calcular métricas automáticas](P1-07.3.md) · P0 · Evaluation
- [P1-07.4 — [P1-07.4] Realizar evaluación humana ciega](P1-07.4.md) · P1 · Evaluation
- [P1-07.5 — [P1-07.5] Analizar errores, casos difíciles y desacuerdos](P1-07.5.md) · P1 · Research
- [P1-07.6 — [P1-07.6] Redactar informe de baseline y recomendaciones para Fase 2](P1-07.6.md) · P0 · Documentation

