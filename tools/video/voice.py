"""Synthesize narration with Kokoro (local, offline) and compute word timings for captions.

Each beat in the spec has `say` (text for the voice, numbers written as words) and
`show` (text for the captions, numbers as digits). Timing per beat is exact (synthesized
separately); word timings inside a beat are distributed by syllable weight.

Usage (as module): synth(spec, out_wav, model_dir) -> list of beats with start/end and words.
Model files (kokoro-v1.0.onnx, voices-v1.0.bin) come from
https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.0
"""
import re
import numpy as np
import soundfile as sf

VOWELS = "aeiouáéíóúü"


def syllables(word):
    w = re.sub(r"[^a-záéíóúüñ0-9]", "", word.lower())
    if not w:
        return 1
    if w.isdigit():  # digits are spoken as words: approximate
        return {1: 2, 2: 3}.get(len(w), 4)
    groups = re.findall(r"[aeiouáéíóúü]+", w)
    return max(1, len(groups))


def synth(spec, out_wav, model_dir, voice="em_alex", speed=1.08, gap=0.28):
    from kokoro_onnx import Kokoro
    k = Kokoro(f"{model_dir}/kokoro-v1.0.onnx", f"{model_dir}/voices-v1.0.bin")
    sr = 24000
    chunks, beats, t = [], [], 0.45  # small lead-in
    chunks.append(np.zeros(int(sr * t), dtype=np.float32))
    for b in spec["beats"]:
        audio, sr = k.create(b["say"], voice=spec.get("voice", voice), speed=spec.get("speed", speed), lang="es")
        audio = audio.astype(np.float32)
        # trim leading/trailing near-silence so timings are tight
        thr = 0.01 * np.max(np.abs(audio))
        nz = np.where(np.abs(audio) > thr)[0]
        if len(nz):
            audio = audio[max(0, nz[0] - int(0.02 * sr)): nz[-1] + int(0.06 * sr)]
        dur = len(audio) / sr
        words = b["show"].split()
        weights = [syllables(w) + 0.15 for w in words]
        tot = sum(weights)
        acc, wt = t, []
        for w, wgt in zip(words, weights):
            d = dur * wgt / tot
            wt.append({"w": w, "s": round(acc, 3), "e": round(acc + d, 3)})
            acc += d
        beats.append({**b, "start": round(t, 3), "end": round(t + dur, 3), "words": wt})
        chunks.append(audio)
        pause = b.get("pause", gap)
        chunks.append(np.zeros(int(sr * pause), dtype=np.float32))
        t += dur + pause
    chunks.append(np.zeros(int(sr * 0.8), dtype=np.float32))
    full = np.concatenate(chunks)
    full = full / max(1e-6, np.max(np.abs(full))) * 0.89
    sf.write(out_wav, full, sr)
    return beats, len(full) / sr
