# Crear el repositorio y el proyecto de GitHub

Este paquete incluye un script que automatiza la creación del repositorio privado, el GitHub Project, los campos, las etiquetas, las épicas y sus subtareas. La operación se ejecuta desde vuestro ordenador con vuestra propia sesión de GitHub; este repositorio local no se publica hasta que lo hagáis.

## Requisitos

- Cuenta de GitHub.
- Git instalado.
- GitHub CLI (`gh`) instalado.
- Python 3.11+.
- VS Code (opcional, recomendado).

## 1. Autenticarse

```bash
gh auth login
gh auth status
gh auth refresh -s project
```

La última orden concede a GitHub CLI el scope necesario para crear/gestionar GitHub Projects. Revisad la autorización en el navegador cuando se solicite.

## 2. Ejecutar el bootstrap

Desde la raíz del repositorio:

```bash
python scripts/bootstrap_github.py --visibility private
```

El script:

1. Comprueba GitHub CLI y la autenticación.
2. Inicializa Git localmente si hace falta y crea el commit inicial.
3. Crea `fitevidence-ai` como repositorio privado (o utiliza el remoto configurado).
4. Crea el proyecto `FitEvidence AI - TFM` y lo enlaza al repositorio.
5. Crea campos `Phase`, `Priority` y `Workstream`.
6. Crea labels para fase, tipo y área.
7. Crea issues de épica y subtareas como sub-issues, y las añade al proyecto.

Si el repositorio o proyecto ya existen, el script intenta reutilizarlos cuando puede. No ejecutar varias veces en paralelo. Revisad los resultados y, si el proceso se interrumpe, comprobad primero qué elementos se han creado antes de volver a ejecutarlo.

## 3. Ajustar el tablero

En GitHub Projects, cread una vista **Board** agrupada por `Status` con columnas:

- Todo
- In Progress
- In Review
- Done

Podéis crear también una vista **Table** filtrada por `Phase = Fase 1` y ordenar por `Priority`.

## 4. Convención de tareas

- Las épicas comienzan por `[P1-XX]`.
- Las subtareas comienzan por `[P1-XX.Y]`.
- Cada subtarea debe tener responsable, prioridad y comentario de progreso cuando haya un cambio significativo.
- No cerrar una tarea sin cumplir su Definition of Done.
- Registrar bloqueos en comentarios y con relaciones `blocked by` cuando aplique.

## 5. Privacidad

El repositorio se crea privado por defecto. Antes de hacerlo público, revisad PDFs, datos, credenciales, notas y derechos de reutilización de documentos científicos.
