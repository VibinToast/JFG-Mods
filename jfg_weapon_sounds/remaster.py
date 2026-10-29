"""The Weapon Sounds mod's sounds: the game's own weapon sounds (original/, from extract_originals.py) remastered to
sound modern, into sounds/ (16-bit stereo WAV, 44.1 kHz).

    python remaster.py            # writes every sound
    python remaster.py preview    # also preview.html: each original next to its remaster (not shipped)

The originals are 11-22 kHz samples: dull on top, light in the chest, dry and mono. Each goes through
  upsampling    to 44.1 kHz;
  exciter       new highs made from the sound's own upper band (saturated, then only the octave above kept);
  transient     the attack lifted against the body (an envelope follower's fast minus slow), plus a short snap;
  sub           a kick-style punch under the attack (make_sounds.punch), tuned per weapon;
  EQ            low shelf, the boxy 300-500 Hz scooped, presence and air;
  space         a stereo room and a slapback, for width and tail;
  master        parallel compression and a ceiling (make_sounds.master).
Loops (the machine gun's one round, the shocker) are tiled into a longer loop first, so each repeat gets the same
treatment and the result still loops cleanly.
"""
import base64
import io
import sys
import wave
from pathlib import Path

import numpy as np
from scipy import signal

import make_sounds as ms

RATE = ms.RATE
HERE = Path(__file__).resolve().parent
SRC = HERE / 'original'
OUT = HERE / 'sounds'


def load(name):
    with wave.open(str(SRC / f'{name}.wav'), 'rb') as w:
        rate = w.getframerate()
        x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(float) / 32768
        if w.getnchannels() == 2:
            x = x.reshape(-1, 2).mean(axis=1)
    n = int(round(len(x) * RATE / rate))
    return signal.resample_poly(x, RATE, rate)[:n] if n else x


def shelf(x, hz, gain_db, kind='low'):
    """RBJ shelving EQ."""
    a_ = 10 ** (gain_db / 40)
    w0 = 2 * np.pi * hz / RATE
    alpha = np.sin(w0) / 2 * np.sqrt(2)
    c = np.cos(w0)
    s = 2 * np.sqrt(a_) * alpha
    if kind == 'low':
        b = [a_ * ((a_ + 1) - (a_ - 1) * c + s), 2 * a_ * ((a_ - 1) - (a_ + 1) * c), a_ * ((a_ + 1) - (a_ - 1) * c - s)]
        a = [(a_ + 1) + (a_ - 1) * c + s, -2 * ((a_ - 1) + (a_ + 1) * c), (a_ + 1) + (a_ - 1) * c - s]
    else:
        b = [a_ * ((a_ + 1) + (a_ - 1) * c + s), -2 * a_ * ((a_ - 1) + (a_ + 1) * c), a_ * ((a_ + 1) + (a_ - 1) * c - s)]
        a = [(a_ + 1) - (a_ - 1) * c + s, 2 * ((a_ - 1) - (a_ + 1) * c), (a_ + 1) - (a_ - 1) * c - s]
    return signal.lfilter(b, a, x)


def follower(x, ms_):
    """An amplitude envelope with the given smoothing (milliseconds)."""
    k = max(1, int(RATE * ms_ / 1000))
    return signal.lfilter([1.0 / k], [1, -(1 - 1.0 / k)], np.abs(x))


def exciter(x, top, amount):
    """New highs above `top` Hz (the original's ceiling): its upper band, saturated, high-passed above top."""
    upper = ms.high(x, top * 0.5, 2)
    harm = np.tanh(upper * 6.0)
    return ms.high(harm, top * 0.95, 4) * amount


def transient_shape(x, amount):
    """The attack lifted: gain follows where a fast envelope runs ahead of a slow one."""
    fast, slow = follower(x, 1.0), follower(x, 25.0)
    boost = np.clip((fast - slow) / (np.max(fast) or 1.0), 0, None)
    return x * (1.0 + amount * boost / (np.max(boost) or 1.0))


def onsets(x, threshold=0.35, gap=0.05):
    """Where the hits start: rises of the fast envelope past a share of its peak, at least gap seconds apart."""
    env = follower(x, 2.0)
    env /= np.max(env) or 1.0
    hits, last = [], -10 ** 9
    for i in range(1, len(env)):
        if env[i] >= threshold > env[i - 1] and i - last > gap * RATE:
            hits.append(i)
            last = i
    return hits or [0]


