# Backlog completo — Fase 1: baseline y evaluación

Este documento reúne las 7 épicas y sus 39 subtareas. El script de bootstrap crea cada épica y subtarea como GitHub Issue/sub-issue para permitir estados, responsables y comentarios independientes.

## P1-01 — [P1-01] Definir alcance, usuarios y requisitos del baseline

**Prioridad:** P0  
**Workstream:** Research  
**Objetivo:** Cerrar qué problema resuelve el baseline, qué información recibe y qué queda fuera.

**Definition of Done de la épica:**
- [ ] Carta del proyecto revisada por el equipo.
- [ ] Perfil, petición y salida definidos.
- [ ] Exclusiones y límites de seguridad documentados.
- [ ] Variables comunes para comparar sistemas registradas en DECISIONS.md.

### Subtareas

#### P1-01.1 — [P1-01.1] Definir población objetivo y alcance funcional

**Prioridad:** P0 · **Workstream:** Research

Acordar usuarios adultos sanos, fuerza/hipertrofia y entorno de gimnasio. Documentar objetivos cubiertos y casos excluidos.

**Definition of Done:**
- [ ] Población y contexto escritos en PROJECT_CHARTER.md.
- [ ] Quedan explícitamente fuera patología, rehabilitación, menores y prescripción clínica.

#### P1-01.2 — [P1-01.2] Especificar el perfil de usuario y las peticiones

**Prioridad:** P0 · **Workstream:** Data

Definir campos obligatorios/opcionales del perfil, unidades, categorías y ejemplos de peticiones en español.

**Definition of Done:**
- [ ] Campos definidos con tipo y valores permitidos.
- [ ] Se documentan campos ausentes y cómo se representan.
- [ ] Se incluyen ejemplos representativos.

#### P1-01.3 — [P1-01.3] Definir formato de salida y alcance de una sesión

**Prioridad:** P0 · **Workstream:** Model

Acordar que el output de la primera versión será una única sesión estructurada; enumerar ejercicios, series, repeticiones, descansos, intensidad si se utiliza y duración estimada.

**Definition of Done:**
- [ ] Campos del plan documentados.
- [ ] Se separan campos obligatorios de opcionales.
- [ ] El esquema no promete precisión fisiológica que no pueda validarse.

#### P1-01.4 — [P1-01.4] Documentar exclusiones, salvaguardas y privacidad

**Prioridad:** P0 · **Workstream:** Safety

Definir señales que requieren detener la recomendación o derivar a un profesional. Establecer el uso de datos sintéticos y la prohibición de subir información personal real.

**Definition of Done:**
- [ ] Límites de uso y casos de derivación documentados.
- [ ] Reglas de privacidad incluidas en README y protocolo.
- [ ] La lista de fallos críticos queda preparada para revisión profesional.

#### P1-01.5 — [P1-01.5] Fijar condiciones comunes de comparación experimental

**Prioridad:** P0 · **Workstream:** Research

Definir qué se mantendrá constante entre baseline y sistemas futuros: modelo, perfil, petición, prompt base, JSON schema, decoding, dataset y criterios de scoring.

**Definition of Done:**
- [ ] Lista de variables controladas documentada.
- [ ] Se define RAG como única diferencia de la primera comparación planificada, y validación como factor separado.

#### P1-01.6 — [P1-01.6] Revisar y aprobar la carta del proyecto

**Prioridad:** P1 · **Workstream:** Documentation

Revisar PROJECT_CHARTER.md y cerrar la versión inicial con el equipo/tutor.

**Definition of Done:**
- [ ] Comentarios resueltos o registrados.
- [ ] La versión aprobada tiene fecha y responsable.

## P1-02 — [P1-02] Diseñar y construir el benchmark de perfiles y peticiones

**Prioridad:** P0  
**Workstream:** Data  
**Objetivo:** Crear un conjunto de 40–50 casos sintéticos con condiciones esperadas revisables.

**Definition of Done de la épica:**
- [ ] Benchmark v1 en JSONL.
- [ ] Cobertura documentada.
- [ ] Casos de test separados y congelados.
- [ ] Todos los registros pasan validación de esquema y revisión manual.

### Subtareas

#### P1-02.1 — [P1-02.1] Diseñar la matriz de cobertura del benchmark

