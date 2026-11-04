import "@fontsource/archivo/500.css";
import "@fontsource/archivo/800.css";
import React from "react";
import {
  AbsoluteFill, Audio, Sequence, interpolate, spring, staticFile,
  useCurrentFrame, useVideoConfig,
} from "remotion";
import type { Escena, Palabra, Visual, VideoProps } from "./schema";

export const C = {
  bg: "#0E0E0C",
  panel: "#1A1916",
  text: "#F3EFE6",
  muted: "#9C978B",
  accent: "#F2A93B",
  line: "#2C2A25",
};
const FONT = "Archivo, sans-serif";

const BLOQUE_LABEL: Record<Escena["bloque"], string> = {
  gancho: "", contexto: "El contexto", decision: "La decisión",
  consecuencia: "Lo que pasó", aprendizaje: "La lección", cierre: "",
};

/** "Vender el doble y [[quebrar]]" → resalta lo que va entre [[ ]] */
const Resaltado: React.FC<{ texto: string }> = ({ texto }) => (
  <>
    {texto.split(/(\[\[.+?\]\])/g).map((p, i) =>
      p.startsWith("[[") ? <span key={i} style={{ color: C.accent }}>{p.slice(2, -2)}</span> : <span key={i}>{p}</span>,
    )}
  </>
);

const useEntrada = (delay = 0) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 200 }, durationInFrames: 14 });
  return { opacity: s, transform: `translateY(${interpolate(s, [0, 1], [40, 0])}px)` };
};

const VisualView: React.FC<{ v: Visual }> = ({ v }) => {
  const a = useEntrada(0);
  const { fps } = useVideoConfig();
  switch (v.tipo) {
    case "titulo":
      return (
        <div style={a}>
          {v.kicker && <div style={{ fontSize: 34, fontWeight: 500, color: C.accent, letterSpacing: 2, textTransform: "uppercase", marginBottom: 28 }}>{v.kicker}</div>}
          <div style={{ fontSize: 104, fontWeight: 800, lineHeight: 1.02, color: C.text, letterSpacing: -2 }}><Resaltado texto={v.texto} /></div>
        </div>
      );
    case "dato":
      return (
        <div style={a}>
          <div style={{ fontSize: 210, fontWeight: 800, lineHeight: 0.95, color: C.accent, letterSpacing: -6 }}>{v.valor}</div>
          <div style={{ fontSize: 50, fontWeight: 500, color: C.text, marginTop: 30, lineHeight: 1.2 }}>{v.etiqueta}</div>
        </div>
      );
    case "lista":
      return (
        <div>
          {v.titulo && <div style={{ ...a, fontSize: 40, fontWeight: 500, color: C.muted, marginBottom: 36 }}>{v.titulo}</div>}
          {v.items.map((it, i) => <ItemLista key={i} n={i} texto={it} delay={Math.round(fps * 0.55 * i)} />)}
        </div>
      );
    case "comparacion":
      return (
        <div style={{ display: "flex", flexDirection: "column", gap: 28 }}>
          <Tarjeta {...v.izquierda} delay={0} />
          <Tarjeta {...v.derecha} delay={Math.round(fps * 0.8)} acento />
        </div>
      );
    case "linea_tiempo":
      return (
        <div style={{ borderLeft: `4px solid ${C.line}`, paddingLeft: 44 }}>
          {v.hitos.map((h, i) => <Hito key={i} {...h} delay={Math.round(fps * 0.6 * i)} />)}
        </div>
      );
  }
};

