"""Concussion Cannon's sounds, synthesized (no game audio), into sounds/*.wav (16-bit mono, 44.1 kHz):

    charge_loop.wav  2.0 s, a seamless loop: an electric whine that keeps rising (an endless Shepard glide, an octave
                     per loop, so it never jumps back) with a crackle, over a low throbbing rumble (the mod raises its
                     pitch with the charge)
    full.wav         0.5 s: a bright two-note ping with a spark, at full charge
    blast.wav        1.0 s: a crack, a deep concussive whump falling in pitch, and a rush of air with a fizz tail
    slam.wav         0.5 s: a heavy thud and a crunch of debris (an enemy hitting a wall)

    python make_sounds.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 44100
OUT = Path(__file__).resolve().parent / "sounds"
rng = np.random.default_rng(310)


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


def sweep(f):
    """Phase of a tone whose frequency follows the array f (Hz per sample)."""
    return 2 * np.pi * np.cumsum(f) / RATE


def charge_loop():
    """Every part repeats a whole number of times in 2 s. The whine: octave-spaced partials all rising an octave per
    loop under a fixed bell over log-frequency, so at the loop's end each partial stands where the next one up began;
    their start phases are chained so they also join in phase."""
    T = 2.0
    n = int(RATE * T)
    fade = int(RATE * 0.03)                                  # made this much longer, the overrun crossfaded into the start
    t = np.arange(n + fade) / RATE
    f0, centre, width = 110.0, np.log2(900.0), 0.9
    whine = np.zeros(len(t))
    phase0 = 0.0
    for k in range(7):
        f = f0 * 2 ** (k + t / T)
        ph = phase0 + 2 * np.pi * f0 * 2 ** k * T / np.log(2) * (2 ** (t / T) - 1)
        amp = np.exp(-((np.log2(f) - centre) / width) ** 2 / 2)
        whine += amp * (np.sin(ph) + 0.25 * np.sin(3 * ph))  # a little buzz
        phase0 += 2 * np.pi * f0 * 2 ** k * T / np.log(2)      # where this partial ends: the next one's start
    buzz = 0.75 + 0.25 * np.sin(2 * np.pi * 60 * t)          # a mains-like electric flutter
    rumble = np.sin(2 * np.pi * 41 * t) + 0.5 * np.sin(2 * np.pi * 82 * t + 0.6)
    rumble *= 0.7 + 0.3 * np.sin(2 * np.pi * 3 * t)           # throbbing three times a second
    m = n + fade
    noise = rng.standard_normal(m * 2)
    hiss = bandpass(noise, 2500, 7000)[m:]                   # the second half: the filters have settled
    pops = (rng.random(m) < 30 / RATE) * rng.uniform(0.5, 1, m)  # sparse crackle pops, rung through a short decay
    crackle = np.convolve(pops, np.exp(-np.arange(200) / 25.0) * np.sin(np.arange(200) * 1.3))[:m]
    x = whine * 0.55 * buzz + rumble * 0.5 + hiss * 0.5 + crackle * 0.35
    # Sample n + i follows sample n - 1 as sample i should: fade from the overrun into the start (the tones are the
    # same in both; only the noise differs), then drop the overrun.
    w = np.linspace(0, 1, fade)
    x[:fade] = x[n:] * (1 - w) + x[:fade] * w
    save("charge_loop.wav", x[:n], 0.9)


def full():
    n = int(RATE * 0.5)
    t = np.arange(n) / RATE
    second = t >= 0.07
    tone = (np.sin(2 * np.pi * 1760 * t) + 0.4 * np.sin(2 * np.pi * 3520 * t)) * np.exp(-t * 14) * ~second
    t2 = np.where(second, t - 0.07, 0)
    tone += (np.sin(2 * np.pi * 2637 * t) + 0.35 * np.sin(2 * np.pi * 5274 * t) + 0.2 * np.sin(2 * np.pi * 3951 * t)) \
        * np.exp(-t2 * 7) * second
    spark = bandpass(rng.standard_normal(n), 3000, 9000) * np.exp(-t * 60)
    env = np.clip(t / 0.002, 0, 1)
    save("full.wav", (tone + spark * 1.5) * env)


def blast():
    n = int(RATE * 1.0)
    t = np.arange(n) / RATE
    crack = bandpass(rng.standard_normal(n), 1500, 9000) * np.exp(-t * 70)
    boom = np.sin(sweep(130 * np.exp(-t * 6) + 34)) * np.clip(t / 0.004, 0, 1) * np.exp(-t * 3.5)
    sub = np.sin(sweep(55 * np.exp(-t * 2) + 25)) * np.exp(-t * 2.5)
    rush_env = np.clip(t / 0.06, 0, 1) * np.exp(-t * 3.2)
    noise = rng.standard_normal(n)
    rush = (lowpass(noise, 700) * 1.6 + bandpass(noise, 700, 2500) * 0.6) * rush_env
    fizz = bandpass(rng.standard_normal(n), 4000, 10000) * np.exp(-t * 5) * (0.6 + 0.4 * np.sin(2 * np.pi * 37 * t))
    x = boom * 1.1 + sub * 0.7 + rush * 1.2 + crack * 0.8 + fizz * 0.25
    x *= np.clip((1.0 - t) / 0.08, 0, 1)                 # fade the very end
    save("blast.wav", np.tanh(x * 1.4))                  # a little saturation for punch


def slam():
    n = int(RATE * 0.5)
    t = np.arange(n) / RATE
    thud = np.sin(sweep(95 * np.exp(-t * 18) + 42)) * np.clip(t / 0.002, 0, 1) * np.exp(-t * 11)
    knock = lowpass(rng.standard_normal(n), 900) * np.exp(-t * 35)
    grains = (rng.random(n) < 900 / RATE) * rng.standard_normal(n) * np.exp(-t * 12)  # debris clatter
    crunch = bandpass(np.convolve(grains, np.exp(-np.arange(120) / 18.0))[:n], 600, 5000)
    x = thud * 1.2 + knock * 1.0 + crunch * 2.2
    x *= np.clip((0.5 - t) / 0.05, 0, 1)
    save("slam.wav", np.tanh(x * 1.3))


charge_loop()
full()
blast()
slam()
print("sounds in", OUT)
