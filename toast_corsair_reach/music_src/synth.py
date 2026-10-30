"""Corsair Reach music: the shared synthesizer (numpy and scipy, our own code, no samples).

A `Song` holds notes on named buses. `render()` mixes them into one loop of exactly `bars` bars: everything that
rings past the end (notes, reverb, delay) wraps round onto the start, and every bus effect is a circular filter, so
the file loops with no seam. A one-shot (`loop=False`, the stings) gets a tail instead.

Instruments: band-limited wavetable oscillators with a time-varying low-pass (each table holds the harmonics a
24 dB/octave filter at that cutoff lets through), additive partials (bells, pans, mallets, piano), Karplus-Strong
plucks, and noise drums shaped in the frequency domain. Every random number comes from a seed made from the note,
so a run makes the same tracks byte for byte.
"""

import zlib

import numpy as np
from scipy.ndimage import minimum_filter1d, uniform_filter1d

RATE = 44100
TABLE = 2048
_GRID = np.geomspace(50.0, 18000.0, 40)  # wavetable filter cutoffs (Hz)
_LOG_GRID = np.log(_GRID)

MAJOR = (0, 2, 4, 5, 7, 9, 11)
MINOR = (0, 2, 3, 5, 7, 8, 10)
DORIAN = (0, 2, 3, 5, 7, 9, 10)
PHRYGIAN = (0, 1, 3, 5, 7, 8, 10)


def hz(midi):
    return 440.0 * 2.0 ** ((np.asarray(midi, dtype=float) - 69.0) / 12.0)


def rng_for(*key):
    return np.random.default_rng(zlib.crc32(repr(key).encode()))


# ---------------------------------------------------------------- oscillators

_tables = {}