**Prioridad:** P0 · **Workstream:** Data

Definir combinaciones de nivel, objetivo, duración, equipamiento, grupos musculares, petición habitual y casos límite.

**Definition of Done:**
- [ ] Matriz de cobertura guardada en documentación.
- [ ] Se identifican huecos y categorías sobrerrepresentadas.

#### P1-02.2 — [P1-02.2] Crear 40–50 perfiles y peticiones sintéticas

**Prioridad:** P0 · **Workstream:** Data

Crear los casos con perfiles adultos ficticios y peticiones realistas en español. Evitar variaciones triviales de una misma plantilla.

**Definition of Done:**
- [ ] Se alcanza el objetivo inicial de 40–50 casos o se documenta una desviación justificada.
- [ ] No se utiliza información personal real.

#### P1-02.3 — [P1-02.3] Etiquetar restricciones y condiciones esperadas por caso

**Prioridad:** P0 · **Workstream:** Evaluation

Para cada caso, anotar músculos objetivo, duración máxima, equipo disponible, si hace falta aclarar la petición y si debe activarse una salvaguarda.

**Definition of Done:**
- [ ] Cada caso tiene expected constraints.
- [ ] Las etiquetas se definen antes de ejecutar el modelo.
- [ ] Las etiquetas ambiguas se revisan manualmente.

#### P1-02.4 — [P1-02.4] Añadir casos límite, ambiguos y de seguridad

**Prioridad:** P1 · **Workstream:** Safety

Añadir peticiones con restricciones incompatibles, falta de información, tiempo limitado, equipo ausente, entrenamiento reciente y señales de alarma.

**Definition of Done:**
- [ ] Cada tipo de caso límite está representado.
- [ ] Se documenta la respuesta esperada (aclarar, adaptar o derivar).

#### P1-02.5 — [P1-02.5] Definir split development/test y congelar benchmark

**Prioridad:** P0 · **Workstream:** Data

Propuesta inicial: 30 casos de development y 20 de test. Separar el test para que no se utilice durante el ajuste del prompt.

**Definition of Done:**
- [ ] Cada caso tiene split.
- [ ] La composición de los splits está documentada.
- [ ] Se registra versión y hash del fichero congelado.

#### P1-02.6 — [P1-02.6] Validar esquema y revisar calidad del benchmark

**Prioridad:** P0 · **Workstream:** Data

Validar cada línea con JSON Schema/Pydantic y realizar una revisión humana de consistencia y duplicados.

**Definition of Done:**
- [ ] Todos los registros pasan validación.
- [ ] No hay case_id duplicados.
- [ ] Revisión manual y correcciones registradas.

## P1-03 — [P1-03] Definir el protocolo y la rúbrica de evaluación

**Prioridad:** P0  
**Workstream:** Evaluation  
**Objetivo:** Convertir la calidad de una rutina en dimensiones observables y puntuables.

**Definition of Done de la épica:**
- [ ] Protocolo de evaluación versionado.
- [ ] Rúbrica 1–5 con anclajes.
- [ ] Métricas automáticas y fallos críticos definidos.
- [ ] Proceso de evaluación humana documentado.

### Subtareas

#### P1-03.1 — [P1-03.1] Definir dimensiones y rúbrica humana 1–5

**Prioridad:** P0 · **Workstream:** Evaluation

Definir relevancia, personalización, coherencia, viabilidad, claridad y precisión/fundamentación. Crear anclajes por nivel para evitar puntuaciones vagas.

**Definition of Done:**
- [ ] Cada dimensión tiene definición y criterios 1/3/5.
- [ ] La fundamentación del baseline no exige citas RAG.

#### P1-03.2 — [P1-03.2] Definir métricas automáticas de estructura y restricciones

**Prioridad:** P0 · **Workstream:** Evaluation

Especificar parse rate, schema compliance, target coverage, equipment compliance, duration compliance, constraint violation rate, duplicados y latencia.

**Definition of Done:**
- [ ] Cada métrica tiene fórmula, unidad y limitaciones.
- [ ] Las reglas no convierten preferencias controvertidas en verdades universales.

#### P1-03.3 — [P1-03.3] Crear taxonomía de errores críticos de seguridad

