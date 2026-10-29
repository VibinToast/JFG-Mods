"""Rolling Shellback's sounds, synthesized (no game audio), into sounds/*.wav (16-bit mono, 44.1 kHz):

    walk.wav         1.0 s, a seamless loop: two click-clack steps (each tripod of feet landing, at 0 and 0.5 s, as
                     the walk animation's gait)
    roll_loop.wav    1.5 s, a seamless loop: a rumbling roll with the plates clacking ten times a second
    bounce.wav       0.5 s: a heavy, dead impact of shell on stone: a low thump, a gritty crunch, grit, a short tail
    deflect.wav      0.6 s: a metallic ricochet ping, gliding down
    curl.wav         0.45 s: a quick run of plate clacks speeding up, ending in a snap shut
    dizzy_loop.wav   1.0 s, a seamless loop: wobbly chirping, four chirps a second
    spines.wav       0.6 s: three sharp whooshes 70 ms apart with a hiss
    hurt.wav         0.4 s: a squeal
    death.wav        1.3 s: a crunch, then a squeal fading and falling
    alert.wav        0.6 s: a rattling hiss

    python make_sounds.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 44100
OUT = Path(__file__).resolve().parent / "sounds"
rng = np.random.default_rng(159)


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


def times(T):
    return np.arange(int(RATE * T)) / RATE


def click(n, freqs, decay, noise_amt=0.6):
    """A hard tick: a few inharmonic modes rung by a noise burst, n samples long."""
    t = np.arange(n) / RATE
    x = sum(np.sin(2 * np.pi * f * t + rng.uniform(0, 6)) * a for f, a in freqs) * np.exp(-t * decay)
    x += bandpass(rng.standard_normal(n), 2000, 9000) * np.exp(-t * decay * 2.5) * noise_amt
    return x * np.clip(t / 0.0005, 0, 1)


def place(x, at, y):
    """Add y into x starting at time at (s), clipped at x's end."""
    i = int(at * RATE)
    m = min(len(y), len(x) - i)
    x[i:i + m] += y[:m]


def loop_noise(n, fn):
    """fn(noise) filtered, as a seamless loop of n samples: made long, settled, its overrun crossfaded into its start."""
    fade = int(RATE * 0.03)
    m = n + fade
    y = fn(rng.standard_normal(2 * m))[m:]
    w = np.linspace(0, 1, fade)
    y[:fade] = y[n:] * (1 - w) + y[:fade] * w
    return y[:n]


def walk():
    """Each step: three feet landing a few milliseconds apart, the first two a 'click', the third a lower 'clack'."""
    x = np.zeros(int(RATE * 1.0))
    for step, at in enumerate((0.0, 0.5)):
        for k, dt in enumerate((0.0, 0.028, 0.06)):
            hi = 1.0 + 0.08 * step - 0.18 * (k == 2)
            c = click(int(RATE * 0.08), ((2300 * hi, 1.0), (3900 * hi, 0.5), (1150 * hi, 0.6)), 75)
            place(x, at + dt, c * (0.9 if k < 2 else 1.0))
    save("walk.wav", x, 0.8)


def roll_loop():
    """Every part repeats a whole number of times in 1.5 s, so it loops."""
    T = 1.5
    n = int(RATE * T)
    t = np.arange(n) / RATE
    rumble = loop_noise(n, lambda z: lowpass(z, 160) * 3.0)
    gravel = loop_noise(n, lambda z: bandpass(z, 300, 1400))
    gravel *= 0.6 + 0.4 * np.sin(2 * np.pi * 2 * t / T * 3)        # 4 swells a second
    sub = np.sin(2 * np.pi * 40 * t) * (0.7 + 0.3 * np.sin(2 * np.pi * t / T * 3))
    clacks = np.zeros(n)
    for k in range(15):                                           # ten plate clacks a second, a little uneven
        at = k * 0.1 + rng.uniform(-0.01, 0.01) + 0.012
        c = click(int(RATE * 0.05), ((900, 1.0), (1700, 0.6), (2600, 0.3)), 90, 0.4)
        place(clacks, at, c * rng.uniform(0.5, 1.0))
    save("roll_loop.wav", np.tanh((rumble * 1.4 + gravel * 0.9 + sub * 0.5 + clacks * 0.6) * 1.2), 0.85)