def _harmonics(wave, k, f0):
    if wave == "saw":
        return 1.0 / k
    if wave == "square":
        return np.where(k % 2 == 1, 1.0 / k, 0.0)
    if wave == "pulse":  # 25% duty: hollow, reedy
        return np.sin(np.pi * k * 0.25) / k
    if wave == "tri":
        return np.where(k % 2 == 1, ((-1.0) ** ((k - 1) // 2)) / k ** 2, 0.0) * 1.6
    if wave == "sine":
        return np.where(k == 1, 1.0, 0.0)
    if wave.startswith("vowel_"):  # a saw through three formants: sung vowels
        formants = {"ah": ((730, 1.0, 90), (1090, 0.55, 110), (2440, 0.3, 160)),
                    "oo": ((320, 1.0, 70), (800, 0.35, 90), (2300, 0.08, 140)),
                    "eh": ((530, 1.0, 80), (1840, 0.5, 120), (2480, 0.3, 160))}[wave[6:]]
        f = k * f0
        g = 0.04 + sum(a / (1.0 + ((f - fc) / bw) ** 2) for fc, a, bw in formants)
        return g / k ** 0.6
    raise ValueError(wave)


def _table(wave, m, j, reso):
    key = (wave, m, j, reso)
    tab = _tables.get(key)
    if tab is None:
        f0 = float(hz(m))
        kmax = max(1, min(TABLE // 2 - 1, int(19000.0 / (f0 * 1.07))))
        k = np.arange(1, kmax + 1, dtype=float)
        x = k * f0 / _GRID[j]
        h = 1.0 / np.sqrt((1.0 - x ** 2) ** 2 + (x / reso) ** 2)
        amp = _harmonics(wave, k, f0) * h * h
        spec = np.zeros(TABLE // 2 + 1, dtype=complex)
        spec[1:kmax + 1] = -1j * amp * TABLE / 2
        tab = (np.fft.irfft(spec, TABLE) * 0.62).astype(np.float32)
        tab = np.append(tab, tab[0])  # guard sample for interpolation
        _tables[key] = tab
    return tab


def osc(wave, freq, n, cut, reso=0.8, phase0=0.0):
    """n samples of `wave` at `freq` (Hz, scalar or array) through a low-pass at `cut` (Hz, scalar or array)."""
    freq = np.broadcast_to(np.asarray(freq, dtype=float), (n,))
    m = int(np.ceil(69 + 12 * np.log2(max(float(freq.max()), 1.0) / 440.0)))
    ph = (phase0 + np.cumsum(freq) / RATE) % 1.0
    pos = np.interp(np.log(np.clip(np.broadcast_to(cut, (n,)), 40.0, 18000.0)), _LOG_GRID,
                    np.arange(len(_GRID), dtype=float))
    j0 = np.minimum(pos.astype(int), len(_GRID) - 2)
    w = (pos - j0).astype(np.float32)
    lo, hi = int(j0.min()), int(j0.max()) + 2
    tabs = np.stack([_table(wave, m, j, reso) for j in range(lo, hi)])
    idx = ph * TABLE
    i0 = idx.astype(int)
    fr = (idx - i0).astype(np.float32)
    jj = j0 - lo
    a = tabs[jj, i0] * (1 - fr) + tabs[jj, i0 + 1] * fr
    b = tabs[jj + 1, i0] * (1 - fr) + tabs[jj + 1, i0 + 1] * fr
    return a * (1 - w) + b * w


def band_noise(n, rng, lo=20.0, hi=20000.0, order=2):
    """White noise through a smooth band-pass (frequency domain), unit RMS."""
    spec = np.fft.rfft(rng.standard_normal(n))
    f = np.fft.rfftfreq(n, 1.0 / RATE) + 1e-3
    spec *= 1.0 / (1.0 + (lo / f) ** (2 * order)) / (1.0 + (f / hi) ** (2 * order))
    x = np.fft.irfft(spec, n)
    return (x / (np.sqrt(np.mean(x ** 2)) + 1e-12)).astype(np.float32)


def adsr(ng, n, a, d, s, r):
    """Gate `ng` samples, total `n`; `r` is the release time constant (seconds)."""
    t = np.arange(n) / RATE
    a = max(a, 0.0015)
    e = np.where(t < a, t / a, s + (1.0 - s) * np.exp(-(t - a) / max(d, 1e-3)))
    if ng < n:
        v = e[ng - 1] if ng > 0 else 0.0
        e[ng:] = v * np.exp(-(t[ng:] - t[ng]) / max(r, 1e-3))
    k = min(96, n)
    e[-k:] *= np.linspace(1.0, 0.0, k)
    return e.astype(np.float32)


def _fade_ends(x, a=0.002):
    k = min(len(x), int(a * RATE))
    x[:k] *= np.linspace(0.0, 1.0, k)
    x[-k:] *= np.linspace(1.0, 0.0, k)
    return x


# ---------------------------------------------------------------- instruments
# Each takes (f, dur, vel, rng, **params) and returns a mono float32 buffer, longer than dur by its release.

def synth(f, dur, vel, rng, wave="saw", voices=1, detune=0.0, a=0.01, d=0.3, s=0.8, r=0.1,
          cut=2000.0, kt=0.5, env=0.0, ca=0.005, cd=0.3, cs=0.0, reso=0.8,
          vib=0.0, vib_rate=5.0, vib_delay=0.3, sub=0.0, drive=0.0, breath=0.0, bend=0.0, bend_t=0.05,
          tremolo=0.0, trem_rate=5.0):
    ng = max(1, int(dur * RATE))
    n = ng + int(r * 6 * RATE) + 1
    t = np.arange(n) / RATE
    fe = np.where(t < ca, t / ca, cs + (1.0 - cs) * np.exp(-(t - ca) / cd))
    c = cut * (f / 261.6) ** kt + env * fe * (0.6 + 0.4 * vel)
    pm = vib * np.sin(2 * np.pi * vib_rate * t) * np.clip((t - vib_delay) / 0.4, 0, 1)
    if bend:
        pm = pm + bend * np.exp(-t / bend_t)
    out = np.zeros(n, dtype=np.float32)
    for v in range(voices):
        det = 0.0 if voices == 1 else detune * (2.0 * v / (voices - 1) - 1.0)
        out += osc(wave, f * 2.0 ** ((pm + det) / 12.0), n, c, reso, rng.random())
    out /= np.sqrt(voices)
    if sub:
        out += sub * np.sin(2 * np.pi * f / 2 * t + 0.3).astype(np.float32)
    if breath:
        out += breath * band_noise(n, rng, f * 0.8, f * 4.0) * 0.08
    if tremolo:
        out *= (1.0 - tremolo * 0.5 * (1 + np.sin(2 * np.pi * trem_rate * t))).astype(np.float32)
    out *= adsr(ng, n, a, d, s, r)
    if drive:
        out = np.tanh(drive * out) / np.tanh(drive)
    return (out * vel).astype(np.float32)


def partials(f, dur, vel, rng, ratios=(1,), amps=(1,), taus=(1,), a=0.002, r=0.15, damped=True,
             click=0.0, click_lo=2000.0, click_hi=9000.0, drop=0.0, beat=0.0, maxlen=9.0):
    tmax = min(maxlen, max(taus) * 5.0)
    n = int((min(tmax, dur + 6 * r) if damped else tmax) * RATE) + 1
    t = np.arange(n) / RATE
    bend = 1.0 + drop * np.exp(-t / 0.015)
    out = np.zeros(n)
    for i, (q, am, tau) in enumerate(zip(ratios, amps, taus)):
        fq = f * q
        if fq > 18000:
            continue
        ph = 2 * np.pi * np.cumsum(fq * bend) / RATE + rng.random() * 6.28
        part = np.sin(ph)
        if beat:  # two slightly detuned strings
            part = 0.5 * (part + np.sin(ph * (1.0 + beat * 1e-3 * (i + 1))))
        out += am * np.exp(-t / tau) * part
    out *= np.minimum(t / max(a, 1e-4), 1.0)
    if click:
        k = int(0.012 * RATE)
        cl = band_noise(k, rng, click_lo, click_hi) * np.exp(-np.arange(k) / (0.002 * RATE))
        out[:k] += click * cl
    if damped:
        ng = int(dur * RATE)
        if ng < n:
            out[ng:] *= np.exp(-(t[ng:] - t[ng]) / r)
    return (_fade_ends(out.astype(np.float32)) * vel).astype(np.float32)


def piano(f, dur, vel, rng, bright=1.0, tau=2.5, r=0.12):
    k = np.arange(1, 17)
    B = 0.0003
    ratios = k * np.sqrt(1 + B * k ** 2)
    amps = (1.0 / k ** (1.6 - 0.5 * vel * bright)) * np.exp(-((k * f) / (5000 * bright + 500)) ** 2)
    t1 = tau * min(1.5, (220.0 / f) ** 0.5)
    taus = t1 / (1 + 0.35 * (k - 1))
    return partials(f, dur, vel, rng, ratios, amps, taus, a=0.002, r=r, click=0.06, click_lo=800,
                    click_hi=4000, beat=0.6)


def pluck(f, dur, vel, rng, bright=0.6, t60=1.6, r=0.08, pick=0.3, body=0.0):
    """Karplus-Strong, a period at a time, then resampled to the exact pitch."""
    P = int(np.ceil(RATE / f))
    ratio = (RATE / f) / P
    n_out = int(min(t60 * 1.3, dur + 6 * r) * RATE) + 1
    n_in = int(n_out / ratio) + 2 * P + 2
    blocks = n_in // P + 1
    x = rng.uniform(-1, 1, P)
    for _ in range(int(round((1.0 - bright) * 10))):
        x = 0.5 * (x + np.roll(x, 1))
    if pick:
        x = x - np.roll(x, max(1, int(pick * P)))
    x -= x.mean()
    g = 10.0 ** (-3.0 / (t60 * f))
    sm = 0.12 + 0.38 * (1.0 - bright)
    Y = np.zeros((blocks, P))
    Y[0] = x
    last2 = 0.0
    for b in range(1, blocks):
        prev = Y[b - 1]
        sh = np.empty(P)
        sh[0] = last2
        sh[1:] = prev[:-1]
        Y[b] = g * ((1 - sm) * prev + sm * sh)
        last2 = prev[-1]
    y = Y.ravel()
    out = np.interp(np.arange(n_out) / ratio, np.arange(len(y)), y)
    t = np.arange(n_out) / RATE
    ng = int(dur * RATE)
    if ng < n_out:
        out[ng:] *= np.exp(-(t[ng:] - t[ng]) / r)
    if body:  # a soft low resonance for upright bass and guitar bodies
        out += body * np.sin(2 * np.pi * f * t) * np.exp(-t / (t60 * 0.4))
    peak = np.max(np.abs(out[: min(len(out), 4 * P)])) + 1e-9
    return (_fade_ends(out / peak * 0.8).astype(np.float32) * vel).astype(np.float32)


# drums ------------------------------------------------------------------

def _decay(n, tau):
    return np.exp(-np.arange(n) / (tau * RATE)).astype(np.float32)


def kick(f, dur, vel, rng, tune=52.0, punch=3.0, tau=0.3, click=0.35, drive=1.5):
    n = int(tau * 5 * RATE)
    t = np.arange(n) / RATE
    fr = tune * (1.0 + punch * np.exp(-t / 0.028))
    x = np.sin(2 * np.pi * np.cumsum(fr) / RATE) * np.exp(-t / tau)
    k = int(0.01 * RATE)
    x[:k] += click * band_noise(k, rng, 1500, 9000) * _decay(k, 0.002)
    x = np.tanh(drive * x) / np.tanh(drive)
    return (_fade_ends(x.astype(np.float32), 0.0005) * vel).astype(np.float32)


def snare(f, dur, vel, rng, tone=190.0, tau=0.14, snap=1.0, lo=1500.0, hi=9000.0):
    n = int(tau * 5 * RATE)
    t = np.arange(n) / RATE
    body = (np.sin(2 * np.pi * tone * t) + 0.5 * np.sin(2 * np.pi * tone * 1.73 * t)) * np.exp(-t / 0.05)
    nz = band_noise(n, rng, lo, hi) * np.exp(-t / tau) * 0.5 * snap
    return (_fade_ends((0.55 * body + nz).astype(np.float32), 0.0005) * vel).astype(np.float32)


def clap(f, dur, vel, rng):
    n = int(0.45 * RATE)
    t = np.arange(n) / RATE
    e = np.zeros(n)
    for off in (0.0, 0.011, 0.022):
        e += np.where(t >= off, np.exp(-(t - off) / 0.006), 0)
    e += np.where(t >= 0.03, 0.6 * np.exp(-(t - 0.03) / 0.08), 0)
    return (band_noise(n, rng, 900, 6000) * e * 0.5 * vel).astype(np.float32)


def hat(f, dur, vel, rng, tau=0.035, lo=7000.0, hi=17000.0):
    n = int(tau * 6 * RATE) + 64
    x = band_noise(n, rng, lo, hi) * _decay(n, tau) * 0.45
    return (_fade_ends(x, 0.0004) * vel).astype(np.float32)


def shaker(f, dur, vel, rng, tau=0.05, lo=4000.0, hi=12000.0):
    n = int((tau * 5 + 0.015) * RATE)
    t = np.arange(n) / RATE
    e = np.minimum(t / 0.012, 1.0) * np.exp(-np.maximum(t - 0.012, 0) / tau)
    return (band_noise(n, rng, lo, hi) * e * 0.35 * vel).astype(np.float32)


def tambourine(f, dur, vel, rng):
    x = shaker(f, dur, 1.0, rng, tau=0.07, lo=5000, hi=14000)
    t = np.arange(len(x)) / RATE
    jingle = sum(np.sin(2 * np.pi * fq * t + rng.random() * 6) for fq in (5230, 6870, 8190, 9610))
    x = x + 0.06 * jingle * np.exp(-t / 0.09)
    return (x * vel).astype(np.float32)


def conga(f, dur, vel, rng, tau=0.18, slap=0.3):
    n = int(tau * 5 * RATE)
    t = np.arange(n) / RATE
    fr = f * (1.0 + 0.12 * np.exp(-t / 0.02))
    x = np.sin(2 * np.pi * np.cumsum(fr) / RATE) * np.exp(-t / tau)
    x += 0.25 * np.sin(2 * np.pi * np.cumsum(fr * 1.52) / RATE) * np.exp(-t / (tau * 0.4))
    k = int(0.01 * RATE)
    x[:k] += slap * band_noise(k, rng, 900, 5000) * _decay(k, 0.002)
    return (_fade_ends(x.astype(np.float32), 0.0005) * vel * 0.8).astype(np.float32)


def tom(f, dur, vel, rng, tau=0.35, noise=0.25, drive=1.2):
    n = int(tau * 5 * RATE)
    t = np.arange(n) / RATE
    fr = f * (1.0 + 0.6 * np.exp(-t / 0.04))
    x = np.sin(2 * np.pi * np.cumsum(fr) / RATE) * np.exp(-t / tau)
    x += noise * band_noise(n, rng, 200, 3000) * np.exp(-t / 0.04)
    x = np.tanh(drive * x) / np.tanh(drive)
    return (_fade_ends(x.astype(np.float32), 0.0005) * vel).astype(np.float32)


def taiko(f, dur, vel, rng):
    x = tom(f, dur, 1.0, rng, tau=0.55, noise=0.45, drive=2.0)
    n = len(x)
    t = np.arange(n) / RATE
    x = x + 0.3 * band_noise(n, rng, 60, 600) * np.exp(-t / 0.12)
    return (x * vel).astype(np.float32)


def timpani(f, dur, vel, rng):
    return partials(f, dur, vel, rng, (1.0, 1.5, 1.99, 2.44, 2.9), (1.0, 0.5, 0.3, 0.15, 0.08),
                    (1.4, 0.9, 0.6, 0.4, 0.3), a=0.004, damped=False, click=0.25, click_lo=200, click_hi=2000,
                    maxlen=4.0)


def cymbal(f, dur, vel, rng, tau=1.3, lo=3000.0, hi=16000.0, ping=0.0):
    n = int(min(tau * 4, 7.0) * RATE)
    t = np.arange(n) / RATE
    x = band_noise(n, rng, lo, hi) * np.exp(-t / tau) * 0.3
    x += 0.4 * band_noise(n, rng, lo * 0.3, lo) * np.exp(-t / (tau * 0.3)) * 0.3
    if ping:
        x += ping * 0.1 * np.sin(2 * np.pi * 3400 * t) * np.exp(-t / 0.4)
    k = int(0.004 * RATE)
    x[:k] *= np.linspace(0.3, 1, k)
    return (_fade_ends(x.astype(np.float32)) * vel).astype(np.float32)


def wood(f, dur, vel, rng):
    n = int(0.12 * RATE)
    t = np.arange(n) / RATE
    x = np.sin(2 * np.pi * f * t) * np.exp(-t / 0.018) + 0.4 * np.sin(2 * np.pi * f * 2.7 * t) * np.exp(-t / 0.008)
    return (_fade_ends(x.astype(np.float32), 0.0003) * vel * 0.6).astype(np.float32)


def anvil(f, dur, vel, rng, tau=0.9):
    return partials(f, dur, vel, rng, (1.0, 2.756, 5.404, 8.933, 13.34), (1.0, 0.7, 0.45, 0.3, 0.15),
                    (tau, tau * 0.6, tau * 0.35, tau * 0.2, tau * 0.12), a=0.0005, damped=False,
                    click=0.5, click_lo=2000, click_hi=12000, maxlen=4.0)


def drip(f, dur, vel, rng):
    n = int(0.35 * RATE)
    t = np.arange(n) / RATE
    fr = f * (1.0 + 0.7 * (1 - np.exp(-t / 0.012)))
    x = np.sin(2 * np.pi * np.cumsum(fr) / RATE) * np.exp(-t / 0.05)
    return (_fade_ends(x.astype(np.float32), 0.0005) * vel * 0.5).astype(np.float32)


def thunder(f, dur, vel, rng, length=6.0):
    n = int(length * RATE)
    t = np.arange(n) / RATE
    roll = np.abs(band_noise(n, rng, 0.5, 6.0)) * 0.6 + 0.4
    x = band_noise(n, rng, 25, 380) * roll * np.minimum(t / 0.25, 1.0) * np.exp(-t / (length * 0.3))
    k = int(0.5 * RATE)
    x[:k] += 0.5 * band_noise(k, rng, 150, 2500) * _decay(k, 0.08)
    return (_fade_ends(x.astype(np.float32), 0.3) * vel * 0.5).astype(np.float32)


def hiss(f, dur, vel, rng, lo=2500.0, hi=11000.0, a=0.05, r=0.2):
    ng = int(dur * RATE)
    n = ng + int(r * 6 * RATE)
    return (band_noise(n, rng, lo, hi) * adsr(ng, n, a, 0.2, 0.7, r) * 0.25 * vel).astype(np.float32)


def piston(f, dur, vel, rng):
    n = int(0.28 * RATE)
    t = np.arange(n) / RATE
    e = np.minimum(t / 0.008, 1.0) * np.exp(-t / 0.06)
    x = band_noise(n, rng, 300, 3500) * e * 0.4
    x += np.sin(2 * np.pi * 70 * t) * np.exp(-t / 0.05) * 0.6
    return (_fade_ends(x.astype(np.float32)) * vel).astype(np.float32)


def swell(f, dur, vel, rng, lo=200.0, hi=6000.0):
    """Noise rising over `dur` and cut off: a riser into a downbeat."""
    n = int(dur * RATE)
    t = np.arange(n) / RATE
    x = band_noise(n, rng, lo, hi) * (t / dur) ** 2.5 * 0.3
    return (_fade_ends(x.astype(np.float32), 0.01) * vel).astype(np.float32)


INSTRUMENTS = {fn.__name__: fn for fn in (synth, partials, piano, pluck, kick, snare, clap, hat, shaker,
                                          tambourine, conga, tom, taiko, timpani, cymbal, wood, anvil, drip,
                                          thunder, hiss, piston, swell)}

# Presets: name -> (instrument, params)
PRESETS = {
    # leads
    "steelpan": ("partials", dict(ratios=(1, 2, 3, 4.02, 5.1), amps=(1, 0.55, 0.35, 0.12, 0.05),
                                  taus=(1.1, 0.55, 0.35, 0.2, 0.12), a=0.004, r=0.25, click=0.08,
                                  click_lo=1000, click_hi=5000)),
    "marimba": ("partials", dict(ratios=(1, 3.98, 9.1), amps=(1, 0.3, 0.07), taus=(0.45, 0.1, 0.035), a=0.0015,
                                 r=0.2, click=0.12, click_lo=1500, click_hi=6000)),
    "musicbox": ("partials", dict(ratios=(1, 3.0, 5.8, 9.2), amps=(1, 0.22, 0.08, 0.03),
                                  taus=(1.6, 0.4, 0.15, 0.08), a=0.001, damped=False, click=0.05)),
    "celesta": ("partials", dict(ratios=(1, 2.0, 4.0, 6.3), amps=(1, 0.35, 0.12, 0.04),
                                 taus=(1.2, 0.5, 0.2, 0.1), a=0.002, damped=False, click=0.04)),
    "bell": ("partials", dict(ratios=(0.5, 1.0, 1.19, 1.5, 2.0, 2.52, 3.0, 4.07),
                              amps=(0.45, 1.0, 0.55, 0.3, 0.45, 0.22, 0.18, 0.1),
                              taus=(6.0, 4.0, 3.0, 2.4, 2.0, 1.4, 1.1, 0.7), a=0.002, damped=False, click=0.15,
                              click_lo=800, click_hi=5000, maxlen=9.0)),
    "glassbell": ("partials", dict(ratios=(1, 2.32, 4.25, 6.63), amps=(1, 0.4, 0.15, 0.06),
                                   taus=(2.5, 1.2, 0.6, 0.3), a=0.003, damped=False)),
    "flute": ("synth", dict(wave="tri", a=0.05, d=0.3, s=0.85, r=0.12, cut=3000, kt=0.6, vib=0.12, vib_rate=5.2,
                            vib_delay=0.25, breath=0.35)),
    "whistle": ("synth", dict(wave="sine", a=0.03, d=0.2, s=0.9, r=0.08, cut=6000, kt=0, vib=0.18,
                              vib_rate=6.0, vib_delay=0.15, breath=0.25, bend=-0.6, bend_t=0.03)),
    "reed": ("synth", dict(wave="pulse", voices=2, detune=0.09, a=0.03, d=0.2, s=0.85, r=0.08, cut=1900, kt=0.4,
                           env=1200, cd=0.2, reso=0.9, tremolo=0.15, trem_rate=6.0)),
    "oboe": ("synth", dict(wave="pulse", a=0.04, d=0.25, s=0.85, r=0.1, cut=1400, kt=0.7, env=800, cd=0.25,
                           reso=1.6, vib=0.1, vib_rate=5.0, vib_delay=0.2)),
    "brass": ("synth", dict(wave="saw", voices=2, detune=0.06, a=0.04, d=0.4, s=0.8, r=0.12, cut=500, kt=0.7,
                            env=2600, ca=0.06, cd=0.35, cs=0.35, reso=0.9, vib=0.08, vib_delay=0.35)),
    "horn": ("synth", dict(wave="saw", voices=2, detune=0.05, a=0.09, d=0.5, s=0.85, r=0.2, cut=380, kt=0.6,
                           env=900, ca=0.12, cd=0.6, cs=0.4, reso=0.7, vib=0.06, vib_delay=0.4)),
    "cello": ("synth", dict(wave="saw", voices=2, detune=0.07, a=0.12, d=0.5, s=0.9, r=0.25, cut=700, kt=0.6,
                            env=500, ca=0.15, cd=0.5, cs=0.5, reso=0.9, vib=0.14, vib_rate=5.2, vib_delay=0.3)),
    "glass": ("synth", dict(wave="tri", voices=2, detune=0.04, a=0.2, d=1.0, s=0.7, r=0.6, cut=3000, kt=0.3,
                            vib=0.05, vib_rate=4.0)),
    "buzz": ("synth", dict(wave="square", voices=2, detune=0.1, a=0.005, d=0.25, s=0.7, r=0.08, cut=900, kt=0.6,
                           env=3500, cd=0.18, cs=0.2, reso=2.2, drive=2.5, vib=0.1, vib_delay=0.3)),
    # pads and choirs
    "strings": ("synth", dict(wave="saw", voices=3, detune=0.12, a=0.6, d=1.0, s=0.9, r=0.6, cut=1600, kt=0.3,
                              reso=0.7, vib=0.06, vib_rate=4.6, vib_delay=0.0)),
    "warmpad": ("synth", dict(wave="saw", voices=3, detune=0.1, a=0.4, d=1.0, s=0.85, r=0.8, cut=650, kt=0.2,
                              reso=0.8)),
    "darkpad": ("synth", dict(wave="saw", voices=3, detune=0.15, a=1.2, d=2.0, s=0.9, r=1.2, cut=380, kt=0.1,
                              reso=1.1)),
    "choir": ("synth", dict(wave="vowel_ah", voices=3, detune=0.1, a=0.5, d=1.0, s=0.9, r=0.6, cut=5000, kt=0,
                            vib=0.1, vib_rate=5.0, vib_delay=0.2)),
    "choir_oo": ("synth", dict(wave="vowel_oo", voices=3, detune=0.08, a=0.7, d=1.0, s=0.9, r=0.8, cut=3000,
                               kt=0, vib=0.08, vib_rate=4.6, vib_delay=0.2)),
    "drone": ("synth", dict(wave="saw", voices=3, detune=0.08, a=2.0, d=2.0, s=0.9, r=2.0, cut=220, kt=0.2,
                            reso=1.4)),
    # plucks and keys
    "uke": ("pluck", dict(bright=0.7, t60=0.9, r=0.06, pick=0.25)),
    "guitar": ("pluck", dict(bright=0.55, t60=2.0, r=0.1, pick=0.18, body=0.1)),
    "harp": ("pluck", dict(bright=0.5, t60=2.5, r=0.6, pick=0.5)),
    "pizz": ("pluck", dict(bright=0.35, t60=0.5, r=0.05, pick=0.4)),
    "harpsi": ("pluck", dict(bright=0.95, t60=1.6, r=0.08, pick=0.12)),
    "piano": ("piano", dict()),
    "softpiano": ("piano", dict(bright=0.5, tau=3.0)),
    # bass
    "bass_pluck": ("synth", dict(wave="saw", a=0.003, d=0.25, s=0.5, r=0.06, cut=220, kt=0.4, env=900, cd=0.12,
                                 reso=1.2, sub=0.5)),
    "bass_round": ("synth", dict(wave="tri", a=0.005, d=0.4, s=0.7, r=0.08, cut=900, kt=0, sub=0.4)),
    "upright": ("pluck", dict(bright=0.25, t60=1.4, r=0.08, pick=0.3, body=0.5)),
    "bass_dist": ("synth", dict(wave="saw", voices=2, detune=0.08, a=0.003, d=0.2, s=0.7, r=0.05, cut=300, kt=0.3,
                                env=1500, cd=0.1, reso=1.4, sub=0.6, drive=3.0)),
    "bass_sub": ("synth", dict(wave="sine", a=0.01, d=0.5, s=0.9, r=0.15, cut=2000, kt=0)),
    "chug": ("synth", dict(wave="saw", voices=2, detune=0.1, a=0.002, d=0.12, s=0.25, r=0.04, cut=900, kt=0.2,
                           env=2500, cd=0.06, reso=1.0, drive=5.0)),
    "power": ("synth", dict(wave="saw", voices=2, detune=0.12, a=0.004, d=0.6, s=0.7, r=0.15, cut=1500, kt=0.2,
                            env=2000, cd=0.3, reso=0.9, drive=4.0)),
    # drums
    "kick": ("kick", dict()), "kick_soft": ("kick", dict(tune=58, punch=2.0, tau=0.22, click=0.15, drive=1.0)),
    "kick_big": ("kick", dict(tune=46, punch=3.5, tau=0.42, click=0.45, drive=2.2)),
    "snare": ("snare", dict()), "snare_tight": ("snare", dict(tone=230, tau=0.1, snap=1.2)),
    "rim": ("wood", dict()), "brush": ("shaker", dict(tau=0.14, lo=2000, hi=9000)),
    "clap": ("clap", dict()), "hat": ("hat", dict()), "hat_open": ("hat", dict(tau=0.22)),
    "shaker": ("shaker", dict()), "tambourine": ("tambourine", dict()), "conga": ("conga", dict()),
    "bongo": ("conga", dict(tau=0.09, slap=0.4)), "tom": ("tom", dict()), "taiko": ("taiko", dict()),
    "timpani": ("timpani", dict()), "crash": ("cymbal", dict()), "ride": ("cymbal", dict(tau=0.5, ping=1.0)),
    "anvil": ("anvil", dict()), "clank": ("anvil", dict(tau=0.25)), "wood": ("wood", dict()),
    "drip": ("drip", dict()), "thunder": ("thunder", dict()), "hiss": ("hiss", dict()), "piston": ("piston", dict()),
    "swell": ("swell", dict()),
}


# ---------------------------------------------------------------- circular effects

def _freqs(L):
    return np.fft.rfftfreq(L, 1.0 / RATE) + 1e-3


def eq_mask(L, lp=None, hp=None, order=2):
    f = _freqs(L)
    m = np.ones_like(f)
    if lp:
        m /= np.sqrt(1.0 + (f / lp) ** (2 * order))
    if hp:
        m /= np.sqrt(1.0 + (hp / f) ** (2 * order))
    return m


def reverb_ir(seconds, rng, damp=0.5, predelay=0.02, length=None):
    """A stereo impulse response: decorrelated noise decaying faster in its highs, with early reflections."""
    n = int((length or seconds * 1.1) * RATE)
    t = np.arange(n) / RATE
    irs = []
    for ch in range(2):
        ir = np.zeros(n)
        for lo, hi, k in ((20, 400, 1.0), (400, 1800, 0.85), (1800, 5000, 0.85 - 0.45 * damp),
                          (5000, 16000, 0.7 - 0.5 * damp)):
            ir += band_noise(n, rng, lo, hi, 3) * np.exp(-6.9 * t / (seconds * k))
        ir *= np.minimum(t / 0.012, 1.0)
        for _ in range(8):  # early reflections
            p = int(rng.uniform(0.008, 0.07) * RATE)
            ir[p] += rng.uniform(-1, 1) * 6
        pd = int(predelay * RATE)
        ir = np.concatenate([np.zeros(pd), ir])[:n]
        irs.append(ir / np.sqrt(np.sum(ir ** 2)))
    return irs


def circ_conv(x, ir):
    L = len(x)
    return np.fft.irfft(np.fft.rfft(x) * np.fft.rfft(ir[:L], L), L)


def circ_delay(stereo, d, fb, damp=4000.0, pingpong=True):
    """A feedback delay as one circular filter: wet only."""
    L = stereo.shape[1]
    f = _freqs(L)
    z = fb * np.exp(-2j * np.pi * f * d / RATE) / np.sqrt(1.0 + (f / damp) ** 2)
    first = np.exp(-2j * np.pi * f * d / RATE) / np.sqrt(1.0 + (f / damp) ** 2)
    if pingpong:
        x = np.fft.rfft(stereo.mean(axis=0))
        yl = first * x / (1 - z * z)
        yr = first * z * x / (1 - z * z)
        return np.stack([np.fft.irfft(yl, L), np.fft.irfft(yr, L)])
    X = np.fft.rfft(stereo, axis=1)
    return np.fft.irfft(first * X / (1 - z), L, axis=1)


# ---------------------------------------------------------------- the song

class Song:
    def __init__(self, name, bpm, bars, key, scale=MAJOR, beats_per_bar=4, loop=True, tail=4.0, swing=0.0,
                 reverb=2.0, damp=0.5, loudness=-16.0, seed=0):
        self.name, self.bpm, self.bars, self.key, self.scale = name, bpm, bars, key, scale
        self.bpb, self.loop, self.swing = beats_per_bar, loop, swing
        self.reverb, self.damp, self.loudness = reverb, damp, loudness
        self.events = []
        self.buses = {}
        self.chords = []  # (start beat, beats, root degree, quality) for melody alterations
        self.duck_beats = []
        self.rng = rng_for(name, seed)
        self.length = int(round(bars * beats_per_bar * 60.0 / bpm * RATE)) + (0 if loop else int(tail * RATE))

    @property
    def beats(self):
        return self.bars * self.bpb

    def sec(self, beat):
        if self.swing:
            whole = np.floor(beat * 2) / 2
            if abs((beat * 2) % 2 - 1.0) < 1e-6:  # an off-beat eighth
                beat = whole + self.swing / 6.0
        return beat * 60.0 / self.bpm

    def bus(self, name, gain=1.0, rev=0.2, delay=None, lp=None, hp=None, width=0.0, duck=0.0, drive=0.0):
        """delay = (beats, feedback, wet)."""
        self.buses[name] = dict(gain=gain, rev=rev, delay=delay, lp=lp, hp=hp, width=width, duck=duck, drive=drive)

    # pitches -------------------------------------------------------------
    def chord_at(self, beat):
        for c in self.chords:
            if c[0] <= beat + 1e-6 < c[0] + c[1]:
                return c
        return None

    def pitch(self, deg, octave=0, root=None, quality=None, beat=None):
        """MIDI of scale degree `deg` (0 = key), with the chord's quality: 'M'/'m' force the third above `root`."""
        if beat is not None and root is None:
            c = self.chord_at(beat)
            if c:
                root, quality = c[2], c[3]
        m = self.key + 12 * octave + self.scale[deg % 7] + 12 * (deg // 7)
        if root is not None and quality in ("M", "m") and (deg - root) % 7 == 2:
            r = self.key + self.scale[root % 7] + 12 * (root // 7)
            want = 4 if quality == "M" else 3
            m += (want - (m - r) % 12 + 6) % 12 - 6
        return m

    def voicing(self, root, center, n=3, seventh=False, quality=None, add9=False):
        degs = [root, root + 2, root + 4] + ([root + 6] if seventh else []) + ([root + 8] if add9 else [])
        pcs = [self.pitch(d, 0, root, quality) for d in degs]
        best = None
        for inv in range(len(pcs)):
            notes = []
            for p in pcs[inv:] + [p + 12 for p in pcs[:inv]]:
                notes.append(p)
            mean = np.mean(notes)
            shift = 12 * round((center - mean) / 12)
            notes = [p + shift for p in notes]
            score = abs(np.mean(notes) - center)
            if best is None or score < best[0]:
                best = (score, notes)
        return best[1][:max(n, len(degs))]

    # notes ---------------------------------------------------------------
    def add(self, bus, preset, beat, beats, pitch, vel=0.8, pan=0.0, var=0, **params):
        self.events.append((bus, preset, beat, beats, pitch, vel, pan, var, params))

    def duck_at(self, beat):
        self.duck_beats.append(beat)

    def drums(self, bus, bar, patterns, bars=1, pans=None, pitches=None, vel=1.0, duck=None):
        """patterns: {preset: "x..x" grid for one bar}; X accent, x normal, o ghost."""
        levels = {"X": 1.0, "x": 0.78, "o": 0.42, "-": 0.25}
        for b in range(bars):
            for preset, grid in patterns.items():
                steps = len(grid)
                for i, ch in enumerate(grid):
                    if ch in levels:
                        beat = (bar + b) * self.bpb + i * self.bpb / steps
                        p = (pitches or {}).get(preset, 60)
                        self.add(bus, preset, beat, 0.1, p, vel * levels[ch], (pans or {}).get(preset, 0.0),
                                 var=i % 3)
                        if duck is not None and preset == duck:
                            self.duck_at(beat)

    # render --------------------------------------------------------------
    def render(self, report=False):
        L = self.length
        cache = {}
        mix = {name: np.zeros((2, L), dtype=np.float64) for name in self.buses}
        hum = rng_for(self.name, "humanize")
        for bus, preset, beat, beats, pitch, vel, pan, var, params in self.events:
            inst, base = PRESETS[preset]
            p = dict(base, **params)
            f = float(hz(pitch))
            start = self.sec(beat)
            dur = max(self.sec(beat + beats) - start, 0.5 * beats * 60.0 / self.bpm)
            key = (preset, round(f, 3), round(dur, 4), round(vel, 3), var, tuple(sorted(p.items())))
            buf = cache.get(key)
            if buf is None:
                buf = INSTRUMENTS[inst](f, dur, vel, rng_for(self.name, key), **p)
                cache[key] = buf
            s0 = int(round((start + hum.normal(0, 0.003)) * RATE))
            gl, gr = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
            self._place(mix[bus], buf, s0, gl * 1.414, gr * 1.414)
        duck_env = None
        if self.duck_beats:
            duck_env = np.zeros(L)
            imp = np.exp(-np.arange(int(0.25 * RATE)) / (0.09 * RATE)) * np.minimum(
                np.arange(int(0.25 * RATE)) / (0.004 * RATE), 1)
            for b in self.duck_beats:
                self._place_mono(duck_env, imp, int(round(self.sec(b) * RATE)))
            duck_env = np.minimum(duck_env, 1.0)
        out = np.zeros((2, L))
        rev_send = np.zeros(L)
        levels = {}
        for name, b in self.buses.items():
            x = mix[name]
            if b["lp"] or b["hp"]:
                m = eq_mask(L, b["lp"], b["hp"])
                x = np.fft.irfft(np.fft.rfft(x, axis=1) * m, L, axis=1)
            if b["drive"]:
                x = np.tanh(b["drive"] * x) / b["drive"]
            if b["width"]:
                d = int(0.013 * RATE)
                side = np.roll(x.mean(axis=0), d) * b["width"]
                x = x + np.stack([side, -side])
            if b["delay"]:
                beats, fb, wet = b["delay"]
                x = x + wet * circ_delay(x, beats * 60.0 / self.bpm * RATE, fb)
            if b["duck"] and duck_env is not None:
                x = x * (1.0 - b["duck"] * duck_env)
            x = x * b["gain"]
            levels[name] = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
            out += x
            rev_send += b["rev"] * x.mean(axis=0)
        if self.reverb:
            irs = reverb_ir(self.reverb, rng_for(self.name, "reverb"), self.damp,
                            length=min(self.reverb * 1.1, L / RATE * 0.9))
            for ch in range(2):
                out[ch] += circ_conv(rev_send, irs[ch])
        out = np.fft.irfft(np.fft.rfft(out, axis=1) * eq_mask(L, hp=28.0), L, axis=1)
        out = self._master(out)
        if not self.loop:
            fade = int(0.4 * RATE)
            out[:, -fade:] *= np.linspace(1, 0, fade) ** 2
        if report:
            print(f"  {self.name}: " + ", ".join(f"{k} {v:.1f}" for k, v in levels.items()))
        return out.astype(np.float32)

    def _place(self, dst, buf, s0, gl, gr):
        L = dst.shape[1]
        m = len(buf)
        if not self.loop:
            if s0 < 0:
                buf, s0 = buf[-s0:], 0
            m = min(len(buf), L - s0)
            if m > 0:
                dst[0, s0:s0 + m] += gl * buf[:m]
                dst[1, s0:s0 + m] += gr * buf[:m]
            return
        pos, idx = 0, s0 % L
        while pos < m:
            k = min(m - pos, L - idx)
            dst[0, idx:idx + k] += gl * buf[pos:pos + k]
            dst[1, idx:idx + k] += gr * buf[pos:pos + k]
            pos += k
            idx = 0

    def _place_mono(self, dst, buf, s0):
        L = len(dst)
        idx = (s0 + np.arange(len(buf))) % L if self.loop else np.clip(s0 + np.arange(len(buf)), 0, L - 1)
        np.add.at(dst, idx, buf)

    def _master(self, x):
        rms = np.sqrt(np.mean(x ** 2)) + 1e-12
        x = x * (10 ** (self.loudness / 20) / rms)
        ceiling = 0.80
        peak = np.max(np.abs(x), axis=0)
        g = np.minimum(1.0, ceiling / (peak + 1e-12))
        w = int(0.006 * RATE)
        mode = "wrap" if self.loop else "nearest"
        g = minimum_filter1d(g, 2 * w + 1, mode=mode)
        g = uniform_filter1d(g, w, mode=mode)
        x = x * g
        return np.clip(x, -0.89, 0.89)


# ---------------------------------------------------------------- themes and parts

def place_chords(song, bar, theme_bars, quality=None, stretch=1.0):
    """Register a theme's chords from `bar` on; `quality(root) -> 'M'/'m'/None` overrides a chord's third."""
    beat = bar * song.bpb
    out = []
    for tb in theme_bars:
        for root, beats in tb["chords"]:
            beats *= stretch
            q = quality(root) if quality else None
            song.chords.append((beat, beats, root, q))
            out.append((beat, beats, root, q))
            beat += beats
    return out


def melody(song, bus, preset, bar, theme_bars, octave=0, vel=0.8, legato=0.92, stretch=1.0, pan=0.0,
           transpose=0, accent=0.12, only=None, **params):
    """A theme's notes from `bar`; `stretch` 2 plays it at half speed; `only(i, deg, beat)` filters notes."""
    beat = bar * song.bpb
    i = 0
    for tb in theme_bars:
        for deg, beats in tb["notes"]:
            b = beats * stretch
            if deg is not None and (only is None or only(i, deg, beat)):
                v = vel * (1.0 + (accent if abs(beat % song.bpb) < 1e-6 else 0.0))
                song.add(bus, preset, beat, b * legato, song.pitch(deg + transpose, octave, beat=beat), min(v, 1.0),
                         pan, **params)
            beat += b
            i += 1
    return beat


def pads(song, bus, preset, chords, center, vel=0.5, n=3, seventh=False, pan=0.0, legato=1.0, **params):
    for beat, beats, root, q in chords:
        for p in song.voicing(root, center, n, seventh, q):
            song.add(bus, preset, beat, beats * legato, p, vel, pan, **params)


def arp(song, bus, preset, chords, center, step=0.5, pattern=(0, 1, 2, 3), vel=0.5, gate=0.9, pan=0.0,
        accent=0.15, **params):
    for beat, beats, root, q in chords:
        notes = song.voicing(root, center, 3, False, q)
        notes = notes + [notes[0] + 12, notes[1] + 12, notes[2] + 12]
        k = 0
        t = beat
        while t < beat + beats - 1e-6:
            p = notes[pattern[k % len(pattern)] % len(notes)]
            v = vel * (1 + (accent if abs(t % 1.0) < 1e-6 else 0))
            song.add(bus, preset, t, step * gate, p, min(v, 1.0), pan, **params)
            t += step
            k += 1


def bassline(song, bus, preset, chords, rhythm, octave=-2, vel=0.8, **params):
    """rhythm per chord: (offset beats, length beats, tone) with tone 0 root, 1 third, 2 fifth, 3 octave, -1 the
    fifth below; it repeats to fill each chord."""
    tones = {0: 0, 1: 2, 2: 4, 3: 7, -1: -3}
    for beat, beats, root, q in chords:
        span = max(off + ln for off, ln, _ in rhythm)
        span = max(span, 1.0)
        rep = 0.0
        while rep < beats - 1e-6:
            for off, ln, tone in rhythm:
                t = rep + off
                if t >= beats - 1e-6:
                    continue
                p = song.pitch(root + tones[tone], octave, root, q)
                song.add(bus, preset, beat + t, min(ln, beats - t), p, vel * (1.0 if off == 0 else 0.85), **params)
            rep += np.ceil(span)


def stabs(song, bus, preset, chords, center, offsets=(0.5, 1.5, 2.5, 3.5), length=0.25, vel=0.5, n=3, pan=0.0,
          **params):
    """Short chords at `offsets` within each bar of every chord (an off-beat skank by default)."""
    for beat, beats, root, q in chords:
        notes = song.voicing(root, center, n, False, q)
        for off in offsets:
            t = beat + off
            if beat <= t < beat + beats - 1e-6 or (beats >= 4 and off < beats):
                for p in notes:
                    song.add(bus, preset, t, length, p, vel, pan, **params)


def strum(song, bus, preset, chords, center, pattern="x.xx.xx.", vel=0.5, spread=0.03, gate=0.9, pan=0.0,
          **params):
    """Strummed chords on a grid (8 steps a bar by default); a down-strum goes up the strings, 'u' comes back."""
    steps = len(pattern)
    step = song.bpb / steps
    for beat, beats, root, q in chords:
        notes = song.voicing(root, center, 4, False, q)
        for i in range(int(round(beats / step))):
            ch = pattern[i % steps]
            if ch not in "xXu":
                continue
            order = notes if ch != "u" else notes[::-1]
            v = vel * (1.0 if ch == "X" else 0.8 if ch == "x" else 0.6)
            for k, p in enumerate(order):
                song.add(bus, preset, beat + i * step + k * spread, step * gate, p, v, pan, **params)
