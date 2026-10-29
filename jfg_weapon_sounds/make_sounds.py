"""The Weapon Sounds mod's sounds, synthesized from scratch (no game audio): 16-bit stereo WAV files in sounds/.

    python make_sounds.py            # writes every sound
    python make_sounds.py preview    # also a page to listen to them all (preview.html, not shipped)

Built the way modern shooters layer a gun (big-budget console shooters as the reference): each sound is
  transient  a sub-millisecond click and a bright snap: the attack you feel first;
  punch      a kick-drum layer (a sine whose pitch falls from about 220 Hz to the sub in 20 ms, saturated): the chest hit;
  body       noise through a bank of resonant filters: each weapon's own character;
  mechanics  bolts, actions and pings;
  tail       a wide stereo reverb (room or outdoors) and a slapback echo: the shot carrying away;
then mastered: parallel compression, saturation and a limiter, loud and dense.
"""
import base64
import io
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

RATE = 44100
HERE = Path(__file__).resolve().parent
OUT = HERE / 'sounds'
rng = np.random.default_rng(64)


# --- signal tools (mono arrays; stereo is (2, n)) --------------------------------------------------------------------
def n_of(seconds):
    return max(1, int(seconds * RATE))


def noise(seconds):
    return rng.uniform(-1, 1, n_of(seconds))


def env(n, attack=0.0005, decay=0.1, curve=5.0, hold=0.0):
    t = np.arange(n) / RATE
    a = np.clip(t / max(attack, 1e-6), 0, 1)
    d = np.exp(-curve * np.clip(t - attack - hold, 0, None) / max(decay, 1e-6))
    return a * d


def filt(x, kind, hz, order=2):
    w = np.array(hz, dtype=float) / (RATE / 2)
    w = np.clip(w, 1e-4, 0.99)
    b, a = signal.butter(order, w, kind)
    return signal.lfilter(b, a, x)


def low(x, hz, order=2):
    return filt(x, 'low', hz, order)


def high(x, hz, order=2):
    return filt(x, 'high', hz, order)


def band(x, lo, hi, order=2):
    return filt(x, 'band', [lo, hi], order)