def bounce():
    """A heavy, dead impact (no ringing tones, no pitch sweep): a low thump at a fixed pitch, a gritty crunch of shell
    on stone, a few bits of grit after it and a short room tail. Its own random numbers: the shared ones are drawn as
    the first bounce drew them (0.45 s), so every other sound stays as it was."""
    n_old = len(times(0.45))
    for _ in range(4):
        rng.uniform(0, 6)
    rng.standard_normal(n_old)
    rng.standard_normal(n_old)
    r = np.random.default_rng(1591)
    t = times(0.5)
    n = len(t)
    attack = np.clip(t / 0.0015, 0, 1)
    thump = (np.sin(2 * np.pi * 58 * t) * 0.8 + np.sin(2 * np.pi * 92 * t + 1.0) * 0.4) * np.exp(-t * 32)
    body = lowpass(r.standard_normal(n), 240) * np.exp(-t * 26) * 4.0
    crunch = bandpass(r.standard_normal(n), 700, 3800) * np.exp(-t * 70)
    grit = np.zeros(n)
    for _ in range(7):  # bits of grit and chitin skittering off just after
        at = r.uniform(0.012, 0.11)
        k = int(RATE * 0.012)
        tick = bandpass(r.standard_normal(k), 1500, 6000) * np.exp(-np.arange(k) / RATE * 400)
        place(grit, at, tick * r.uniform(0.15, 0.4))
    tail = lowpass(r.standard_normal(n), 900) * np.exp(-t * 9) * 0.25
    x = (thump * 1.1 + body * 1.0 + crunch * 0.8 + grit + tail) * attack
    save("bounce.wav", np.tanh(x * 1.3), 0.8)


def deflect():
    t = times(0.6)
    n = len(t)
    glide = 1.0 - 0.18 * (1 - np.exp(-t * 6))                     # the ricochet's pitch falling away
    ping = sum(np.sin(sweep(f * glide)) * a * np.exp(-t * d)
               for f, a, d in ((2450, 1.0, 7), (3870, 0.6, 9), (5630, 0.4, 12), (1720, 0.3, 6)))
    ping *= 1 + 0.25 * np.sin(2 * np.pi * 23 * t)                 # a metallic wobble
    tick = bandpass(rng.standard_normal(n), 3000, 10000) * np.exp(-t * 120)
    save("deflect.wav", (ping + tick * 1.6) * np.clip(t / 0.001, 0, 1))


def curl():
    x = np.zeros(int(RATE * 0.45))
    t = np.arange(len(x)) / RATE
    at = 0.0
    for k in range(6):                                            # the plates folding over, faster and faster
        c = click(int(RATE * 0.06), ((1400 + 120 * k, 1.0), (2300 + 150 * k, 0.6), (700, 0.4)), 80)
        place(x, at, c * (0.6 + 0.07 * k))
        at += 0.055 * 0.82 ** k
    snap = click(int(RATE * 0.15), ((520, 1.0), (1180, 0.7), (2100, 0.5)), 28, 1.0)
    place(x, at + 0.02, snap * 1.4)
    whoosh = bandpass(rng.standard_normal(len(x)), 500, 3000) * np.sin(np.pi * np.clip(t / 0.3, 0, 1)) ** 2
    save("curl.wav", x + whoosh * 0.25)