**Prioridad:** P0 · **Workstream:** Safety

Definir errores críticos y señales que requieren rechazar/derivar. Revisar la lista con un profesional cualificado cuando sea posible.

**Definition of Done:**
- [ ] Taxonomía documentada.
- [ ] Los fallos críticos se reportan separadamente y no se compensan con la media.

#### P1-03.4 — [P1-03.4] Preparar instrucciones de evaluación ciega

**Prioridad:** P1 · **Workstream:** Evaluation

Definir cómo presentar casos y outputs aleatorizados a evaluadores sin indicar la arquitectura que los generó.

**Definition of Done:**
- [ ] Instrucciones y hoja de puntuación creadas.
- [ ] Se describe el procedimiento de aleatorización y anonimización de condición.

#### P1-03.5 — [P1-03.5] Definir acuerdo entre evaluadores y adjudicación

**Prioridad:** P1 · **Workstream:** Evaluation

Establecer idealmente dos revisores independientes y un estadístico de acuerdo apropiado para puntuaciones ordinales; documentar alternativa si no hay segundo revisor experto.

**Definition of Done:**
- [ ] Número y cualificación deseada de evaluadores documentados.
- [ ] Se define cómo tratar desacuerdos y limitaciones.

#### P1-03.6 — [P1-03.6] Crear plantilla de anotación y cálculo de métricas

**Prioridad:** P1 · **Workstream:** Evaluation

Diseñar CSV/JSON o formulario con caso, condición, puntuaciones, fallos críticos y comentarios; definir exportación agregada.

**Definition of Done:**
- [ ] La plantilla se puede aplicar a todos los outputs.
- [ ] Las dimensiones y los valores permitidos están validados.

## P1-04 — [P1-04] Crear referencias de evaluación post-hoc

**Prioridad:** P1  
**Workstream:** Data  
**Objetivo:** Preparar una taxonomía mínima y reglas de comprobación que no se entregan al baseline.

**Definition of Done de la épica:**
- [ ] Taxonomía de ejercicios y músculos versionada.
- [ ] Reglas post-hoc documentadas.
- [ ] Se garantiza que el baseline no recibe este contenido como contexto.

### Subtareas

#### P1-04.1 — [P1-04.1] Definir esquema de referencia para ejercicios

**Prioridad:** P1 · **Workstream:** Data

Definir campos para nombre, sinónimos, músculos principales/secundarios, equipo, patrón de movimiento y dificultad.

**Definition of Done:**
- [ ] Esquema de referencia documentado.
- [ ] Se admite más de un músculo implicado.

#### P1-04.2 — [P1-04.2] Construir catálogo inicial para scoring

**Prioridad:** P1 · **Workstream:** Data

Curar una selección pequeña de ejercicios comunes que permita revisar nombres, equipo y grupos musculares.

**Definition of Done:**
- [ ] Entradas iniciales revisadas.
- [ ] La fuente o criterio de inclusión está anotado.

#### P1-04.3 — [P1-04.3] Definir reglas post-hoc sin alterar la salida

**Prioridad:** P1 · **Workstream:** Evaluation

Diseñar comprobaciones que inspeccionen la salida guardada y generen flags. No corregir ni regenerar el output del baseline.

**Definition of Done:**
- [ ] Las reglas solo producen métricas/flags.
- [ ] Se conserva el output raw original.

#### P1-04.4 — [P1-04.4] Revisar taxonomía y reglas con criterio experto

**Prioridad:** P2 · **Workstream:** Research

Solicitar revisión de un entrenador o profesional de ciencias del deporte para los mapeos y umbrales utilizados.

**Definition of Done:**
- [ ] Feedback y cambios documentados; si no se consigue revisión, la limitación queda explícita.

## P1-05 — [P1-05] Seleccionar modelo open-weight y configurar inferencia local

**Prioridad:** P0  
**Workstream:** Model  
**Objetivo:** Seleccionar un modelo compatible con hardware, español y JSON, registrando licencia y revisión.

**Definition of Done de la épica:**
- [ ] Hardware inventariado.
- [ ] Modelo y licencia revisados.
- [ ] Inferencia local funcional.
- [ ] Pruebas de humo y metadatos registrados.

### Subtareas

#### P1-05.1 — [P1-05.1] Inventariar hardware y sistema operativo

