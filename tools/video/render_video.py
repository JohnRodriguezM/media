"""Render a pixel-art episode spec (JSON) into a 1080x1920 MP4 with original chiptune music.

Usage: python3 render_video.py <spec.json> <out.mp4> [--fps 24]
"""
import asyncio, json, math, os, shutil, subprocess, sys, tempfile, wave
from pathlib import Path
import numpy as np
from playwright.async_api import async_playwright

HERE = Path(__file__).resolve().parent
SR = 44100


# ---------------- music: original procedural chiptune ----------------
def note_hz(n):  # MIDI note -> Hz
    return 440.0 * 2 ** ((n - 69) / 12)


def square(f, dur, duty=0.25, vol=0.18):
    t = np.arange(int(SR * dur)) / SR
    w = np.where((t * f) % 1 < duty, 1.0, -1.0) * vol
    env = np.minimum(1, np.linspace(0, 40, len(t))) * np.exp(-t * 3.2)
    return w * env


def tri(f, dur, vol=0.22):
    t = np.arange(int(SR * dur)) / SR
    w = (2 * np.abs(2 * ((t * f) % 1) - 1) - 1) * vol
    return w * np.minimum(1, np.linspace(0, 30, len(t))) * np.exp(-t * 1.2)


def noise(dur, vol=0.07, decay=40):
    t = np.arange(int(SR * dur)) / SR
    return np.random.default_rng(1).uniform(-1, 1, len(t)) * vol * np.exp(-t * decay)


def music(total, events, seed=0):
    bpm = 108
    beat = 60 / bpm
    out = np.zeros(int(SR * (total + 1)))

    def put(sig, at):
        i = int(at * SR)
        j = min(len(out), i + len(sig))
        if i < len(out):
            out[i:j] += sig[: j - i]

    # Am - F - C - G, one bar each (4 beats)
    prog = [(57, [0, 3, 7]), (53, [0, 4, 7]), (48, [0, 4, 7]), (55, [0, 4, 7])]
    rng = np.random.default_rng(seed)
    melody_shapes = [[0, 2, 1, 2, 0, 1, 2, 1], [2, 1, 0, 1, 2, 2, 1, 0], [0, 1, 2, 3, 2, 1, 0, 1]]
    bar = 0
    t = 0.0
    while t < total:
        root, chord = prog[bar % 4]
        for b in range(4):  # bass on beats, arpeggio on 8ths
            put(tri(note_hz(root - 12 + (7 if b == 2 else 0)), beat * 0.95), t + b * beat)
            put(noise(0.06, 0.05 if b % 2 else 0.09, 30 if b % 2 else 18), t + b * beat)
        shape = melody_shapes[(bar // 2) % len(melody_shapes)]
        for k in range(8):
            deg = shape[k] % 3
            octv = 12 if shape[k] >= 3 else 0
            n = root + 12 + chord[deg] + octv
            put(square(note_hz(n), beat * 0.48, duty=0.25 if bar % 8 < 4 else 0.125, vol=0.11), t + k * beat / 2)
        t += 4 * beat
        bar += 1
    # sfx
    for ev in events:
        if ev["k"] == "blip":
            put(square(note_hz(84), 0.06, 0.5, 0.12), ev["t"])
            put(square(note_hz(91), 0.06, 0.5, 0.10), ev["t"] + 0.05)
        elif ev["k"] == "quest":
            for i, n in enumerate([72, 76, 79, 84]):
                put(square(note_hz(n), 0.14, 0.5, 0.13), ev["t"] + i * 0.09)
        elif ev["k"] == "select":
            for i, n in enumerate([79, 84]):
                put(square(note_hz(n), 0.1, 0.5, 0.13), ev["t"] + i * 0.08)
    out = out[: int(SR * total)]
    fade = int(SR * 1.2)
    out[-fade:] *= np.linspace(1, 0, fade)
    out = np.tanh(out * 1.4) * 0.8
    return (out * 32767).astype(np.int16)


def indie_sfx(base, total, ev):
    """Estilo indie: música más baja + "voces" RPG (bips por personaje) y efectos."""
    pitch = {"doctora": 79, "mariana": 76, "laura": 74, "andres": 64, "raul": 60}
    out = base.astype(np.float32) / 32767 * 0.6
    def put(x, t):
        i = int(t * SR)
        if i >= len(out): return
        x = x[: len(out) - i]; out[i:i + len(x)] += x
    for e in ev:
        k = e["k"]
        if k == "voice":
            n = pitch.get(e.get("who"), 70) + [0, 2, 4, 7][int(e.get("ch", 0)) % 4]
            put(square(note_hz(n), 0.045, 0.5, 0.09), e["t"])
        elif k == "stamp":
            put(noise(0.25, 0.25, 18), e["t"]); put(square(note_hz(43), 0.18, 0.5, 0.18), e["t"])
        elif k == "cut":
            put(noise(0.08, 0.12, 60), e["t"])
        elif k == "whoosh":
            put(noise(0.35, 0.10, 8), e["t"])
        elif k == "pop":
            put(square(note_hz(88), 0.05, 0.5, 0.10), e["t"])
    return (np.tanh(out * 1.3) * 0.85 * 32767).astype(np.int16)


def sfx_events(spec):
    ev, a = [], 0.0
    for s in spec["scenes"]:
        if s["type"] == "chat":
            ev += [{"k": "blip", "t": a + m["at"]} for m in s.get("msgs", [])]
        if s["type"] == "quest":
            ev.append({"k": "quest", "t": a + 0.1})
        if s["type"] == "choice":
            ev += [{"k": "select", "t": a + 1.2}, {"k": "select", "t": a + 1.8}]
        a += s["dur"]
    return ev, a


async def frames(spec, outdir, fps):
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1080, "height": 1920})
        page = "indie.html" if spec.get("engine") == "indie" else "pixel.html"
        await pg.goto((HERE / page).as_uri())
        await pg.evaluate("document.fonts.load('40px Px')")
        await pg.evaluate("document.fonts.load('40px Sk')")
        await pg.evaluate("document.fonts.load('40px Vt')")
        total = await pg.evaluate("ep=>load(ep)", spec)
        await pg.evaluate("document.fonts.ready")
        n = int(math.ceil(total * fps))
        for i in range(n):
            await pg.evaluate("t=>renderAt(t)", i / fps)
            await pg.screenshot(path=str(outdir / f"{i:05d}.jpg"), type="jpeg", quality=90)
        events = await pg.evaluate("()=>window.EVENTS||[]")
        await b.close()
    return total, events


def main(spec_path, out_path, fps=24):
    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp())
    total, ev = asyncio.run(frames(spec, tmp, fps))
    audio = music(total, ev, spec.get("seed", 0))
    if spec.get("engine") == "indie":
        audio = indie_sfx(audio, total, ev)
    wav = tmp / "music.wav"
    with wave.open(str(wav), "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(audio.tobytes())
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps), "-i", str(tmp / "%05d.jpg"), "-i", str(wav),
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", out_path], check=True)
    # cover frame for thumbnails
    shutil.copy(tmp / f"{int(fps * 1.0):05d}.jpg", Path(out_path).with_suffix(".cover.jpg"))
    shutil.rmtree(tmp)
    print(out_path, f"{total:.1f}s")


if __name__ == "__main__":
    a = sys.argv[1:]
    fps = int(a[a.index("--fps") + 1]) if "--fps" in a else 24
    main(a[0], a[1], fps)