const ItemLista: React.FC<{ n: number; texto: string; delay: number }> = ({ n, texto, delay }) => {
  const a = useEntrada(delay);
  return (
    <div style={{ ...a, display: "flex", alignItems: "center", gap: 30, marginBottom: 30 }}>
      <div style={{ width: 72, height: 72, borderRadius: 14, background: C.panel, border: `2px solid ${C.line}`, color: C.accent, fontSize: 38, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>{n + 1}</div>
      <div style={{ fontSize: 60, fontWeight: 800, color: C.text, lineHeight: 1.1 }}>{texto}</div>
    </div>
  );
};

const Tarjeta: React.FC<{ titulo: string; texto: string; delay: number; acento?: boolean }> = ({ titulo, texto, delay, acento }) => {
  const a = useEntrada(delay);
  return (
    <div style={{ ...a, background: C.panel, border: `2px solid ${acento ? C.accent : C.line}`, borderRadius: 24, padding: "40px 44px" }}>
      <div style={{ fontSize: 34, fontWeight: 500, color: acento ? C.accent : C.muted, textTransform: "uppercase", letterSpacing: 2 }}>{titulo}</div>
      <div style={{ fontSize: 62, fontWeight: 800, color: C.text, marginTop: 14, lineHeight: 1.08 }}>{texto}</div>
    </div>
  );
};

const Hito: React.FC<{ fecha: string; texto: string; delay: number }> = ({ fecha, texto, delay }) => {
  const a = useEntrada(delay);
  return (
    <div style={{ ...a, marginBottom: 46 }}>
      <div style={{ fontSize: 40, fontWeight: 800, color: C.accent }}>{fecha}</div>
      <div style={{ fontSize: 56, fontWeight: 800, color: C.text, lineHeight: 1.1 }}>{texto}</div>
    </div>
  );
};

/** Agrupa palabras en frases cortas (≤5 palabras o hasta un signo de puntuación). */
const agrupar = (palabras: Palabra[]) => {
  const grupos: Palabra[][] = [];
  let actual: Palabra[] = [];
  for (const p of palabras) {
    actual.push(p);
    if (actual.length >= 5 || /[.,;:?!]$/.test(p.texto)) { grupos.push(actual); actual = []; }
  }
  if (actual.length) grupos.push(actual);
  return grupos;
};

const Subtitulos: React.FC<{ palabras: Palabra[] }> = ({ palabras }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const grupos = React.useMemo(() => agrupar(palabras), [palabras]);
  const g = grupos.find((g) => t >= g[0].inicio && t < g[g.length - 1].fin + 0.15);
  if (!g) return null;
  return (
    <div style={{ position: "absolute", left: 80, right: 160, top: 1260, textAlign: "center", fontSize: 64, fontWeight: 800, lineHeight: 1.15 }}>
      {g.map((p, i) => {
        const activa = t >= p.inicio && t < p.fin + 0.05;
        return (
          <span key={i} style={{ color: activa ? C.accent : C.text, textShadow: "0 4px 18px rgba(0,0,0,0.9)" }}>
            {p.texto.replace(/[.,;:]$/, "")}{i < g.length - 1 ? " " : ""}
          </span>
        );
      })}
    </div>
  );
};

const Progreso: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  return (
    <div style={{ position: "absolute", top: 0, left: 0, height: 8, width: `${(frame / durationInFrames) * 100}%`, background: C.accent }} />
  );
};

export const Video: React.FC<VideoProps> = ({ guion, timing, audio }) => {
  const { fps } = useVideoConfig();
  return (
    <AbsoluteFill style={{ background: C.bg, fontFamily: FONT }}>
      {audio && <Audio src={audio.startsWith("http") ? audio : staticFile(audio)} />}
      {guion.escenas.map((e, i) => {
        const { inicio, fin } = timing.escenas[i];
        const from = Math.round(inicio * fps);
        const dur = Math.max(1, Math.round(fin * fps) - from);
        const label = BLOQUE_LABEL[e.bloque];
        return (
          <Sequence key={i} from={from} durationInFrames={dur}>
            <AbsoluteFill style={{ padding: "0 80px", paddingRight: 140 }}>
              {label && <div style={{ position: "absolute", top: 200, left: 80, fontSize: 32, fontWeight: 500, color: C.muted, letterSpacing: 3, textTransform: "uppercase" }}>{label}</div>}
              <div style={{ position: "absolute", top: 280, bottom: 720, left: 80, right: 140, display: "flex", flexDirection: "column", justifyContent: "center" }}>
                <VisualView v={e.visual} />
              </div>
            </AbsoluteFill>
          </Sequence>
        );
      })}
      <Subtitulos palabras={timing.palabras} />
      <Progreso />
    </AbsoluteFill>
  );
};