**Prioridad:** P0 · **Workstream:** Model

Registrar CPU, RAM, GPU, VRAM, sistema operativo y espacio en disco del equipo que ejecutará inferencia.

**Definition of Done:**
- [ ] Ficha de hardware guardada.
- [ ] Limitaciones de ejecución local identificadas.

#### P1-05.2 — [P1-05.2] Comparar candidatos y verificar licencias

**Prioridad:** P0 · **Workstream:** Research

Comparar 2–3 modelos candidatos por capacidad en español, salida estructurada, tamaño, consumo, latencia y términos de licencia/model card.

**Definition of Done:**
- [ ] Tabla comparativa con enlaces a model cards.
- [ ] Licencia exacta y restricciones revisadas; no asumir que open-weight equivale a open-source.
- [ ] Se elige candidato y alternativa justificados.

#### P1-05.3 — [P1-05.3] Instalar runtime local y descargar el modelo elegido

**Prioridad:** P0 · **Workstream:** Model

Configurar Ollama o runtime equivalente y fijar etiqueta/revisión exacta del modelo.

**Definition of Done:**
- [ ] El modelo carga localmente.
- [ ] La versión/revisión queda registrada.
- [ ] No se requieren credenciales API para la generación baseline.

#### P1-05.4 — [P1-05.4] Ejecutar pruebas de humo en español y JSON

**Prioridad:** P0 · **Workstream:** Model

Probar prompts representativos, parsing JSON, errores, latencia y consumo de memoria.

**Definition of Done:**
- [ ] Resultados de pruebas guardados.
- [ ] Se conoce si hace falta cuantización o cambiar de tamaño.

#### P1-05.5 — [P1-05.5] Registrar entorno y configuración reproducible

**Prioridad:** P1 · **Workstream:** Documentation

Guardar versiones de Python/runtime, model id, parámetros, hardware y comandos para reproducir la ejecución.

**Definition of Done:**
- [ ] Ficha reproducible en docs/ o experiments/.
- [ ] No se suben tokens, secretos ni modelos binarios al repositorio.

## P1-06 — [P1-06] Implementar el generador baseline sin RAG

**Prioridad:** P0  
**Workstream:** Model  
**Objetivo:** Implementar generación local estructurada desde perfil y petición, sin contexto externo recuperado.

**Definition of Done de la épica:**
- [ ] Esquemas validados.
- [ ] Prompt versionado.
- [ ] Generación local ejecutable.
- [ ] Outputs raw y metadatos persistidos.
- [ ] Prompt y configuración congelados tras el piloto.

### Subtareas

#### P1-06.1 — [P1-06.1] Diseñar y versionar el prompt baseline

**Prioridad:** P0 · **Workstream:** Model

Escribir instrucciones para interpretar perfil y petición, producir una sesión y expresar incertidumbre/solicitar aclaración cuando falte información.

**Definition of Done:**
- [ ] Prompt almacenado como archivo versionado.
- [ ] No contiene papers, resultados de búsqueda ni catálogo externo.
- [ ] Versión del prompt identificable.

#### P1-06.2 — [P1-06.2] Completar esquemas Pydantic de entrada y salida

**Prioridad:** P0 · **Workstream:** Model

Formalizar el perfil, la petición, el plan de entrenamiento y el registro de ejecución.

**Definition of Done:**
- [ ] Campos y tipos documentados.
- [ ] Pruebas de validación positivas y negativas.
- [ ] El esquema no impone umbrales deportivos sin justificación.

#### P1-06.3 — [P1-06.3] Implementar cliente de inferencia local

**Prioridad:** P0 · **Workstream:** Model

Implementar wrapper para invocar el modelo local, gestionar timeout/errores y recoger metadatos.

**Definition of Done:**
- [ ] Una función recibe perfil+petición y devuelve respuesta raw.
- [ ] Errores de runtime quedan registrados.
- [ ] Configuración externa al código mediante variables/config.

#### P1-06.4 — [P1-06.4] Persistir prompts, outputs y metadatos por caso

**Prioridad:** P0 · **Workstream:** Data

Guardar outputs raw, parseados si son válidos, parámetros, latencia, model id, prompt version y case_id.

