import type { Guion, Palabra, Timing } from "./schema";

/** Texto que se envía a la voz: las narraciones unidas por un espacio. */
export const textoNarracion = (g: Guion) => g.escenas.map((e) => e.narracion.trim()).join(" ");

/** Rangos [inicio, fin) de caracteres de cada escena dentro de textoNarracion. */
const rangosEscenas = (g: Guion) => {
  let pos = 0;
  return g.escenas.map((e) => {
    const n = e.narracion.trim().length;
    const r = { desde: pos, hasta: pos + n };
    pos += n + 1;
    return r;
  });
};

export type Alineacion = {
  characters: string[];
  character_start_times_seconds: number[];
  character_end_times_seconds: number[];
};

/** Convierte la alineación por carácter de ElevenLabs en palabras + límites de escena. */
export const timingDesdeAlineacion = (g: Guion, al: Alineacion): Timing => {
  const chars = al.characters;
  const palabras: Palabra[] = [];
  let buf = "", ini = 0, fin = 0;
  chars.forEach((c, i) => {
    if (/\s/.test(c)) {
      if (buf) palabras.push({ texto: buf, inicio: ini, fin });
      buf = "";
      return;
    }
    if (!buf) ini = al.character_start_times_seconds[i];
    buf += c;
    fin = al.character_end_times_seconds[i];
  });
  if (buf) palabras.push({ texto: buf, inicio: ini, fin });

  const duracion = al.character_end_times_seconds[chars.length - 1] ?? 0;
  const rangos = rangosEscenas(g);
  const inicios = rangos.map((r, i) => (i === 0 ? 0 : al.character_start_times_seconds[Math.min(r.desde, chars.length - 1)]));
  const escenas = inicios.map((inicio, i) => ({ inicio, fin: i + 1 < inicios.length ? inicios[i + 1] : duracion + 0.6 }));
  return { duracion, escenas, palabras };
};

/** Timing estimado sin audio (≈2,7 palabras/s) para previsualizar el diseño. */
export const estimarTiming = (g: Guion, wps = 2.7): Timing => {
  const palabras: Palabra[] = [];
  const escenas: Timing["escenas"] = [];
  let t = 0;
  for (const e of g.escenas) {
    const inicio = t;
    for (const w of e.narracion.trim().split(/\s+/)) {
      const d = 1 / wps + (/[.?!]$/.test(w) ? 0.25 : 0);
      palabras.push({ texto: w, inicio: t, fin: t + d - 0.04 });
      t += d;
    }
    escenas.push({ inicio, fin: t });
  }
  escenas[escenas.length - 1].fin = t + 0.6;
  return { duracion: t, escenas, palabras };
};
