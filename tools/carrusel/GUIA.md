# Carrusel diario — La Dosis de Ciencia (TikTok)

Rutina: cada día se generan 3 carruseles de 5-6 láminas (ver Ritmo), se sube a este repo y se programa en
TikTok (@ladosisdeciencia) por Zernio como **publicación directa** a las 11:30, 17:30 y 20:30 (America/Bogota),
con descripción y música automática. John recibe el resumen a las ~7:45 y puede pedir cancelarlo.

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

## Ritmo: 3 carruseles al día (desde 2026-11-04)
| Franja | Hora (Bogotá) | Series |
|---|---|---|
| A | 11:30 | Ayuno |
| B | 17:30 | Hormonas y metabolismo / Ejercicio y músculo |
| C | 20:30 | Intestino-cerebro / Sueño y cerebro |
Los tres del día deben ser de temas distintos entre sí y con portadas visualmente distintas (`seed` diferente).

## Temas (banco por serie; ampliar con ángulos nuevos, nunca repetir el historial)
1. **Ayuno** (88% del tráfico llega por búsqueda): qué rompe el ayuno, hora 12/16/18/24/36/48/72, cómo romperlo bien, ayuno en mujeres y ciclo menstrual, después de los 40/50, menopausia, errores comunes, ayuno y sueño, ayuno y ejercicio, ayuno y café, electrolitos, hambre y grelina, ayuno y músculo, 16:8 vs 18:6 vs OMAD, ayuno y colesterol, ayuno y piel, quién NO debe ayunar, mitos del ayuno, ayuno los fines de semana, cetosis vs autofagia.
2. **Hormonas y metabolismo**: insulina, resistencia a la insulina (señales), cortisol, leptina, grelina, GLP-1/Ozempic, tiroides, melatonina, hormona de crecimiento, testosterona y edad, estrógeno, adiponectina, glucagón, picos de glucosa, grasa visceral, hígado graso, azúcar y fructosa.
3. **Ejercicio y músculo**: caminar vs correr, zona 2, fuerza después de los 40, sarcopenia, proteína por comida, creatina (solo evidencia, sin vender producto), sedentarismo y 1 h sentado, NEAT, recuperación.
4. **Intestino-cerebro**: microbioma, serotonina intestinal, nervio vago, fibra, fermentados, ultraprocesados, inflamación intestinal, ansiedad y digestión, antibióticos y microbiota.
5. **Sueño y cerebro**: qué pasa al dormir 5 h, ciclos REM, cafeína y sueño, luz de pantallas, siestas, alcohol y sueño, memoria y sueño, dopamina y scroll, estrés crónico, BDNF.
Audiencia: 77% mayor de 35 años, Latinoamérica. Español neutro, frases cortas.
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
  `tiktok_settings={mediaType:"photo", photoCoverIndex:0, description:<description>, autoAddMusic:true, allowComment:true, privacyLevel:"PUBLIC_TO_EVERYONE", contentPreviewConfirmed:true, expressConsentGiven:true}`,
  `scheduled_for` = hoy a la hora de su franja, `timezone`="America/Bogota".
- No usar `draft:true`: TikTok no pasa el caption a los borradores y John no los encuentra fácilmente (decisión 2026-11-03).