**Definition of Done:**
- [ ] Cada resultado se puede rastrear al caso y configuración.
- [ ] Los outputs originales no se sobrescriben.

#### P1-06.5 — [P1-06.5] Ejecutar piloto con 5 casos development

**Prioridad:** P1 · **Workstream:** Evaluation

Ejecutar un piloto pequeño para detectar fallos de formato, prompts poco claros y problemas de runtime antes del congelado.

**Definition of Done:**
- [ ] Cinco casos ejecutados o fallos documentados.
- [ ] Cambios de prompt anotados.
- [ ] No se consulta ni ajusta con el test set.

#### P1-06.6 — [P1-06.6] Congelar versión del baseline y parámetros

**Prioridad:** P0 · **Workstream:** Documentation

Fijar modelo/revisión, prompt, schema y parámetros para la ejecución principal; registrar hash/commit.

**Definition of Done:**
- [ ] Ficha de configuración baseline_v1 publicada.
- [ ] Cualquier cambio posterior exige nueva versión de experimento.

## P1-07 — [P1-07] Ejecutar, evaluar y documentar el baseline

**Prioridad:** P0  
**Workstream:** Evaluation  
**Objetivo:** Obtener resultados reproducibles del baseline y una taxonomía de errores para orientar Fase 2.

**Definition of Done de la épica:**
- [ ] Conjunto test ejecutado bajo configuración congelada.
- [ ] Métricas y evaluación humana disponibles o limitación documentada.
- [ ] Informe de resultados y errores terminado.

### Subtareas

#### P1-07.1 — [P1-07.1] Ejecutar baseline sobre development

**Prioridad:** P1 · **Workstream:** Evaluation

Ejecutar el conjunto development con la configuración congelada y comprobar que el pipeline de evaluación funciona.

**Definition of Done:**
- [ ] Outputs y logs completos.
- [ ] Errores de ejecución revisados.

#### P1-07.2 — [P1-07.2] Ejecutar baseline sobre test sin ajustar el prompt

**Prioridad:** P0 · **Workstream:** Evaluation

Ejecutar una vez el conjunto test con el prompt/modelo/parámetros congelados. No modificar el prompt a partir de los resultados test para la misma versión.

**Definition of Done:**
- [ ] Todos los casos test tienen registro de ejecución o error explícito.
- [ ] La configuración y commit SHA están registrados.

#### P1-07.3 — [P1-07.3] Calcular métricas automáticas

**Prioridad:** P0 · **Workstream:** Evaluation

Calcular parsing, schema compliance, restricciones, cobertura de músculos, equipo, duración, duplicados y latencia.

**Definition of Done:**
- [ ] Métricas agregadas y desglosadas por tag.
- [ ] Casos fallidos incluidos en denominadores o informados aparte con criterio explícito.

#### P1-07.4 — [P1-07.4] Realizar evaluación humana ciega

**Prioridad:** P1 · **Workstream:** Evaluation

Aplicar rúbrica a outputs anonimizados y aleatorizados; priorizar dos evaluadores independientes cualificados.

**Definition of Done:**
- [ ] Hojas de puntuación guardadas.
- [ ] Cualificación y procedimiento documentados.
- [ ] Si no se consigue evaluación experta, se explicita como limitación.

#### P1-07.5 — [P1-07.5] Analizar errores, casos difíciles y desacuerdos

**Prioridad:** P1 · **Workstream:** Research

Agrupar errores por formato, personalización, viabilidad, coherencia, seguridad y afirmaciones dudosas. Identificar patrones por tipo de perfil/petición.

**Definition of Done:**
- [ ] Taxonomía de errores con ejemplos anonimizados.
- [ ] Se destacan fallos críticos por separado.
- [ ] Se documentan desacuerdos de evaluación.

#### P1-07.6 — [P1-07.6] Redactar informe de baseline y recomendaciones para Fase 2

**Prioridad:** P0 · **Workstream:** Documentation

Preparar resultados, tablas/gráficos, limitaciones, decisiones y prioridades de mejora para la fase RAG.

**Definition of Done:**
- [ ] Informe baseline v1 terminado.
- [ ] Se documentan limitaciones del tamaño muestral y del evaluador.
- [ ] El informe enlaza dataset, prompts, outputs y código por versión.

