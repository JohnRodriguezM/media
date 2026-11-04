/**
 * Guion JSON → voz (ElevenLabs) → video (Remotion) → post en Zernio.
 *
 *   npx tsx pipeline/producir.ts guiones/<id>.json [--sin-voz] [--publicar=borrador|programar|no] [--hora=19:30]
 *
 * Variables de entorno (en GitHub van como Secrets):
 *   ELEVENLABS_API_KEY, ELEVENLABS_VOICE_ID, ELEVENLABS_MODEL (opcional)
 *   ZERNIO_API_KEY, ZERNIO_TIKTOK_ID, ZERNIO_INSTAGRAM_ID
 *   REMOTION_BROWSER (opcional: ruta a un Chrome/Chromium ya instalado)
 */
import { mkdir, readFile, writeFile, stat } from "node:fs/promises";
import path from "node:path";
import { randomUUID } from "node:crypto";
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
import { guionSchema, type Guion, type Timing, type VideoProps } from "../src/schema";
import { estimarTiming, textoNarracion, timingDesdeAlineacion, type Alineacion } from "../src/timing";

const RAIZ = path.resolve(__dirname, "..");
const OUT = path.join(RAIZ, "out");
const PUBLIC = path.join(RAIZ, "public");

const args = process.argv.slice(2);
const flag = (n: string) => args.find((a) => a.startsWith(`--${n}`))?.split("=")[1] ?? (args.includes(`--${n}`) ? "true" : undefined);
const env = (n: string) => {
  const v = process.env[n];
  if (!v) throw new Error(`Falta la variable de entorno ${n}`);
  return v;
};

async function voz(g: Guion): Promise<{ timing: Timing; audio: string | null }> {
  if (flag("sin-voz")) return { timing: estimarTiming(g), audio: null };
  const res = await fetch(`https://api.elevenlabs.io/v1/text-to-speech/${env("ELEVENLABS_VOICE_ID")}/with-timestamps`, {
    method: "POST",
    headers: { "xi-api-key": env("ELEVENLABS_API_KEY"), "Content-Type": "application/json" },
    body: JSON.stringify({
      text: textoNarracion(g),
      model_id: process.env.ELEVENLABS_MODEL || "eleven_multilingual_v2",
      language_code: "es",
    }),
  });
  if (!res.ok) throw new Error(`ElevenLabs ${res.status}: ${await res.text()}`);
  const data = (await res.json()) as { audio_base64: string; alignment: Alineacion };
  const rel = `audio/${g.id}.mp3`;
  await mkdir(path.join(PUBLIC, "audio"), { recursive: true });
  await writeFile(path.join(PUBLIC, rel), Buffer.from(data.audio_base64, "base64"));
  return { timing: timingDesdeAlineacion(g, data.alignment), audio: rel };
}

async function render(props: VideoProps, salida: string) {
  const serveUrl = await bundle({ entryPoint: path.join(RAIZ, "src/Root.tsx"), publicDir: PUBLIC });
  const browserExecutable = process.env.REMOTION_BROWSER || null;
  const composition = await selectComposition({ serveUrl, id: "Video", inputProps: props, browserExecutable });
  await renderMedia({
    composition, serveUrl, codec: "h264", crf: 20, outputLocation: salida, inputProps: props,
    browserExecutable, audioBitrate: "192k",
    onProgress: ({ progress }) => process.stdout.write(`\rRender ${Math.round(progress * 100)}%`),
  });
  process.stdout.write("\n");
}

/** Próxima ocurrencia de HH:MM en Bogotá, como fecha local sin zona (Zernio aplica `timezone`). */
function proximaHora(hhmm: string) {
  const ahora = new Date(new Date().toLocaleString("en-US", { timeZone: "America/Bogota" }));
  const [h, m] = hhmm.split(":").map(Number);
  const d = new Date(ahora);
  d.setHours(h, m, 0, 0);
  if (d <= ahora) d.setDate(d.getDate() + 1);
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}T${p(h)}:${p(m)}:00`;
}

async function publicar(g: Guion, video: string, modo: "borrador" | "programar") {
  const api = "https://zernio.com/api/v1";
  const auth = { Authorization: `Bearer ${env("ZERNIO_API_KEY")}`, "Content-Type": "application/json" };
  const size = (await stat(video)).size;

  const pre = await fetch(`${api}/media/presign`, {
    method: "POST", headers: auth,
    body: JSON.stringify({ filename: `${g.id}.mp4`, contentType: "video/mp4", size }),
  });
  if (!pre.ok) throw new Error(`Zernio presign ${pre.status}: ${await pre.text()}`);
  const { uploadUrl, publicUrl } = (await pre.json()) as { uploadUrl: string; publicUrl: string };

  const put = await fetch(uploadUrl, { method: "PUT", headers: { "Content-Type": "video/mp4" }, body: await readFile(video) });
  if (!put.ok) throw new Error(`Subida del video ${put.status}`);

  const body: Record<string, unknown> = {
    content: `${g.caption}\n\n${g.hashtags.join(" ")}`,
    mediaItems: [{ type: "video", url: publicUrl }],
    platforms: [
      { platform: "tiktok", accountId: env("ZERNIO_TIKTOK_ID") },
      { platform: "instagram", accountId: env("ZERNIO_INSTAGRAM_ID") },
    ],
    tiktokSettings: {
      privacy_level: "PUBLIC_TO_EVERYONE",
      allow_comment: true, allow_duet: true, allow_stitch: true,
      content_preview_confirmed: true, express_consent_given: true,
    },
  };
  if (modo === "borrador") body.isDraft = true;
  else { body.scheduledFor = proximaHora(flag("hora") ?? "19:30"); body.timezone = "America/Bogota"; }

  const res = await fetch(`${api}/posts`, { method: "POST", headers: { ...auth, "Idempotency-Key": randomUUID() }, body: JSON.stringify(body) });
  const txt = await res.text();
  if (!res.ok) throw new Error(`Zernio posts ${res.status}: ${txt}`);
  const post = JSON.parse(txt).post;
  console.log(`Post ${modo === "borrador" ? "en borrador" : `programado para ${body.scheduledFor} (Bogotá)`}: ${post?._id}`);
  return post?._id as string | undefined;
}

async function main() {
  const archivo = args.find((a) => !a.startsWith("--"));
  if (!archivo) throw new Error("Uso: producir.ts guiones/<id>.json");
  const guion = guionSchema.parse(JSON.parse(await readFile(path.resolve(archivo), "utf8")));
  await mkdir(OUT, { recursive: true });

  console.log(`→ ${guion.id}: voz`);
  const { timing, audio } = await voz(guion);
  await writeFile(path.join(OUT, `${guion.id}.timing.json`), JSON.stringify(timing, null, 2));
  console.log(`  ${timing.duracion.toFixed(1)} s, ${timing.palabras.length} palabras`);
  if (timing.duracion > 90) console.warn("  ⚠ más de 90 s: recorta el guion");

  console.log("→ render");
  const video = path.join(OUT, `${guion.id}.mp4`);
  await render({ guion, timing, audio }, video);

  const modo = (flag("publicar") ?? "no") as "borrador" | "programar" | "no";
  if (modo !== "no") {
    console.log(`→ Zernio (${modo})`);
    await publicar(guion, video, modo);
  }
  console.log(`✓ ${video}`);
}

main().catch((e) => { console.error(e); process.exit(1); });
