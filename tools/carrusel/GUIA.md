# Carrusel diario — La Dosis de Ciencia (TikTok)

## FORMATO VIGENTE (desde 2026-11-10): 1 carrusel al día, "El reto de Andrés", 10:30 Bogotá
Un solo carrusel diario, de alto impacto: una historia por episodios con un personaje **ficticio y avisado**
(Andrés, 47 años, reto de 90 días para volver a sentirse como el de su foto de perfil). La biblia del personaje,
sus reglas y el registro de episodios están en `tiktok/historia/andres.json`: leerlo completo antes de escribir.
Las secciones de abajo sobre franjas/series quedan como referencia del formato anterior; las reglas científicas siguen vigentes.

Estructura de cada episodio (6 láminas, `template_v2.html`, `theme` "noche", `serie` "El reto de Andrés", `ring` = día del reto / 90 en todas las láminas):
1. `cover`: `kicker` "Historia ficticia · Episodio N", título-gancho ≤7 palabras (cuando el tema sea ayuno, usar el gancho de horas: "Hora 16: lo que sintió Andrés"), subtítulo de una línea que retome la decisión del episodio anterior.
2. Escena: `chat` (`name`, `status`, `messages` [{from: them|me|note, text, time}], `caption`) o `diario` (`day` "Día N", `daySub`, `text`, `sign`). Variar entre episodios.
3. La otra escena (diario o chat) o un `point` que muestre qué hizo Andrés con la opción ganadora.
4-5. `point` con la ciencia del día (1-2 datos conservadores, ligados a lo que vive Andrés).
6. `poll`: `title` (pregunta), `a`, `b` (dos opciones razonables y seguras), `comment` "Comenta [[A]] o [[B]]", `small` "Lo que gane pasa en el episodio N+1.\nCalcula tu ventana de ayuno: link en el perfil."

