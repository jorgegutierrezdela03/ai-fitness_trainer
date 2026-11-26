# FitEvidence Frontend

Monorepo con una librería de componentes de cristal para Web, iOS y Android.

| Paquete | Contenido |
|---|---|
| `packages/ui` | Librería `@fitevidence/ui`: `GlassSurface`, `GlassCard`, `Button`, `Badge`, `Input` y `DemoScreen` |
| `apps/expo` | App móvil y web con Expo SDK 58 |
| `apps/next` | App web con Next.js 16 |

## Requisitos

- Node 24 LTS (`.nvmrc`). Metro y React Native 0.88 no admiten Node 25.
- pnpm 12. Sin instalarlo globalmente, usa `npx pnpm@12.23.0` en lugar de `pnpm`.

## Comandos

```bash
pnpm install
pnpm dev:mobile   # Expo: pulsa i (iOS), a (Android) o w (web)
pnpm dev:web      # Next.js en http://localhost:3000
pnpm typecheck
pnpm build
```

## Generar sesiones con el modelo local

Hacen falta tres procesos, cada uno en su terminal:

```bash
ollama serve                                  # o la app de Ollama abierta
uv run uvicorn api.main:app --reload          # desde la raíz del repositorio, puerto 8000
pnpm dev:web                                  # desde frontend/, http://localhost:3000
```

La página principal es el formulario. La demo visual está en `/demo`. Next.js reenvía `/api` a FastAPI, así que no hace falta configurar CORS.

En Expo, la app llama a `EXPO_PUBLIC_API_URL`, que por defecto es `http://localhost:8000`. En el emulador de Android usa `http://10.0.2.2:8000`, y en un móvil físico, la IP local del ordenador.

El modelo se elige con `OLLAMA_MODEL` en el `.env` de la raíz. Si no se indica, se usa `qwen2.5:7b`.

## Cómo se distribuye la librería

`@fitevidence/ui` se publica como código TypeScript, sin compilar. Metro la transpila con `babel-preset-expo` y Next.js con `transpilePackages`. Las variantes por plataforma usan extensiones: `GlassSurface.tsx` en iOS y Android, `GlassSurface.web.tsx` en web.

Next.js usa webpack (`--webpack`) porque Turbopack no aplica las extensiones `.web.*` dentro de algunas dependencias de React Native.

## Reglas para usar el cristal

- Envuelve la pantalla en `GlassProvider` y pon el fondo dentro de `GlassBackdrop`.
- `GlassBackdrop` debe ser hermano de las superficies de cristal, nunca su padre.
- Las pantallas animadas en Next.js se cargan solo en cliente (`next/dynamic` con `ssr: false`).
