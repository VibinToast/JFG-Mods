"""Singularity's sounds, synthesized (no game audio), into sounds/*.wav (16-bit mono, 44.1 kHz):

    hum.wav       2.0 s, a seamless loop: a deep drone and a whoosh that passes twice a second, in time with the swirl
                  on screen (the open black hole; the mod raises its pitch as the pull goes on)
    open.wav      0.6 s: a downward suck, the black hole tearing open
    collapse.wav  1.2 s: a reversed swell into a deep boom with a violet shimmer tail

    python make_sounds.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 44100
OUT = Path(__file__).resolve().parent / "sounds"
rng = np.random.default_rng(154)


def save(name, x, peak=0.85):
    x = x / max(1e-9, np.max(np.abs(x))) * peak
    OUT.mkdir(exist_ok=True)
    with wave.open(str(OUT / name), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((x * 32767).astype("<i2").tobytes())


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = acc * a + v * (1 - a)
        y[i] = acc
    return y


def bandpass(x, lo, hi):
    return lowpass(x, hi) - lowpass(x, lo)


def hum():
    """A seamless 2 s loop: a deep drone, and a whoosh that swells and passes four times (twice a second, the swirl's
    turn on screen), its pitch sweeping, over a rushing air bed. Every part repeats a whole number of times in 2 s."""
    n = int(RATE * 2.0)
    t = np.arange(n) / RATE
    drone = np.sin(2 * np.pi * 55 * t + 1.2 * np.sin(2 * np.pi * 2 * t)) + 0.6 * np.sin(2 * np.pi * 110 * t)
    drone += 0.35 * np.sin(2 * np.pi * 165 * t + 0.8 * np.sin(2 * np.pi * 2 * t))
    pulse = np.sin(np.pi * 2 * t) ** 2                 # 0..1, peaks twice a second
    noise = rng.standard_normal(n * 2)
    whoosh_lo = bandpass(noise, 300, 900)[n:]          # the second half: the filters have settled, so it loops clean
    whoosh_hi = bandpass(noise, 900, 2600)[n:]
    whoosh = whoosh_lo * (0.3 + 0.7 * pulse) + whoosh_hi * pulse ** 2 * 0.8
    whine = 0.18 * np.sin(2 * np.pi * 440 * t + 4 * np.sin(2 * np.pi * 2 * t)) * (0.4 + 0.6 * pulse)
    x = drone * 0.55 + whoosh * 2.2 + whine
    # Join the ends: a short crossfade with the loop's start.
    fade = int(RATE * 0.05)
    w = np.linspace(0, 1, fade)
    x[-fade:] = x[-fade:] * (1 - w) + x[:fade] * w
    save("hum.wav", x, 0.95)


def open_():
    n = int(RATE * 0.6)
    t = np.arange(n) / RATE
    f = 900 * np.exp(-t * 6) + 50                     # a fast downward sweep
    ph = 2 * np.pi * np.cumsum(f) / RATE
    tone = np.sin(ph) + 0.4 * np.sin(2 * ph)
    noise = lowpass(rng.standard_normal(n), 2500) * np.exp(-t * 5)
    env = np.clip(t / 0.01, 0, 1) * np.exp(-t * 3.5)
    save("open.wav", (tone * 0.7 + noise * 0.8) * env)


def collapse():
    n = int(RATE * 1.2)
    t = np.arange(n) / RATE
    swell_end = 0.35
    rise = np.clip(t / swell_end, 0, 1) ** 3 * (t < swell_end)
    swell = lowpass(rng.standard_normal(n), 1800) * rise
    after = t >= swell_end
    tb = np.where(after, t - swell_end, 0)
    boom_f = 70 * np.exp(-tb * 3) + 35
    boom = np.sin(2 * np.pi * np.cumsum(boom_f) / RATE) * np.exp(-tb * 3.2) * after
    crack = lowpass(rng.standard_normal(n), 4000) * np.exp(-tb * 14) * after
    shimmer = np.sin(2 * np.pi * 1320 * t + 4 * np.sin(2 * np.pi * 7 * t)) * np.exp(-tb * 4) * after * 0.15
    save("collapse.wav", swell * 0.6 + boom * 1.2 + crack * 0.7 + shimmer)


hum()
open_()
collapse()
print("sounds in", OUT)
