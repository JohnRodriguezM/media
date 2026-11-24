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


async def frames(data, outdir, fps):
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--use-gl=swiftshader", "--enable-webgl", "--ignore-gpu-blocklist"])
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto((HERE / "motion.html").as_uri())
        await pg.evaluate("document.fonts.load('900 40px In')")
        await pg.evaluate("document.fonts.load('800 40px Fr')")
        await pg.evaluate("d=>load(d)", data)
        await pg.evaluate("document.fonts.ready")
        n = int(math.ceil(data["total"] * fps))
        for i in range(n):
            await pg.evaluate("t=>renderAt(t)", i / fps)
            await pg.screenshot(path=str(outdir / f"{i:05d}.jpg"), type="jpeg", quality=90)
        await b.close()


def main(spec_path, out_path, models, fps=30):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    models = ensure_models(models)
    tmp = Path(tempfile.mkdtemp())
    voice_wav = tmp / "voice.wav"
    beats, total = synth(spec, str(voice_wav), str(models))
    data = {"beats": beats, "total": total}
    Path(out_path).with_suffix(".timing.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    asyncio.run(frames(data, tmp, fps))
    bed = music_bed(total)
    with wave.open(str(tmp / "music.wav"), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(24000); w.writeframes((bed * 32767).astype(np.int16).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "%05d.jpg"),
                    "-i", str(voice_wav), "-i", str(tmp / "music.wav"),
                    "-filter_complex", "[2:a]volume=0.55[m];[1:a][m]amix=inputs=2:duration=first:normalize=0,loudnorm=I=-14:TP=-1.5:LRA=11[a]",
                    "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "44100", "-shortest", "-movflags", "+faststart", out_path], check=True)
    shutil.rmtree(tmp)
    print(out_path, f"{total:.1f}s")


if __name__ == "__main__":
    a = sys.argv[1:]
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 30
    models = a[a.index("--models") + 1] if "--models" in a else os.environ.get("KOKORO_DIR", str(Path.home() / ".cache/kokoro"))
    main(a[0], a[1], models, fps)