def remaster(x, top, sub=None, snap=0.6, air=0.5, excite=0.6, attack=1.5, low_db=4.0, mud_db=-4.0, presence_db=4.0,
             space=ms.ROOM, wet=0.3, slap=0.1, loudness=2.2, hits=None):
    """sub: (level, start Hz, end Hz, length s) of the punch under each hit, or None."""
    y = x / (np.max(np.abs(x)) or 1.0)
    y = y + exciter(y, top, excite)
    y = transient_shape(y, attack)
    layers = []
    for at in hits if hits is not None else onsets(y):
        parts = []
        if sub:
            level, f0, f1, length = sub
            parts.append(ms.punch(level, f0, f1, 0.018, length, 2.5))
        if snap:
            parts.append(ms.transient(snap * 1.5, 3500, 0.025))
        if air:
            parts.append(ms.air(air, 0.07))
        if parts:
            layers.append(ms.delay(ms.mix(*parts).mean(axis=0), at / RATE))
    y = ms.mix(y, *layers).mean(axis=0) if layers else y
    y = shelf(y, 90, low_db, 'low')
    y = ms.peak(y, 400, 1.2, mud_db)
    y = ms.peak(y, 3000, 1.0, presence_db)
    y = shelf(y, 9000, 3.0, 'high')
    out = ms.tail(y, space, wet, slap=slap, slap_level=0.15) if space is not None else ms.mix(y)
    return ms.master(out, loudness)


def tiled(x, times):
    return np.tile(x, times)


def middle_loop(stereo, period_n):
    """A seamless loop from a processed run of three: the middle one, where the filters, the room and the slapback
    are already in their steady state, so its end runs exactly into its start."""
    seg = stereo[:, period_n:2 * period_n].copy()
    return seg / (np.max(np.abs(seg)) or 1.0) * 0.97