def peak(x, hz, q, gain_db):
    """A resonant peak (RBJ peaking EQ)."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * hz / RATE
    alpha = np.sin(w0) / (2 * q)
    b = [1 + alpha * a_, -2 * np.cos(w0), 1 - alpha * a_]
    a = [1 + alpha / a_, -2 * np.cos(w0), 1 - alpha / a_]
    return signal.lfilter(b, a, x)


def pitch_sine(f_start, f_end, drop, seconds, phase=0.0):
    """A sine whose pitch falls from f_start to f_end, mostly within `drop` seconds (exponentially)."""
    n = n_of(seconds)
    t = np.arange(n) / RATE
    f = f_end + (f_start - f_end) * np.exp(-t / max(drop, 1e-6))
    return np.sin(2 * np.pi * np.cumsum(f) / RATE + phase)


def glide(f0, f1, seconds, wave_='sine'):
    n = n_of(seconds)
    k = np.arange(n) / n
    f = f0 * (f1 / f0) ** k
    ph = 2 * np.pi * np.cumsum(f) / RATE
    if wave_ == 'saw':
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    return np.sin(ph)


def sat(x, drive):
    return np.tanh(x * drive) / np.tanh(drive)


def mix(*parts):
    """Sum mono or stereo parts into a stereo array."""
    n = max(p.shape[-1] for p in parts)
    out = np.zeros((2, n))
    for p in parts:
        if p.ndim == 1:
            out[:, :len(p)] += p
        else:
            out[:, :p.shape[1]] += p
    return out


def delay(x, seconds):
    pad = n_of(seconds)
    if x.ndim == 1:
        return np.concatenate([np.zeros(pad), x])
    return np.concatenate([np.zeros((2, pad)), x], axis=1)


def norm(x):
    return x / (np.max(np.abs(x)) or 1.0)


# --- the layers --------------------------------------------------------------------------------------------------------
def transient(level=1.0, snap_hz=3000, snap_len=0.012):
    click = np.zeros(n_of(0.002))
    click[:3] = [1.0, -0.7, 0.3]
    click = high(click, 1500)
    snap = high(noise(snap_len), snap_hz, 4) * env(n_of(snap_len), 0.0001, snap_len * 0.6, 5)
    return mix(norm(click) * 0.8, norm(snap)).mean(axis=0) * level


def punch(level=1.0, start=230.0, end=50.0, drop=0.018, length=0.16, drive=3.0):
    k = pitch_sine(start, end, drop, length) * env(n_of(length), 0.0003, length * 0.55, 5)
    return sat(k, drive) * level


def body(level=1.0, length=0.09, lo=180, hi=4500, peaks=((900, 2.0, 9), (2200, 3.0, 6)), curve=5.0):
    b = band(noise(length), lo, hi, 2)
    for hz, q, g in peaks:
        b = peak(b, hz, q, g)
    return norm(b) * env(n_of(length), 0.0003, length * 0.6, curve) * level


def ping(hz, level=0.3, length=0.04):
    return glide(hz, hz * 0.97, length) * env(n_of(length), 0.0002, length * 0.4, 6) * level


def mechanics(level=0.4, at=0.01, pitch=1.0):
    clack = band(noise(0.012), 1500, 7000) * env(n_of(0.012), 0.0001, 0.005, 6)
    parts = mix(norm(clack), ping(3300 * pitch, 0.6), delay(ping(5200 * pitch, 0.4, 0.03), 0.003))
    return delay(parts * level, at)


def reverb(seconds, bright=5000, width=1.0, predelay=0.012):
    """A stereo impulse response: decorrelated decaying noise per side, darkened over time."""
    n = n_of(seconds)
    t = np.arange(n) / RATE
    decay = np.exp(-6.9 * t / seconds)
    sides = []
    for _ in range(2):
        nz = rng.standard_normal(n) * decay
        early = low(nz, bright)
        late = low(nz, bright * 0.35)
        blend = np.clip(t / (seconds * 0.4), 0, 1)
        sides.append(early * (1 - blend) + late * blend)
    ir = np.array(sides)
    mid = ir.mean(axis=0)
    ir = mid + (ir - mid) * width
    ir = delay(ir, predelay)
    return ir / np.sqrt(np.sum(ir ** 2) / 2)


def tail(dry, space, mix_=0.35, slap=None, slap_level=0.2):
    """dry (mono) through a space: a reverb impulse response, plus a slapback echo (seconds) if given."""
    wet = np.array([signal.fftconvolve(dry, space[0]), signal.fftconvolve(dry, space[1])])
    out = mix(dry, wet * mix_)
    if slap:
        echo = low(high(dry, 200), 3000) * slap_level
        out = mix(out, delay(np.array([echo, delay(echo, 0.007)[:len(echo)]]), slap))
    return out


def master(x, loudness=2.2, ceiling=0.97, fade=0.02, comp=0.35):
    """Parallel compression (a driven copy under the original, so the body and tail come up while the attack keeps its
    edge), light saturation, then a ceiling. loudness: how hard the parallel copy is driven."""
    x = x - x.mean(axis=1, keepdims=True)
    x = norm(x)
    squashed = sat(x, loudness * 1.5)
    x = x * (1 - comp) + squashed * comp
    x = sat(norm(x), 1.2)
    x = norm(x) * ceiling
    n = n_of(fade)
    if fade and x.shape[1] > 2 * n:
        x[:, -n:] *= np.linspace(1, 0, n)
        x[:, :n_of(0.0005)] *= np.linspace(0, 1, n_of(0.0005))
    return x


def loopable(x, xfade=0.03):
    """A stereo loop: its end crossfaded into its start."""
    n = n_of(xfade)
    head, body_ = x[:, :n], x[:, n:].copy()
    body_[:, -n:] = body_[:, -n:] * np.linspace(1, 0, n) + head * np.linspace(0, 1, n)
    return body_


ROOM = reverb(0.7, 6000, 0.9)        # an indoor space: the levels are mostly caves, bases and ships
OUTDOOR = reverb(1.6, 4000, 1.0, 0.03)
SMALL = reverb(0.35, 7000, 0.7)


def air(level=0.5, length=0.05):
    """The high sizzle after the crack: what makes a shot sound expensive on small speakers."""
    return norm(band(noise(length), 4500, 15000, 2)) * env(n_of(length), 0.0003, length * 0.5, 5) * level


def gunshot(t=1.0, p=1.0, b=1.0, m=0.0, pitch=1.0, length=0.16, sub=50.0, peaks=((900, 2.0, 9), (2200, 3.0, 6)),
            snap_hz=3000, a=0.6):
    bod = body(b, length * 0.6, 180, 9000 * pitch, peaks + ((5000 * pitch, 1.0, 6),))
    dry = mix(transient(t * 3.0, snap_hz, 0.035), air(a * t * 2.5, 0.09), punch(p, 230 * pitch, sub, 0.018, length),
              bod)
    if m:
        dry = mix(dry, mechanics(m, 0.008, pitch))
    return dry.mean(axis=0)


# --- the weapons -------------------------------------------------------------------------------------------------------
def pistol():
    # A hand cannon: a hard crack, a big chest punch, a ringing room and a slapback.
    dry = gunshot(t=1.1, p=1.2, b=0.9, m=0.25, pitch=1.0, length=0.2, sub=48, peaks=((1100, 2.5, 9), (2800, 3, 7)))
    return master(tail(dry, ROOM, 0.45, slap=0.11, slap_level=0.18), 2.4)


def rifle_round(var=1.0, level=1.0):
    return gunshot(t=1.0 * level, p=0.95 * level, b=0.85 * level, m=0.3 * level, pitch=var, length=0.12, sub=55,
                   peaks=((1300 * var, 2.5, 8), (3200 * var, 3.0, 6)), snap_hz=3500)


def machine_gun_loop():
    # An assault rifle on full auto, 12 rounds a second, looped: each round a full crack and punch, slightly varied, with
    # a dense room under the stream.
    beat = 1 / 12.0
    count = 12
    total = n_of(beat * count)
    dry = np.zeros(total + n_of(0.2))
    for i in range(count):
        r = rifle_round(rng.uniform(0.97, 1.03), rng.uniform(0.88, 1.0))
        s = n_of(i * beat + (rng.uniform(-0.0015, 0.0015) if i else 0))
        dry[s:s + len(r)] += r[:len(dry) - s]
    wet = tail(dry, ROOM, 0.4, slap=0.09, slap_level=0.12)
    out = wet[:, :total].copy()
    over = wet[:, total:]
    out[:, :over.shape[1]] += over[:, :total]  # the tails of the last rounds over the loop's start
    return master(out, 2.6, fade=0)


def pistol_light():
    # The burst's last round (and the pistol's quick shot): one rifle round with the full tail ringing out.
    return master(tail(rifle_round(1.0), ROOM, 0.5, slap=0.09, slap_level=0.15), 2.3)


def spin_down():
    # Letting go: the action cycling home, a heavy metal settle and a short ring.
    a = mechanics(1.0, 0.0, 0.9)
    thunk = punch(0.6, 180, 60, 0.01, 0.08, 2.0)
    late = delay(mix(mechanics(0.6, 0.0, 0.8)), 0.07)
    return master(tail(mix(a, thunk, late).mean(axis=0), SMALL, 0.3), 1.8, 0.75)


def missile():
    # A rocket launcher: a huge boom, the motor's roar tearing away, a long outdoor tail.
    boom = gunshot(t=0.8, p=1.5, b=1.0, pitch=0.7, length=0.4, sub=36, peaks=((500, 1.5, 8), (1600, 2, 5)))
    n = n_of(0.9)
    roar = band(noise(0.9), 150, 5000) * np.minimum(1, np.linspace(0.05, 6, n)) * env(n, 0.02, 0.6, 3)
    roar = peak(roar, 700, 1.0, 8)
    dry = mix(boom, delay(norm(roar) * 0.55, 0.02)).mean(axis=0)
    return master(tail(dry, OUTDOOR, 0.5, slap=0.16, slap_level=0.2), 2.4)


def plasma_charge():
    # Overcharging (Halo-style energy): a deep hum and a climbing electric whine with crackle, brightening as it fills
    # (about 1.4 s), then held at full.
    s = 1.6
    n = n_of(s)
    t = np.arange(n) / RATE
    grow = np.clip(t / 1.4, 0, 1) ** 0.8
    f = 70 + 330 * grow
    ph = 2 * np.pi * np.cumsum(f) / RATE
    whine = np.sin(ph) + 0.4 * np.sin(2 * ph) + 0.25 * np.sin(3.01 * ph)
    whine *= 1 + 0.15 * np.sin(2 * np.pi * (8 + 14 * grow) * t)
    hum = sat(np.sin(2 * np.pi * 55 * t) * 1.5, 2.0) * 0.6
    fizz = band(noise(s), 2000, 10000)
    fizz = low(fizz, 3000) * (1 - grow) + fizz * grow
    crackle = np.zeros(n)
    for _ in range(int(40)):
        i = int(rng.uniform(0.2, 0.99) * n)
        k = n_of(rng.uniform(0.002, 0.008))
        crackle[i:i + k] += high(rng.uniform(-1, 1, len(crackle[i:i + k])), 3000) * rng.uniform(0.3, 1) * (i / n)
    dry = norm(whine) * (0.25 + 0.75 * grow) * 0.7 + hum * (0.5 + 0.5 * grow) + norm(fizz) * grow * 0.35 + crackle * 0.4
    dry *= np.minimum(1, t / 0.04)
    return master(tail(dry, SMALL, 0.25), 1.7, 0.8)


def plasma_fire():
    # The overcharged release: a massive punch, a downward energy sweep, a burst of plasma (bright noise through
    # resonances) and a big tail.
    p = punch(1.5, 260, 34, 0.025, 0.5, 3.5)
    sweep_ = glide(1400, 90, 0.35, 'saw')
    sweep_ = low(sweep_, 3500) * env(n_of(0.35), 0.001, 0.25, 4)
    burst = body(1.0, 0.3, 300, 9000, ((700, 1.5, 9), (1900, 2.5, 7), (4200, 3, 5)), 4)
    dry = mix(transient(1.0, 2500, 0.02), p, norm(sweep_) * 0.6, burst * 0.8).mean(axis=0)
    return master(tail(dry, ROOM, 0.5, slap=0.12, slap_level=0.2), 2.5)


def shocker():
    # Live current: a thick, buzzing arc with a sub hum under it and crackles over it, looped.
    s = 1.0
    n = n_of(s)
    t = np.arange(n) / RATE
    hum = sat(np.sin(2 * np.pi * 50 * t) * 2.0, 2.5) * 0.7
    buzz = glide(100, 100, s, 'saw') + glide(151, 151, s, 'saw') * 0.6
    buzz = peak(band(buzz, 80, 6000), 1200, 2, 8) * (0.75 + 0.25 * np.sin(2 * np.pi * 6 * t))
    arcs = np.zeros(n)
    for _ in range(30):
        i = rng.integers(0, n - 2000)
        k = n_of(rng.uniform(0.003, 0.02))
        arcs[i:i + k] += high(rng.uniform(-1, 1, k), 2000) * env(k, 0.0002, k / RATE * 0.5, 5) * rng.uniform(0.3, 1)
    dry = hum + norm(buzz) * 0.5 + arcs * 0.6
    return master(loopable(tail(dry, SMALL, 0.25)[:, :n + n_of(0.03)]), 2.0, 0.85, fade=0)


def switch():
    # A weapon change: cloth, a heavy slide racking back and slamming home.
    cloth = low(noise(0.08), 2000) * env(n_of(0.08), 0.01, 0.05, 4) * 0.4
    back = mechanics(0.9, 0.03, 0.85)
    home = mix(mechanics(1.0, 0.0, 1.0), punch(0.6, 200, 70, 0.008, 0.07, 2.5))
    dry = mix(cloth, back, delay(home, 0.13)).mean(axis=0)
    return master(tail(dry, SMALL, 0.2), 1.8, 0.8)


def throw():
    # A throw: a cloth snap and a fast air whoosh.
    s = 0.28
    whoosh = band(noise(s), 250, 3500) * np.sin(np.linspace(0, np.pi, n_of(s))) ** 2
    snap = band(noise(0.02), 800, 4000) * env(n_of(0.02), 0.0003, 0.01, 6)
    return master(tail(mix(norm(snap) * 0.6, norm(whoosh)).mean(axis=0), SMALL, 0.15), 1.6, 0.7)


def zing():
    # A shuriken: a sharp metallic whistle cutting past.
    s = 0.3
    t = np.arange(n_of(s)) / RATE
    w = band(noise(s), 3500, 9000) * (0.5 + 0.5 * np.sin(2 * np.pi * 34 * t)) + glide(3400, 2600, s) * 0.3
    return master(tail(w * env(len(t), 0.01, 0.2, 4), SMALL, 0.2), 1.5, 0.5)


def mine_beep():
    # A mine armed: two clean, punchy electronic beeps.
    one = glide(1750, 1750, 0.07) * env(n_of(0.07), 0.001, 0.05, 2)
    return master(tail(mix(one, delay(one, 0.11)).mean(axis=0), SMALL, 0.2), 1.3, 0.55)


def flare():
    # A flare: a pop and a bright, hissing burn.
    pop = gunshot(t=0.6, p=0.5, b=0.4, pitch=1.4, length=0.08)
    s = 0.7
    t = np.arange(n_of(s)) / RATE
    burn = band(noise(s), 1500, 9000) * (0.7 + 0.3 * np.sin(2 * np.pi * 23 * t)) * env(len(t), 0.03, 0.5, 2) * 0.6
    return master(tail(mix(pop, burn).mean(axis=0), SMALL, 0.2), 1.6, 0.65)


SOUNDS = {
    'pistol': pistol,
    'pistol_light': pistol_light,
    'machine_gun_loop': machine_gun_loop,
    'spin_down': spin_down,
    'missile': missile,
    'plasma_charge': plasma_charge,
    'plasma_fire': plasma_fire,
    'shocker': shocker,
    'switch': switch,
    'throw': throw,
    'zing': zing,
    'mine_beep': mine_beep,
    'flare': flare,
}


def wav_bytes(x):
    if x.ndim == 1:
        x = np.array([x, x])
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((np.clip(x.T, -1, 1) * 32767).astype('<i2').tobytes())
    return buf.getvalue()


def main(args):
    OUT.mkdir(exist_ok=True)
    made = {}
    for name, make in SOUNDS.items():
        data = wav_bytes(make())
        (OUT / f'{name}.wav').write_bytes(data)
        made[name] = data
        print(f'{name}.wav  {len(data) // 1024} KB')
    if 'preview' in args:
        rows = ''.join(f'<p><b>{n}</b><br><audio controls src="data:audio/wav;base64,{base64.b64encode(d).decode()}">'
                       f'</audio></p>' for n, d in made.items())
        (HERE / 'preview.html').write_text(f'<!doctype html><meta charset="utf-8"><title>Weapon Sounds</title>'
                                           f'<body style="font-family:sans-serif">{rows}</body>', encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