def dizzy_loop():
    """Four chirps a second, each a quick upward glide with a wobble, alternating pitch; a soft warble under them
    (whole cycles in 1 s)."""
    T = 1.0
    n = int(RATE * T)
    t = np.arange(n) / RATE
    x = np.zeros(n)
    for k in range(4):
        m = int(RATE * 0.11)
        tt = np.arange(m) / RATE
        base = (1500, 1900, 1650, 2100)[k]
        f = base * (1 + 0.45 * tt / tt[-1]) * (1 + 0.04 * np.sin(2 * np.pi * 45 * tt))
        chirp = (np.sin(sweep(f)) + 0.2 * np.sin(2 * sweep(f))) * np.sin(np.pi * tt / tt[-1]) ** 1.5
        place(x, k * 0.25 + 0.01, chirp)
    warble = np.sin(sweep(420 + 60 * np.sin(2 * np.pi * 3 * t))) * (0.5 + 0.5 * np.sin(2 * np.pi * 2 * t)) * 0.15
    save("dizzy_loop.wav", x + warble, 0.75)


def spines():
    t = times(0.6)
    n = len(t)
    x = np.zeros(n)
    for k in range(3):
        m = int(RATE * 0.28)
        tt = np.arange(m) / RATE
        z = rng.standard_normal(m)
        swish = (bandpass(z, 1500, 7000) * 1.0 + bandpass(z, 400, 1500) * 0.5)
        env = np.clip(tt / 0.006, 0, 1) * np.exp(-tt * 16)
        zip_ = np.sin(sweep(2600 * np.exp(-tt * 9) + 500)) * np.exp(-tt * 30) * 0.4   # the spine's zip
        place(x, k * 0.07, (swish * env + zip_) * (1.0 - 0.1 * k))
    hiss = bandpass(rng.standard_normal(n), 4000, 10000) * np.clip(t / 0.02, 0, 1) * np.exp(-t * 6)
    save("spines.wav", x + hiss * 0.4)


def squeal(t, f0, f1, f2, rough=0.3):
    """A squeaky voice: up from f0 to f1 quickly then down to f2, with vibrato and a buzzy edge."""
    T = t[-1]
    f = np.where(t < 0.25 * T, f0 + (f1 - f0) * t / (0.25 * T), f1 + (f2 - f1) * (t - 0.25 * T) / (0.75 * T))
    f = f * (1 + 0.035 * np.sin(2 * np.pi * 28 * t))
    ph = sweep(f)
    return np.sin(ph) + 0.45 * np.sin(2 * ph + 0.3) + 0.25 * np.sin(3 * ph) + rough * np.sign(np.sin(ph)) * 0.3


def hurt():
    t = times(0.4)
    x = squeal(t, 1100, 1900, 900) * np.clip(t / 0.01, 0, 1) * np.clip((0.4 - t) / 0.12, 0, 1)
    save("hurt.wav", bandpass(x, 300, 6000) * 2, 0.8)


def death():
    t = times(1.3)
    n = len(t)
    grains = (rng.random(n) < 1400 / RATE) * rng.standard_normal(n) * np.exp(-t * 9)
    crunch = bandpass(np.convolve(grains, np.exp(-np.arange(150) / 20.0))[:n], 500, 6000)
    crack = click(n, ((480, 1.0), (1210, 0.7), (2650, 0.5)), 22, 1.2)
    st = np.clip(t - 0.12, 0, None)
    voice = squeal(st, 1500, 1700, 380, 0.4) * np.clip(st / 0.03, 0, 1) * np.exp(-st * 1.8) * (t > 0.12)
    voice *= 1 + 0.3 * np.sin(2 * np.pi * 9 * t)                    # trembling as it fades
    x = crunch * 2.2 + crack * 1.0 + bandpass(voice, 250, 6000) * 1.4
    x *= np.clip((1.3 - t) / 0.1, 0, 1)
    save("death.wav", np.tanh(x * 1.3))


def alert():
    t = times(0.6)
    n = len(t)
    hiss = bandpass(rng.standard_normal(n), 2800, 9000)
    rattle = 0.65 + 0.35 * np.sign(np.sin(2 * np.pi * 32 * t))      # the plates rattling as it hisses
    env = np.clip(t / 0.05, 0, 1) * np.clip((0.6 - t) / 0.25, 0, 1)
    save("alert.wav", hiss * rattle * env)


for f in (walk, roll_loop, bounce, deflect, curl, dizzy_loop, spines, hurt, death, alert):
    f()
print("sounds in", OUT)
