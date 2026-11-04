# Canal de negocios — pipeline de video

Historias y decisiones que construyen, transforman o destruyen negocios. Línea editorial y reglas en [`personalidad.md`](personalidad.md).

```
guiones/<fecha>-<slug>.json  →  ElevenLabs (voz + timestamps)  →  Remotion (1080×1920)  →  Zernio (TikTok + Instagram)
```

Hacer push de un guion a `canal-negocios/guiones/` en `main` dispara `.github/workflows/canal-negocios-video.yml`. El MP4 también queda como artifact del run durante 14 días.

## Configuración en GitHub (Settings → Secrets and variables → Actions)

| Tipo | Nombre | Valor |
|---|---|---|
| Secret | `ELEVENLABS_API_KEY` | API key de la cuenta de ElevenLabs del canal |
| Secret | `ELEVENLABS_VOICE_ID` | ID de la voz |
| Secret | `ZERNIO_API_KEY` | API key de la cuenta de Zernio del canal |
| Variable | `ZERNIO_TIKTOK_ID` | accountId de TikTok en Zernio |
| Variable | `ZERNIO_INSTAGRAM_ID` | accountId de Instagram en Zernio |
| Variable | `MODO_PUBLICACION` | `borrador` (por defecto) o `programar` |
| Variable | `HORA_PUBLICACION` | `HH:MM` hora de Bogotá, por defecto `19:30` |

## Local

```bash
cd canal-negocios && npm install
npx remotion studio src/Root.tsx                       # editar el diseño en vivo
npx tsx pipeline/producir.ts guiones/<id>.json --sin-voz   # render sin voz (tiempos estimados)
# con un .env exportado: --publicar=borrador | programar
```

## Guion

Esquema en `src/schema.ts`. Escenas en orden gancho → contexto → decisión → consecuencia → aprendizaje → cierre. Visuales: `titulo`, `dato`, `lista`, `comparacion`, `linea_tiempo`. Cada hecho sobre una empresa o persona real va con su fuente en `fuentes`.
