"""Narrated motion-graphics video: Kokoro voice + word-timed captions + Three.js/motion graphics + soft music.

Usage: python3 render_motion.py <spec.json> <out.mp4> [--models DIR] [--fps 30]
Spec: {"voice": "em_alex", "speed": 1.08, "beats": [{"say": "...", "show": "...", "vis": "hook|cell|insulina|glucogeno|grasa|autofagia|desconfia|aviso|cta", "pause": 0.3}]}
Models: kokoro-v1.0.onnx + voices-v1.0.bin (https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0);
default dir $KOKORO_DIR or ~/.cache/kokoro (downloaded automatically if missing).
"""
import asyncio, json, math, os, shutil, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from voice import synth  # noqa: E402

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/"


def ensure_models(d):
    d = Path(d); d.mkdir(parents=True, exist_ok=True)
    for f in ["kokoro-v1.0.onnx", "voices-v1.0.bin"]:
        if not (d / f).exists():
            subprocess.run(["curl", "-sSL", "-o", str(d / f), MODEL_URL + f], check=True)
    return d


def music_bed(total, sr=24000):
    """Soft original ambient bed: slow chord pads + gentle pulse (Am - F - C - G)."""
    t = np.arange(int(sr * total)) / sr
    out = np.zeros_like(t)
    prog = [[57, 60, 64], [53, 57, 60], [48, 52, 55], [55, 59, 62]]
    bar = 60 / 84 * 4
    for i in range(int(total / bar) + 1):
        s, e = int(i * bar * sr), min(len(t), int((i + 1) * bar * sr))
        if s >= len(t): break
        tt = t[s:e] - t[s]
        env = np.minimum(1, tt / 0.6) * np.minimum(1, (bar - tt) / 0.6)
        for n in prog[i % 4]:
            f = 440 * 2 ** ((n - 69) / 12)
            out[s:e] += 0.05 * env * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt))
        for k in range(4):  # soft pulse on each beat
            ps = s + int(k * bar / 4 * sr)
            pe = min(e, ps + int(0.18 * sr))
            if ps < pe:
                pt = t[ps:pe] - t[ps]
                out[ps:pe] += 0.10 * np.sin(2 * np.pi * 55 * pt) * np.exp(-pt * 22)
    fade = int(sr * 1.5)
    out[-fade:] *= np.linspace(1, 0, fade)
    return out


def sfx_track(beats, total, sr=24000):
    """Original procedural sound design: sub hit on the hook, ticks while the counter runs,
    a whoosh into every new visual and a soft pop when its graphic lands."""
    out = np.zeros(int(sr * (total + 1)))
    rng = np.random.default_rng(3)

    def put(sig, at):
        i = int(at * sr)
        if i < 0 or i >= len(out):
            return
        j = min(len(out), i + len(sig)); out[i:j] += sig[: j - i]

    def whoosh(d=0.45, vol=0.22):
        n = int(sr * d); t = np.arange(n) / sr
        noise = rng.normal(0, 1, n)
        # sweep a one-pole low-pass from dark to bright and back (simple, smooth)
        cut = 0.02 + 0.35 * np.sin(np.pi * t / d) ** 2
        y = np.zeros(n); acc = 0.0
        for k in range(n):
            acc += cut[k] * (noise[k] - acc); y[k] = acc
        return vol * y / (np.max(np.abs(y)) + 1e-9) * np.sin(np.pi * t / d) ** 1.5

    def pop(f=880, d=0.09, vol=0.16):
        t = np.arange(int(sr * d)) / sr
        return vol * np.sin(2 * np.pi * f * t * (1 + 0.6 * np.exp(-t * 60))) * np.exp(-t * 38)

    def boom(d=0.9, vol=0.5):
        t = np.arange(int(sr * d)) / sr
        f = 48 + 90 * np.exp(-t * 18)
        return vol * np.sin(2 * np.pi * np.cumsum(f) / sr) * np.exp(-t * 4.5)

    def tick(vol=0.08):
        t = np.arange(int(sr * 0.03)) / sr
        return vol * np.sin(2 * np.pi * 2400 * t) * np.exp(-t * 180)

    for i, b in enumerate(beats):
        if i == 0:
            put(boom(), b["start"] - 0.05)
            if b.get("vis") in ("hook", "gancho"):
                for k in range(10):
                    put(tick(), b["start"] + 0.05 + k * 0.13)
            continue
        put(whoosh(), b["start"] - 0.42)
        if b.get("vis") not in ("texto", "cell"):
            put(pop(880 if i % 2 else 1175), b["start"] + 0.32)
    return out[: int(sr * total)]


async def _worker(p, data, outdir, fps, i0, i1):
    b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
    pg = await b.new_page(viewport={"width": 1080, "height": 1920})
    await pg.goto((HERE / "motion.html").as_uri())
    await pg.evaluate("document.fonts.load('900 40px In')")
    await pg.evaluate("document.fonts.load('800 40px Fr')")
    await pg.evaluate(f"()=>{{window.FPS={fps};window.HALF3D=true}}")
    await pg.evaluate("d=>load(d)", data)
    await pg.evaluate("document.fonts.ready")
    for i in range(i0, i1):
        await pg.evaluate("t=>renderAt(t)", i / fps)
        await pg.screenshot(path=str(outdir / f"{i:05d}.jpg"), type="jpeg", quality=90)
    await b.close()


async def frames(data, outdir, fps, workers=2):
    """Render frames with N parallel headless browsers (software WebGL is the bottleneck)."""
    n = int(math.ceil(data["total"] * fps))
    cuts = [round(n * k / workers) for k in range(workers + 1)]
    async with async_playwright() as p:
        await asyncio.gather(*[_worker(p, data, outdir, fps, cuts[k], cuts[k + 1]) for k in range(workers)])


def main(spec_path, out_path, models, fps=24):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    models = ensure_models(models)
    tmp = Path(tempfile.mkdtemp())
    voice_wav = tmp / "voice.wav"
    beats, total = synth(spec, str(voice_wav), str(models))
    data = {"beats": beats, "total": total, "scene3d": spec.get("scene3d", "cell")}
    Path(out_path).with_suffix(".timing.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    asyncio.run(frames(data, tmp, fps))
    bed = music_bed(total)
    fx = sfx_track(beats, total)
    n = min(len(bed), len(fx)); bed = bed[:n] + fx[:n]
    bed = np.clip(bed, -1, 1)
    with wave.open(str(tmp / "music.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes((bed * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "%05d.jpg"),
                    "-i", str(voice_wav), "-i", str(tmp / "music.wav"),
                    "-filter_complex", "[2:a]volume=0.7[m];[1:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out_path], check=True)
    shutil.rmtree(tmp)
    print(out_path, f"{total:.1f}s")


if __name__ == "__main__":
    a = sys.argv[1:]
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
    models = a[a.index("--models") + 1] if "--models" in a else os.environ.get("KOKORO_DIR", str(Path.home() / ".cache/kokoro"))
    main(a[0], a[1], models, fps)
