# Carrusel diario — La Dosis de Ciencia (TikTok)

Rutina: cada día se genera un carrusel de 5-6 láminas, se sube a este repo y se envía a
TikTok (@ladosisdeciencia) como **borrador** por Zernio, para que John lo revise, le ponga
música y lo publique. Hora objetivo: 11:30 a. m. (America/Bogota).

## Archivos
- `tools/carrusel/template.html`: diseño (fondo oscuro, dorado, célula procedural, ECG). No usa imágenes de IA.
- `tools/carrusel/render.py`: `python3 tools/carrusel/render.py <spec.json> <carpeta>` → `01.jpg`…`06.jpg` (1080×1920).
- `tiktok/AAAA-MM-DD-slug/spec.json` + láminas: un carrusel por carpeta.
- `tiktok/historial.json`: temas ya hechos. Nunca repetir uno.

## Estructura del spec
- 5 o 6 láminas: `cover` → 3-4 `point` → `cta`.
- `cover`: `title` (usar `[[palabra]]` para resaltar en dorado), `subtitle`, `serie`.
- `point`: `title`, opcional `badge` + `verdict` (`no` | `si` | `gris`), opcional `big` + `bigUnit` (un dato numérico grande), `body` (máx. ~40 palabras, `**negrita**`), opcional `note` (una línea, empieza con `**Etiqueta:**`), opcional `ring` (0-1, arco de progreso para temas de horas de ayuno).
- `cta`: siempre hacia la calculadora: botón "Link en el perfil". Nunca números de teléfono.
- `caption_title`: ≤ 90 caracteres, sin hashtags.
- `description`: caption completo (≤ 4000), lista con ✅⚠️❌ o →, CTA a la calculadora, una pregunta para comentarios, 8-10 hashtags (#dosisdeciencia siempre).

## Temas (en orden de prioridad)
1. Serie Ayuno (lo que más busca la audiencia: 88% del tráfico viene de búsqueda): qué rompe el ayuno, hora por hora, cómo romperlo, ayuno en mujeres, después de los 40/50, errores comunes, ayuno y sueño, ayuno y ejercicio, electrolitos, hambre y grelina.
2. Serie Hormonas: insulina, cortisol, leptina, GLP-1, tiroides, melatonina, hormona de crecimiento.
3. Serie Intestino-cerebro: microbioma, serotonina, nervio vago, fibra, fermentados.
4. Sueño y cerebro (cuando haya pocos temas de 1-3 sin usar).
Audiencia: 77% mayor de 35 años, Latinoamérica. Español neutro, frases cortas.

## Reglas científicas (no negociables)
- Solo afirmaciones con evidencia sólida; si la evidencia es mixta, decirlo ("zona gris", "evidencia mixta").
- Números redondeados y conservadores (≈). Nada de porcentajes inventados.
- Ayunos > 24 h, ayuno seco, embarazo, diabetes con medicación, TCA: siempre "con supervisión médica".
- Nunca prometer curas ni tratar enfermedades. Nada de suplementos ni productos.
- Antes de renderizar, releer cada afirmación y quitar la que no se pueda defender ante un médico.

## Publicación (Zernio)
- Cuenta TikTok: `6a4179799d9472faae14cb5f`.
- `posts_create_post` con `media_items` = URLs raw de GitHub de cada lámina (`https://raw.githubusercontent.com/JohnRodriguezM/media/main/tiktok/<carpeta>/01.jpg` …),
  `platforms=[{platform:"tiktok", accountId:"6a4179799d9472faae14cb5f"}]`, `content` = `caption_title`,
  `tiktok_settings={draft:true, mediaType:"photo", photoCoverIndex:0, description:<description>, autoAddMusic:true, allowComment:true, privacyLevel:"PUBLIC_TO_EVERYONE", contentPreviewConfirmed:true, expressConsentGiven:true}`,
  `scheduled_for` = hoy 11:30, `timezone`="America/Bogota".
- TikTok NO pasa el caption a los borradores (el caption se completa en el editor de la app). Por eso la descripción completa
  siempre se le envía a John en el resumen diario, lista para copiar y pegar.
- TikTok permite máximo 5 borradores pendientes por cuenta en 24 h.
