"""Floyd's Tribal alert chirp, into sounds/chirp.wav (16-bit mono WAV, 44.1 kHz): two quick robotic blips rising a
fourth, a soft square-ish tone (a sine with a little of its odd harmonics), so it reads as Floyd's voice, not a weapon.

    python make_chirp.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 44100


def blip(hz, length):
    t = np.arange(int(RATE * length)) / RATE
    tone = np.sin(2 * np.pi * hz * t) + 0.25 * np.sin(2 * np.pi * 3 * hz * t) + 0.1 * np.sin(2 * np.pi * 5 * hz * t)
    env = np.clip(t / 0.003, 0, 1) * np.exp(-t / (length * 0.45))
    return tone * env


gap = np.zeros(int(RATE * 0.025))
x = np.concatenate([blip(1760, 0.05), gap, blip(2350, 0.07), np.zeros(int(RATE * 0.02))])
x = x / np.max(np.abs(x)) * 0.8
out = Path(__file__).resolve().parent / 'sounds' / 'chirp.wav'
out.parent.mkdir(exist_ok=True)
with wave.open(str(out), 'wb') as w:
    w.setnchannels(1)
    w.setsampwidth(2)
    w.setframerate(RATE)
    w.writeframes((x * 32767).astype('<i2').tobytes())
print(out.name, f'{len(x) / RATE:.2f} s')
