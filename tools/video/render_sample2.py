"""Render del prototipo de estilo v2 (pixel2.html): python3 tools/video/render_sample2.py out.mp4"""
import asyncio, math, shutil, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright
sys.path.insert(0, str(Path(__file__).parent))
from render_video import music, square, noise, note_hz, SR

HERE = Path(__file__).parent

async def frames(outdir, fps):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        await pg.goto((HERE / "pixel2.html").as_uri())
        for f in ("Px", "Sk", "Vt"):
            await pg.evaluate(f"document.fonts.load('40px {f}')")
        total = await pg.evaluate("init()")
        await pg.evaluate("document.fonts.ready")
        for i in range(int(math.ceil(total * fps))):
            await pg.evaluate("t=>renderAt(t)", i / fps)
            await pg.screenshot(path=str(outdir / f"{i:05d}.jpg"), type="jpeg", quality=92)
        ev = await pg.evaluate("()=>window.EVENTS")
        await b.close()
    return total, ev

def mix(total, ev):
    base = music(total, [e for e in ev if e["k"] == "select"], 7).astype(np.float32) / 32767 * 0.55
    out = np.zeros(int(SR * total) + SR, np.float32)
    def put(x, t):
        i = int(t * SR); out[i:i + len(x)] += x[: max(0, len(out) - i)]
    for e in ev:
        if e["k"] == "voice":  # RPG "voice": short square blips, pitch per character + letter
            root = 79 if e["who"] == "doctora" else 64
            n = root + [0, 2, 4, 7][e["ch"] % 4]
            put(square(note_hz(n), 0.045, 0.5, 0.09), e["t"])
        elif e["k"] == "stamp":
            put(noise(0.25, 0.25, 18), e["t"]); put(square(note_hz(43), 0.18, 0.5, 0.18), e["t"])
        elif e["k"] == "cut":
            put(noise(0.08, 0.12, 60), e["t"])
        elif e["k"] == "whoosh":
            put(noise(0.35, 0.10, 8), e["t"])
    out = out[: len(base)] + base
    return (np.tanh(out * 1.3) * 0.85 * 32767).astype(np.int16)

def main(out_path, fps=24):
    tmp = Path(tempfile.mkdtemp())
    total, ev = asyncio.run(frames(tmp, fps))
    wav = tmp / "a.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix(total, ev).tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "%05d.jpg"), "-i", str(wav),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    shutil.rmtree(tmp); print(out_path, f"{total:.1f}s")

if __name__ == "__main__":
    main(sys.argv[1])
