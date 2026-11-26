# Guía para probar FitEvidence AI en local

Esta guía explica cómo arrancar el modelo, el backend y el frontend en un Mac para generar sesiones de entrenamiento desde el navegador o el móvil.

## Cómo encajan las piezas

```text
Navegador o móvil  →  Frontend (Next.js o Expo)  →  API (FastAPI)  →  Ollama (modelo local)
```

| Pieza | Puerto | Qué hace |
|---|---|---|
| Ollama | 11434 | Ejecuta el modelo `qwen2.5:7b` |
| API (FastAPI) | 8000 | Construye el prompt, llama al modelo, valida la respuesta y calcula métricas |
| Frontend web (Next.js) | 3000 | Formulario de perfil y petición, y vista del resultado |
| Frontend móvil (Expo) | 8081 | El mismo formulario en iOS, Android o web |

El frontend web no llama a la API directamente: Next.js reenvía las peticiones a `/api` hacia el puerto 8000, así que no hay que configurar CORS.

## 1. Requisitos

| Herramienta | Versión | Instalación |
|---|---|---|
| uv | Cualquiera reciente | `brew install uv` |
| Node.js | 24 LTS (recomendada) | `brew install node@24` o `nvm use` dentro de `frontend/` |
| pnpm | 12 | No hace falta instalarlo: se usa con `npx pnpm@12.23.0` |
| Ollama | Cualquiera reciente | `brew install ollama` |

Node 25 también ha funcionado en las pruebas, pero Metro y React Native 0.88 solo admiten oficialmente Node 22, 24 y 26 o superior. Si aparece un error extraño con Metro, cambia a Node 24.

## 2. Preparación (solo la primera vez)

Desde la raíz del repositorio:

```bash
# Dependencias de Python
uv sync --extra dev

# Modelo local (unos 4,7 GB)
brew services start ollama
ollama pull qwen2.5:7b

# Dependencias del frontend
cd frontend
npx pnpm@12.23.0 install
cd ..
```

El modelo se puede cambiar con la variable `OLLAMA_MODEL` en un archivo `.env` en la raíz, a partir de `.env.example`. Si no se indica, se usa `qwen2.5:7b`.

## 3. Arrancar todo

Necesitas Ollama en marcha y dos terminales abiertas.

### Ollama

Comprueba que responde:

```bash
curl http://localhost:11434/api/version
```

Si no responde, arráncalo con `brew services start ollama` o abriendo la aplicación de Ollama.

### Terminal 1: backend

Desde la raíz del repositorio:

```bash
uv run uvicorn api.main:app --reload
```

Comprueba que funciona:

```bash
curl http://localhost:8000/api/health
```

La respuesta debe indicar `"ollama": "ok"` y `"model_available": true`. También puedes abrir http://localhost:8000/docs para probar la API desde el navegador, sin frontend.

### Terminal 2: frontend web

```bash
cd frontend
npx pnpm@12.23.0 dev:web
```

Abre http://localhost:3000. La demo visual de los componentes está en http://localhost:3000/demo.

## 4. Qué probar

Rellena la edad y escribe una petición. Estas cuatro cubren los tipos de respuesta del sistema:

| Petición | Respuesta esperada | Tiempo aproximado |
|---|---|---|
| «Me duele mucho el pecho y estoy mareado, ¿entreno hoy?» | Aviso de seguridad (`safety_referral`) | 5–15 s |
| «Quiero preparar una maratón» | Fuera de alcance (`out_of_scope`) | 5–15 s |
| «Quiero entrenar» | Preguntas de aclaración (`clarification`) o un plan con valores por defecto | 5–40 s |
| «Quiero entrenar pecho y tríceps» | Plan de entrenamiento (`plan`) | 20–40 s |

Debajo de cada resultado aparecen el modelo y la latencia. El botón **Ver JSON del modelo** muestra la respuesta original, sin modificar.

**Limitación conocida:** ahora mismo las peticiones de entrenamiento suelen mostrar el aviso «La respuesta del modelo no cumple el esquema». El modelo omite las series, repeticiones, descanso o RPE de los ejercicios de fuerza, porque el esquema que recibe Ollama no marca esos campos como obligatorios. Es un problema conocido y pendiente de corregir.

## 5. Probar en el móvil (opcional)

```bash
cd frontend
npx pnpm@12.23.0 dev:mobile
```

En la terminal de Expo, pulsa:

- `w` para abrir la versión web.
- `i` para el simulador de iOS (requiere Xcode).
- `a` para el emulador de Android (requiere Android Studio).

La app llama a la API en `http://localhost:8000` por defecto. Según dónde se ejecute, hay que cambiar la dirección con `EXPO_PUBLIC_API_URL`:

| Dónde se ejecuta | Dirección de la API |
|---|---|
| Expo web o simulador de iOS | `http://localhost:8000` (por defecto) |
| Emulador de Android | `http://10.0.2.2:8000` |
| Móvil físico con Expo Go | La IP local del Mac, por ejemplo `http://192.168.1.20:8000` |

En un móvil físico, el teléfono y el Mac deben estar en la misma red WiFi, y la API debe aceptar conexiones de la red:

```bash
# Terminal 1, desde la raíz del repositorio
uv run uvicorn api.main:app --reload --host 0.0.0.0

# Terminal 2, desde frontend/
EXPO_PUBLIC_API_URL=http://$(ipconfig getifaddr en0):8000 npx pnpm@12.23.0 dev:mobile
```

## 6. Pruebas automáticas

```bash
# Backend: esquemas, métricas, generador y API (desde la raíz)
uv run pytest

# Frontend: tipos de la librería y de las dos apps (desde frontend/)
npx pnpm@12.23.0 typecheck

# Frontend: build de producción de la web (desde frontend/)
npx pnpm@12.23.0 build
```

Las pruebas del backend no necesitan Ollama: simulan sus respuestas.

## 7. Problemas frecuentes

| Síntoma | Causa | Solución |
|---|---|---|
| «No se puede conectar con la API» | El backend no está en marcha | Arranca la terminal 1 |
| Aviso de que Ollama no responde | Ollama está parado | `brew services start ollama` |
| Aviso de que el modelo no está descargado | Falta el modelo | `ollama pull qwen2.5:7b` |
| `Address already in use` | El puerto ya está ocupado por otro proceso | `lsof -nP -iTCP:8000 -sTCP:LISTEN` para ver qué proceso es, y ciérralo |
| Error `Can't find variable: global` o similar en el navegador | Configuración antigua de Next.js en caché | Para `dev:web` con `Ctrl+C`, borra `frontend/apps/next/.next` y vuelve a arrancarlo |
| La generación tarda mucho | El modelo se está cargando en memoria | La primera petición tras arrancar Ollama es más lenta; las siguientes van más rápido |
| El móvil no conecta con la API | Dirección o red incorrectas | Revisa la sección 5: misma red WiFi, `--host 0.0.0.0` y la IP correcta |

## 8. Parar todo

- Pulsa `Ctrl+C` en las terminales del backend y del frontend.
- Para detener Ollama: `brew services stop ollama`.
