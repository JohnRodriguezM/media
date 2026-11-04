import { z } from "zod";

/** Visual de cada escena. El texto en pantalla es corto; la narración lleva el detalle. */
export const visualSchema = z.discriminatedUnion("tipo", [
  // Frase grande. Usa [[palabra]] para resaltarla en el color de acento.
  z.object({ tipo: z.literal("titulo"), texto: z.string().max(80), kicker: z.string().max(40).optional() }),
  // Un número protagonista con su etiqueta.
  z.object({ tipo: z.literal("dato"), valor: z.string().max(14), etiqueta: z.string().max(60) }),
  // 2-4 ítems que aparecen uno por uno.
  z.object({ tipo: z.literal("lista"), titulo: z.string().max(50).optional(), items: z.array(z.string().max(48)).min(2).max(4) }),
  // Antes / después o A vs B.
  z.object({
    tipo: z.literal("comparacion"),
    izquierda: z.object({ titulo: z.string().max(24), texto: z.string().max(60) }),
    derecha: z.object({ titulo: z.string().max(24), texto: z.string().max(60) }),
  }),
  // Línea de tiempo con 2-4 hitos.
  z.object({ tipo: z.literal("linea_tiempo"), hitos: z.array(z.object({ fecha: z.string().max(12), texto: z.string().max(40) })).min(2).max(4) }),
]);

export const escenaSchema = z.object({
  bloque: z.enum(["gancho", "contexto", "decision", "consecuencia", "aprendizaje", "cierre"]),
  narracion: z.string().min(1),
  visual: visualSchema,
});

export const guionSchema = z.object({
  id: z.string().regex(/^\d{4}-\d{2}-\d{2}-[a-z0-9-]+$/),
  pilar: z.enum(["negocios", "biografias", "tecnologia"]),
  tema: z.string(),
  pregunta_principal: z.string(),
  escenas: z.array(escenaSchema).min(5).max(10),
  caption: z.string().max(2200),
  hashtags: z.array(z.string().regex(/^#\S+$/)).min(3).max(10),
  fuentes: z.array(z.object({ afirmacion: z.string(), url: z.string().url() })),
});

export type Visual = z.infer<typeof visualSchema>;
export type Escena = z.infer<typeof escenaSchema>;
export type Guion = z.infer<typeof guionSchema>;

/** Lo que produce el paso de voz y consume Remotion. */
export type Palabra = { texto: string; inicio: number; fin: number };
export type Timing = {
  duracion: number; // segundos
  escenas: { inicio: number; fin: number }[];
  palabras: Palabra[];
};

export type VideoProps = { guion: Guion; timing: Timing; audio: string | null };