def as_loop(stereo, period_n):
    """A processed tiled loop folded back to an exact multiple of the period, its tail wrapped over its start."""
    total = (stereo.shape[1] // period_n) * period_n
    total = min(total, stereo.shape[1])
    out = stereo[:, :total].copy()
    over = stereo[:, total:]
    out[:, :over.shape[1]] += over[:, :total]
    return out / (np.max(np.abs(out)) or 1.0) * 0.97


# --- per weapon --------------------------------------------------------------------------------------------------------
def first_hit(x):
    return [onsets(x)[0]]


def pistol():
    # One hit only (the original's own echo tail read as more hits and stuttered), and no slapback: the room is enough.
    # Pitched up a little (1.08x) for a lighter crack.
    x = signal.resample_poly(load('pistol'), 25, 27)
    return remaster(x, 10000, sub=(1.0, 250, 55, 0.18), snap=0.8, air=0.6, wet=0.35, slap=None, hits=first_hit(x))


def sniper():
    # The sniper rifle (the pistol's sound in the game, told apart by the weapon in hand): the shot pitched down for
    # weight, a deeper and longer sub, then a big space - a long reverb and an echo coming back off the far walls.
    x = load('pistol')
    x = signal.resample_poly(x, 5, 4)  # played at the same rate: 0.8x the pitch, a quarter longer
    dry = remaster(x, 9000, sub=(1.5, 200, 38, 0.35), snap=1.0, air=0.7, low_db=6, space=None, hits=first_hit(x),
                   loudness=2.4).mean(axis=0)
    hall = ms.reverb(2.6, 4500, 1.0, 0.02)
    out = ms.tail(dry, hall, 0.3, slap=0.28, slap_level=0.25)
    return ms.master(out, 1.4, 0.97, fade=0.3, comp=0.2)


def pistol_light():
    # The machine gun's last round when you let go (and the pistol's quick shot): kept light, a soft sub.
    x = load('pistol_light')
    return remaster(x, 7500, sub=(0.45, 220, 70, 0.1), snap=0.5, air=0.5, low_db=0.0, wet=0.3, slap=None,
                    hits=first_hit(x), loudness=1.6)


def machine_gun_loop():
    # The game loops one round (0.08 s): twelve of them, each round treated, folded back into a seamless loop.
    one = load('machine_gun_loop')
    count = 12
    x = tiled(one, count * 3)
    hits = [i * len(one) for i in range(count * 3)]
    y = remaster(x, 10000, sub=(0.9, 240, 55, 0.11), snap=0.7, air=0.7, excite=0.8, attack=2.0, wet=0.3, slap=0.09,
                 hits=hits, loudness=2.6)
    return middle_loop(y, len(one) * count)


def spin_down():
    # The machine gun settling after you let go: softened, no added low end.
    x = load('spin_down')
    return remaster(x, 7500, sub=None, snap=0.2, air=0.3, low_db=-2.0, mud_db=-5.0, wet=0.25, slap=None,
                    hits=first_hit(x), loudness=1.4)


def missile():
    return remaster(load('missile'), 8000, sub=(1.4, 200, 36, 0.4), snap=0.6, air=0.5, low_db=6, space=ms.OUTDOOR,
                    wet=0.45, slap=0.16, hits=[onsets(load('missile'))[0]])


def plasma_charge():
    x = load('plasma_charge')
    return remaster(x, 8000, sub=None, snap=0, air=0, excite=0.7, attack=0.3, low_db=5, wet=0.2, slap=None, hits=[])


def plasma_fire():
    x = load('plasma_fire')
    return remaster(x, 9500, sub=(1.5, 260, 34, 0.45), snap=0.8, air=0.5, low_db=6, wet=0.45, slap=0.12,
                    hits=[onsets(x)[0]])


def shocker():
    # Bassier: a strong low shelf and a saturated sub hum under the current, the whole loop.
    one = load('shocker')
    times = max(1, int(round(1.4 / (len(one) / RATE))))
    x = tiled(one, times * 3)
    t = np.arange(len(x)) / RATE
    period = len(one) * times / RATE  # the hum and its wobble fit the loop in whole cycles, so it loops cleanly
    f_hum, f_wob = round(50 * period) / period, max(1, round(6 * period)) / period
    hum = ms.sat(np.sin(2 * np.pi * f_hum * t) * 2.0 + np.sin(2 * np.pi * 2 * f_hum * t) * 0.5, 2.0)
    hum *= 0.85 + 0.15 * np.sin(2 * np.pi * f_wob * t)
    x = x / (np.max(np.abs(x)) or 1.0) + hum * 0.55
    y = remaster(x, 10000, sub=None, snap=0, air=0, excite=0.6, attack=0.5, low_db=9, mud_db=-3, wet=0.2, slap=None,
                 hits=[])
    return middle_loop(y, len(one) * times)


def switch():
    # Changing weapons: the game's own click, freshened but kept light so it doesn't pull attention - rebuilt highs, a
    # small tap of weight under it, a tight dry room. The silence before it is trimmed so it lands on the button.
    x = signal.resample_poly(load('switch'), 6, 5)  # pitched down (0.83x, about three semitones) for a deeper click
    a = np.abs(x)
    x = x[max(0, int(np.argmax(a > 0.05 * a.max())) - 20):]
    return remaster(x, 9000, sub=(0.3, 320, 140, 0.04), snap=0.3, air=0.0, excite=0.4, attack=0.8, low_db=2.0,
                    mud_db=-3.0, presence_db=2.0, space=ms.SMALL, wet=0.12, slap=None, hits=first_hit(x), loudness=1.3)


def throw():
    # The original (thrown things and grenades bouncing share it), only with more bass.
    y = shelf(load('throw'), 120, 7.0, 'low')
    y = y / (np.max(np.abs(y)) or 1.0) * 0.95
    return ms.mix(y)


def zing():
    x = load('zing')
    return remaster(x, 10000, sub=None, snap=0.2, air=0.4, space=ms.SMALL, wet=0.2, slap=None, hits=first_hit(x))


def mine_beep():
    return remaster(load('mine_beep'), 5000, sub=None, snap=0, air=0, excite=0.5, attack=0.3, space=ms.SMALL, wet=0.2,
                    slap=None, hits=[])


def flare():
    return remaster(load('flare'), 7500, sub=(0.5, 220, 60, 0.08), snap=0.5, air=0.5, space=ms.SMALL, wet=0.25,
                    slap=None, hits=[onsets(load('flare'))[0]])


SOUNDS = {
    'pistol': pistol, 'sniper': sniper, 'pistol_light': pistol_light, 'machine_gun_loop': machine_gun_loop, 'spin_down': spin_down,
    'missile': missile, 'plasma_charge': plasma_charge, 'plasma_fire': plasma_fire, 'shocker': shocker,
    'switch': switch, 'throw': throw, 'zing': zing, 'mine_beep': mine_beep, 'flare': flare,
}
ORIGINAL = {'sniper': 'pistol'}  # sounds made from another's original


def main(args):
    OUT.mkdir(exist_ok=True)
    made = {}
    for name, make in SOUNDS.items():
        data = ms.wav_bytes(make())
        (OUT / f'{name}.wav').write_bytes(data)
        made[name] = data
        print(f'{name}.wav  {len(data) // 1024} KB')
    if 'preview' in args:
        b64 = lambda d: base64.b64encode(d).decode()
        rows = ''.join(f'<p><b>{n}</b><br>original <audio controls src="data:audio/wav;base64,'
                       f'{b64((SRC / f"{ORIGINAL.get(n, n)}.wav").read_bytes())}"></audio> remaster <audio controls '
                       f'src="data:audio/wav;base64,{b64(d)}"></audio></p>' for n, d in made.items())
        (HERE / 'preview.html').write_text(f'<!doctype html><meta charset="utf-8"><title>Weapon Sounds</title>'
                                           f'<body style="font-family:sans-serif">{rows}</body>', encoding='utf-8')


if __name__ == '__main__':
    main(sys.argv[1:])