Bucle de comentarios: antes de escribir el episodio N+1, leer los comentarios del episodio N con Zernio
(`comments_get_inbox_post_comments`, post_id = `zernio_post_id` del episodio, account_id `6a4179799d9472faae14cb5f`),
contar votos A/B (un voto por usuario; contar comentarios que digan claramente A o B o describan la opción). Gana la mayoría;
si hay empate o 0 votos, decide la opción más prudente y el episodio lo dice ("Empate: Andrés eligió…").
Guardar `ganador` y los votos en el episodio N, y el resumen del N+1 en `andres.json`.
Descripción del post: empieza con "Episodio N · El reto de Andrés (historia ficticia basada en situaciones reales de consulta)", resume la escena, lista ✅⚠️❌ con la ciencia, la encuesta con A y B explicadas, CTA a la calculadora y 8-10 hashtags (#elretodeandres y #dosisdeciencia siempre).


Rutina: cada día se generan 2 carruseles de 5-6 láminas (ver Ritmo), se sube a este repo y se programa en
TikTok (@ladosisdeciencia) por Zernio como **publicación directa** a las 10:30 y 19:00 (America/Bogota),
con descripción y música automática. John recibe el resumen a las ~7:45 y puede pedir cancelarlo.

## Archivos
- `tools/carrusel/template_v2.html`: **diseño vigente desde 2026-11-10** (editorial: serif Fraunces, fuentes en `tools/carrusel/fonts/`, tema `claro` crema o `noche` azul/violeta, ilustración de línea según la serie: reloj 24 h ayuno, hipnograma sueño, molécula hormonas, pulso/barras ejercicio, ondas/bacterias intestino). Se activa con `"template": "template_v2.html"` en el spec.
- `tools/carrusel/template.html`: diseño anterior (fondo oscuro, dorado, célula). Solo para specs viejos.
- `tools/carrusel/render.py`: `python3 tools/carrusel/render.py <spec.json> <carpeta>` → `01.jpg`…`06.jpg` (1080×1920). Usa la plantilla indicada en `spec.template`.
- `tiktok/AAAA-MM-DD-slug/spec.json` + láminas: un carrusel por carpeta.
- `tiktok/historial.json`: temas ya hechos. Nunca repetir uno.

## Estructura del spec
- Raíz: `slug`, `date`, `franja`, `serie`, `seed`, `template: "template_v2.html"`, `theme` (`claro` en franja A, `noche` en franja B), `slides`, `caption_title`, `description`.
- 5 o 6 láminas: `cover` → 3-4 `point` → `cta`.
- `cover`: `title` (máx. ~7 palabras; `[[palabra]]` resalta en cursiva de color), `subtitle` (una línea), `serie`, opcional `kicker` (texto de la etiqueta superior; por defecto "Serie <serie>").
- `point`: `title`, opcional `badge` + `verdict` (`no` | `si` | `gris`), opcional `big` + `bigUnit` (un dato numérico grande), `body` (máx. ~40 palabras, `**negrita**`), opcional `note` (una línea, empieza con `**Etiqueta:**`), opcional `ring` (0-1, arco de progreso para temas de horas de ayuno).
- `cta`: siempre hacia la calculadora: botón "Link en el perfil". Nunca números de teléfono.
- `caption_title`: ≤ 90 caracteres, sin hashtags.
- `description`: caption completo (≤ 4000), lista con ✅⚠️❌ o →, CTA a la calculadora, una pregunta para comentarios, 8-10 hashtags (#dosisdeciencia siempre).

## Ritmo: 2 carruseles al día (desde 2026-11-10; antes 3/día)
| Franja | Hora (Bogotá) | Series | Tema de color |
|---|---|---|---|
| A | 10:30 | Ayuno | `claro` |
| B | 19:00 | Rotan: Hormonas y metabolismo → Ejercicio y músculo → Intestino-cerebro → Sueño y cerebro (la que lleve más días sin salir según el historial) | `noche` |
Los dos del día deben ser de temas distintos entre sí (`seed` diferente). Horarios (análisis 2026-11-10 de 217 videos, vistas relativas a la mediana de su mes): 9-11 h ≈1,9× y 19 h ≈1,6× fueron las mejores franjas; 17-18 h ≈0,8× y desde las 20 h ≈0,8× las más flojas. Revisar de nuevo el 2026-11-24.

## Por qué (análisis 2026-11-10)
Con 3 carruseles/día la mediana cayó a ≈160 vistas; en agosto, con ~1 video/día, era ≈25.800. Lo que más funcionó en la cuenta: ayuno "hora por hora" (12/16/24 h) con un número en el gancho y continuidad tipo "parte 2". Priorizar portadas con número y serie ("Hora 16: …", "Parte 2").

## Temas (banco por serie; ampliar con ángulos nuevos, nunca repetir el historial)
1. **Ayuno** (88% del tráfico llega por búsqueda): qué rompe el ayuno, hora 12/16/18/24/36/48/72, cómo romperlo bien, ayuno en mujeres y ciclo menstrual, después de los 40/50, menopausia, errores comunes, ayuno y sueño, ayuno y ejercicio, ayuno y café, electrolitos, hambre y grelina, ayuno y músculo, 16:8 vs 18:6 vs OMAD, ayuno y colesterol, ayuno y piel, quién NO debe ayunar, mitos del ayuno, ayuno los fines de semana, cetosis vs autofagia.
2. **Hormonas y metabolismo**: insulina, resistencia a la insulina (señales), cortisol, leptina, grelina, GLP-1/Ozempic, tiroides, melatonina, hormona de crecimiento, testosterona y edad, estrógeno, adiponectina, glucagón, picos de glucosa, grasa visceral, hígado graso, azúcar y fructosa.
3. **Ejercicio y músculo**: caminar vs correr, zona 2, fuerza después de los 40, sarcopenia, proteína por comida, creatina (solo evidencia, sin vender producto), sedentarismo y 1 h sentado, NEAT, recuperación.
4. **Intestino-cerebro**: microbioma, serotonina intestinal, nervio vago, fibra, fermentados, ultraprocesados, inflamación intestinal, ansiedad y digestión, antibióticos y microbiota.
5. **Sueño y cerebro**: qué pasa al dormir 5 h, ciclos REM, cafeína y sueño, luz de pantallas, siestas, alcohol y sueño, memoria y sueño, dopamina y scroll, estrés crónico, BDNF.
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
  `scheduled_for` = hoy a la hora de su franja (10:30 o 19:00), `timezone`="America/Bogota".
- No usar `draft:true`: TikTok no pasa el caption a los borradores y John no los encuentra fácilmente (decisión 2026-11-03).
