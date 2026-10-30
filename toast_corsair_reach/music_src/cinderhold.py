"""World 3, Cinderhold: the forge theme in four arrangements and the pack's last victory sting.

Heavy, industrial and driving (distorted power chords, anvils, machines, taiko, brass and choir) in E phrygian,
climbing to the summit arena, where the finale brings back the cay's and the marsh's themes before its own."""

from synth import MINOR, PHRYGIAN, Song, arp, bassline, melody, pads, place_chords
from themes import CAY_A, CINDER_A, CINDER_B, MIRE_A, minor_v

RIFF = [dict(notes=[], chords=c) for c in ([(0, 4)], [(1, 4)], [(0, 4)], [(6, 2), (1, 2)])]


def chugs(s, bus, chords, grid="X.x.x.xxX.x.x.x.", octave=-1, vel=0.6, preset="chug"):
    """Power chords (root and fifth) on a 16-step grid, for every chord."""
    levels = {"X": 1.0, "x": 0.75, "o": 0.45}
    for beat, beats, root, q in chords:
        for i in range(int(beats * 4)):
            ch = grid[(int(round(beat * 4)) + i) % len(grid)]
            if ch in levels:
                r = s.pitch(root, octave)
                for p in (r, r + 7):
                    s.add(bus, preset, beat + i * 0.25, 0.22, p, vel * levels[ch])


def slag_flats():
    """3.1: a red dusk over the lava flats. Heavy and driving: power chords, anvils, brass."""
    s = Song("cinderhold_1_slag_flats", bpm=112, bars=36, key=52, scale=PHRYGIAN, reverb=2.0, damp=0.55,
             loudness=-15.0)
    s.bus("brass", gain=0.9, rev=0.25)
    s.bus("counter", gain=0.4, rev=0.25, delay=(0.75, 0.25, 0.15))
    s.bus("gtr", gain=0.42, rev=0.08, width=0.4, lp=5000)
    s.bus("pad", gain=0.28, rev=0.4, width=0.5)
    s.bus("bass", gain=0.62, rev=0.03, lp=1500)
    s.bus("drums", gain=0.55, rev=0.12)
    s.bus("metal", gain=0.35, rev=0.35)
    beat = {"kick_big": "x.......x.x.....", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.x.",
            "taiko": "x..............."}
    drive_b = {"kick_big": "x.....x.x.x.....", "snare": "....x.......x..o", "hat": "x.xxx.x.x.xxx.x.",
               "taiko": "x.......x......."}
    pitches = {"taiko": 40}

    def riff(bar):
        ch = place_chords(s, bar, RIFF)
        chugs(s, "gtr", ch)
        bassline(s, "bass", "bass_dist", ch, [(0, 0.22, 0), (0.5, 0.22, 0), (0.75, 0.22, 0), (1.5, 0.22, 0)])
        s.drums("drums", bar, beat, bars=4, pitches=pitches, pans={"hat": 0.3})
        s.drums("metal", bar, {"anvil": "....x.......x..."}, bars=4, pitches={"anvil": 84}, pans={"anvil": 0.4})

    riff(0)
    s.add("drums", "crash", 0, 1, 60, 0.45)
    # 4-11: the theme on brass
    ch = place_chords(s, 4, CINDER_A)
    melody(s, "brass", "brass", 4, CINDER_A, octave=1, vel=0.9, legato=0.92)
    chugs(s, "gtr", ch, vel=0.5)
    pads(s, "pad", "darkpad", ch, 52, vel=0.5)
    bassline(s, "bass", "bass_dist", ch, [(0, 0.22, 0), (0.5, 0.22, 0), (0.75, 0.22, 0), (1.5, 0.22, 0)])
    s.drums("drums", 4, beat, bars=8, pitches=pitches, pans={"hat": 0.3})
    # 12-19: again, a buzzing counter-line an octave up and the anvils on every backbeat
    ch = place_chords(s, 12, CINDER_A)
    melody(s, "brass", "brass", 12, CINDER_A, octave=1, vel=0.9, legato=0.92)
    melody(s, "counter", "buzz", 12, CINDER_A, octave=1, vel=0.5, transpose=2, legato=0.7)
    chugs(s, "gtr", ch, vel=0.55)
    pads(s, "pad", "darkpad", ch, 52, vel=0.5)
    bassline(s, "bass", "bass_dist", ch, [(0, 0.22, 0), (0.5, 0.22, 0), (0.75, 0.22, 0), (1.5, 0.22, 0)])
    s.drums("drums", 12, drive_b, bars=8, pitches=pitches, pans={"hat": 0.3})
    s.drums("metal", 12, {"anvil": "....x.......x...", "clank": "..x.....x..x...."}, bars=8,
            pitches={"anvil": 84, "clank": 91}, pans={"anvil": 0.4, "clank": -0.4})
    s.add("drums", "crash", 12 * 4, 1, 60, 0.45)
    # 20-27: B, the climb: brass and choir, held power chords
    ch = place_chords(s, 20, CINDER_B)
    melody(s, "brass", "brass", 20, CINDER_B, octave=0, vel=0.95, legato=0.95)
    pads(s, "pad", "choir", ch, 62, vel=0.6)
    chugs(s, "gtr", ch, grid="X.......X...x...", vel=0.6, preset="power")
    bassline(s, "bass", "bass_dist", ch, [(0, 0.4, 0), (0.5, 0.4, 0), (1, 0.4, 0), (1.5, 0.4, 3)])
    s.drums("drums", 20, drive_b, bars=8, pitches=pitches, pans={"hat": 0.3})
    s.add("drums", "crash", 20 * 4, 1, 60, 0.5)
    # 28-31: the breakdown: drums, steam and metal
    ch = place_chords(s, 28, RIFF)
    bassline(s, "bass", "bass_dist", ch, [(0, 1.5, 0), (2.5, 0.4, 0), (3, 0.4, 1)])
    for b in range(28, 32):
        s.drums("drums", b, {"taiko": "x..x..x...x..x..", "kick_big": "x.......x......."}, pitches=pitches)
        s.drums("metal", b, {"anvil": "x.....x.....x...", "piston": "..x...x...x...x."},
                pitches={"anvil": 79}, pans={"anvil": -0.3, "piston": 0.3})
        s.add("metal", "hiss", b * 4 + 3, 1, 60, 0.6, a=0.02, r=0.15)
    s.drums("drums", 31, {"snare": "........x.x.xxxx"})
    riff(32)
    s.add("drums", "crash", 32 * 4, 1, 60, 0.45)
    return s


def bellows():
    """3.2: inside the foundry. The flats' tune made harder: machine rhythms, a pumping distorted bass, a
    buzzing lead and anvils."""
    s = Song("cinderhold_2_the_bellows", bpm=124, bars=40, key=52, scale=PHRYGIAN, reverb=1.8, damp=0.6,
             loudness=-15.0)
    s.bus("lead", gain=0.8, rev=0.2, delay=(0.75, 0.25, 0.15))
    s.bus("brass", gain=0.85, rev=0.22)
    s.bus("gtr", gain=0.38, rev=0.08, width=0.4, lp=5000, duck=0.4)
    s.bus("pad", gain=0.25, rev=0.35, width=0.5, duck=0.5)
    s.bus("bass", gain=0.62, rev=0.02, lp=1600, duck=0.6)
    s.bus("drums", gain=0.6, rev=0.1)
    s.bus("machine", gain=0.45, rev=0.25, width=0.3)
    beat = {"kick_big": "x...x...x...x...", "clap": "....x.......x...", "hat": "..x...x...x...x."}
    machines = {"piston": ".x.x.x.x.x.x.x.x", "clank": "..x..x....x..x..", "hat": "xxxxxxxxxxxxxxxx"}
    mp = {"clank": 88}
    sixteenths = [(i * 0.25, 0.2, 0) for i in range(4)]

    def machine(bar, bars, vel=1.0):
        s.drums("machine", bar, machines, bars=bars, pitches=mp, pans={"clank": -0.4, "piston": 0.35, "hat": 0.2},
                vel=vel)
        for b in range(bar, bar + bars, 2):
            s.add("machine", "hiss", b * 4 + 7, 1, 60, 0.6, a=0.02, r=0.15)

    # 0-3: the machines start up
    ch = place_chords(s, 0, RIFF)
    machine(0, 4, 0.8)
    bassline(s, "bass", "bass_dist", ch, sixteenths)
    s.drums("drums", 2, {"kick_big": "x...x...x...x..."}, bars=2, duck="kick_big")
    # 4-11: the tune on a buzzing lead
    ch = place_chords(s, 4, CINDER_A)
    melody(s, "lead", "buzz", 4, CINDER_A, octave=1, vel=0.85, legato=0.85)
    bassline(s, "bass", "bass_dist", ch, sixteenths)
    chugs(s, "gtr", ch, grid="x..x..x...x..x..", vel=0.5)
    s.drums("drums", 4, beat, bars=8, duck="kick_big", pans={"hat": 0.3})
    machine(4, 8)
    # 12-19: brass takes it, the buzz an octave up
    ch = place_chords(s, 12, CINDER_A)
    melody(s, "brass", "brass", 12, CINDER_A, octave=1, vel=0.9, legato=0.92)
    melody(s, "lead", "buzz", 12, CINDER_A, octave=2, vel=0.4, legato=0.6)
    bassline(s, "bass", "bass_dist", ch, sixteenths)
    chugs(s, "gtr", ch, grid="x..x..x...x..x..", vel=0.55)
    pads(s, "pad", "darkpad", ch, 52, vel=0.5)
    s.drums("drums", 12, dict(beat, snare="....x.......x..o"), bars=8, duck="kick_big", pans={"hat": 0.3})
    machine(12, 8)
    s.add("drums", "crash", 12 * 4, 1, 60, 0.45)
    # 20-27: B on brass and choir, anvils on the backbeat
    ch = place_chords(s, 20, CINDER_B)
    melody(s, "brass", "brass", 20, CINDER_B, octave=0, vel=0.95, legato=0.95)
    pads(s, "pad", "choir", ch, 62, vel=0.6)
    bassline(s, "bass", "bass_dist", ch, sixteenths)
    chugs(s, "gtr", ch, grid="X.......X...x...", vel=0.55, preset="power")
    s.drums("drums", 20, dict(beat, snare="....x.......x..."), bars=8, duck="kick_big", pans={"hat": 0.3})
    s.drums("machine", 20, {"anvil": "....x.......x..."}, bars=8, pitches={"anvil": 84}, pans={"anvil": 0.4})
    s.add("drums", "crash", 20 * 4, 1, 60, 0.5)
    # 28-31: the machine break
    ch = place_chords(s, 28, RIFF)
    machine(28, 4)
    bassline(s, "bass", "bass_dist", ch, [(0, 0.2, 0), (0.75, 0.2, 0), (1.5, 0.2, 0)])
    for b in range(28, 32):
        s.drums("drums", b, {"taiko": "x.....x...x.....", "kick_big": "x.......x......."},
                pitches={"taiko": 40}, duck="kick_big")
    s.drums("drums", 31, {"snare": "........xxxxxxxx"})
    s.add("machine", "swell", 31 * 4, 4, 60, 0.6)
    # 32-39: B with everything
    ch = place_chords(s, 32, CINDER_B)
    melody(s, "brass", "brass", 32, CINDER_B, octave=0, vel=0.95, legato=0.95)
    melody(s, "lead", "buzz", 32, CINDER_B, octave=1, vel=0.5, legato=0.8)
    pads(s, "pad", "choir", ch, 62, vel=0.55)
    bassline(s, "bass", "bass_dist", ch, sixteenths)
    chugs(s, "gtr", ch, vel=0.5)
    s.drums("drums", 32, dict(beat, snare="....x.......x..o"), bars=8, duck="kick_big", pans={"hat": 0.3})
    machine(32, 8)
    s.add("drums", "crash", 32 * 4, 1, 60, 0.5)
    return s


def caldera_crown():
    """3.3, the finale: the summit arena. Everything at once at 150 bpm: string ostinato, power chords, taiko,
    choir and brass; in its middle the cay's and the marsh's themes come back, then the forge theme's last climb."""
    s = Song("cinderhold_3_caldera_crown", bpm=150, bars=48, key=52, scale=PHRYGIAN, reverb=2.4, damp=0.5,
             loudness=-14.5)
    s.bus("brass", gain=0.9, rev=0.25)
    s.bus("choir", gain=0.42, rev=0.4, width=0.4)
    s.bus("strings", gain=0.9, rev=0.2, width=0.3)
    s.bus("gtr", gain=0.36, rev=0.08, width=0.4, lp=5000)
    s.bus("bass", gain=0.62, rev=0.03, lp=1500)
    s.bus("drums", gain=0.5, rev=0.15)
    s.bus("metal", gain=0.3, rev=0.35)
    big = {"kick_big": "x.....x.x.......", "snare": "....x.......x...", "taiko": "x.......x.....x.",
           "hat": "x.x.x.x.x.x.x.x."}
    gallop = {"kick_big": "x.xx..x.x.xx..x.", "snare": "....x.......x...", "taiko": "x.......x.......",
              "ride": "x...x...x...x..."}
    tp = {"taiko": 40}
    ost = (0, 2, 1, 2, 0, 2, 1, 3)

    def bed(bar, bars, drums, quality=None, gtr=True):
        ch = place_chords(s, bar, bars, quality=quality)
        arp(s, "strings", "pizz", ch, 64, step=0.25, pattern=ost, vel=0.6, pan=-0.3, t60=0.35)
        if gtr:
            chugs(s, "gtr", ch, vel=0.5)
        bassline(s, "bass", "bass_dist", ch, [(0, 0.22, 0), (0.5, 0.22, 0), (0.75, 0.22, 0), (1.5, 0.22, 0)])
        s.drums("drums", bar, drums, bars=len(bars), pitches=tp, pans={"hat": 0.3, "ride": 0.3})
        return ch

    # 0-3: the arena opens: choir and taiko over the ostinato
    ch = bed(0, RIFF, {"taiko": "x.....x...x.....", "kick_big": "x.......x......."}, gtr=False)
    pads(s, "choir", "choir", ch, 62, vel=0.6)
    s.add("drums", "crash", 0, 1, 60, 0.5)
    # 4-19: the forge theme twice, the second time with the choir an octave up
    bed(4, CINDER_A, big)
    melody(s, "brass", "brass", 4, CINDER_A, octave=1, vel=0.9, legato=0.92)
    ch = bed(12, CINDER_A, gallop)
    melody(s, "brass", "brass", 12, CINDER_A, octave=1, vel=0.9, legato=0.92)
    melody(s, "choir", "choir", 12, CINDER_A, octave=2, vel=0.5, legato=0.98)
    s.drums("metal", 12, {"anvil": "....x.......x..."}, bars=8, pitches={"anvil": 84}, pans={"anvil": 0.4})
    s.add("drums", "crash", 12 * 4, 1, 60, 0.5)
    # 20-27: B, heroic
    ch = bed(20, CINDER_B, big)
    melody(s, "brass", "brass", 20, CINDER_B, octave=0, vel=0.95, legato=0.95)
    pads(s, "choir", "choir", ch, 64, vel=0.6)
    s.add("drums", "crash", 20 * 4, 1, 60, 0.5)
    # 28-35: the callbacks, in E minor: the cay's theme on horn, then the marsh's on brass and choir
    s.scale = MINOR
    ch = bed(28, CAY_A[:4], gallop, quality=minor_v)
    melody(s, "brass", "horn", 28, CAY_A[:4], octave=1, vel=0.9, legato=0.92)
    pads(s, "choir", "choir_oo", ch, 62, vel=0.5)
    ch = bed(32, MIRE_A[:4], gallop, quality=minor_v)
    melody(s, "brass", "brass", 32, MIRE_A[:4], octave=1, vel=0.9, legato=0.95)
    melody(s, "choir", "choir", 32, MIRE_A[:4], octave=1, vel=0.5, legato=0.98)
    s.add("drums", "crash", 32 * 4, 1, 60, 0.45)
    s.scale = PHRYGIAN
    # 36-43: B once more, everything
    ch = bed(36, CINDER_B, big)
    melody(s, "brass", "brass", 36, CINDER_B, octave=0, vel=1.0, legato=0.95)
    melody(s, "choir", "choir", 36, CINDER_B, octave=1, vel=0.55, legato=0.98)
    s.drums("metal", 36, {"anvil": "....x.......x..."}, bars=8, pitches={"anvil": 84}, pans={"anvil": 0.4})
    s.add("drums", "crash", 36 * 4, 1, 60, 0.55)
    # 44-47: the riff, rolling back into the start
    bed(44, RIFF, big)
    s.drums("drums", 47, {"snare": "x.x.x.x.xxxxxxxx", "taiko": "x...x...x...x..."}, pitches=tp)
    s.add("metal", "swell", 47 * 4, 4, 60, 0.7)
    return s


def coolant_vents():
    """3.4 (optional): the one cool place in the forge. Quiet: glass bells and pads, soft pumping, steam."""
    s = Song("cinderhold_4_coolant_vents", bpm=84, bars=28, key=52, scale=PHRYGIAN, reverb=3.4, damp=0.35,
             loudness=-20.0)
    s.bus("lead", gain=0.8, rev=0.4, delay=(0.75, 0.35, 0.3))
    s.bus("bells", gain=0.4, rev=0.45, delay=(0.75, 0.45, 0.4), width=0.3)
    s.bus("pad", gain=0.32, rev=0.5, width=0.6, duck=0.35)
    s.bus("bass", gain=0.6, rev=0.05, lp=600, duck=0.5)
    s.bus("pump", gain=0.4, rev=0.2, lp=2500)
    s.bus("steam", gain=0.3, rev=0.4, width=0.5)

    def cool(bar, bars, stretch=1):
        ch = place_chords(s, bar, bars, stretch=stretch)
        pads(s, "pad", "glass", ch, 64, vel=0.5)
        arp(s, "bells", "glassbell", ch, 76, step=0.75, pattern=(0, 2, 1, 3, 2, 4), vel=0.4)
        bassline(s, "bass", "bass_sub", ch, [(0, 0.4, 0), (0.5, 0.4, 0), (1.0, 0.4, 0), (1.5, 0.4, 0)])
        s.drums("pump", bar, {"piston": "x...x...x...x...", "kick_soft": "x.......x......."},
                bars=int(len(bars) * stretch), vel=0.45, duck="kick_soft")
        for b in range(bar, bar + int(len(bars) * stretch), 2):
            s.add("steam", "hiss", b * 4 + 2, 3, 60, 0.6, lo=3000, hi=12000, a=0.8, r=0.5)
        return ch

    cool(0, RIFF)
    cool(4, CINDER_A[:4], stretch=2)
    melody(s, "lead", "flute", 4, CINDER_A[:4], octave=2, vel=0.6, stretch=2, legato=0.97)
    ch = cool(12, CINDER_A[4:], stretch=2)
    melody(s, "lead", "glass", 12, CINDER_A[4:], octave=1, vel=0.6, stretch=2, legato=1.0)
    pads(s, "pad", "choir_oo", ch, 60, vel=0.4)
    cool(20, CINDER_B[:4], stretch=2)
    melody(s, "lead", "celesta", 20, CINDER_B[:4], octave=1, vel=0.55, stretch=2)
    return s


def victory():
    """The pack's end: the forge goes out. Timpani roll, brass and choir, phrygian turning to E major."""
    s = Song("cinderhold_victory", bpm=96, bars=3, key=52, scale=PHRYGIAN, loop=False, tail=5.0, reverb=2.6,
             loudness=-14.5)
    s.bus("brass", gain=0.9, rev=0.3)
    s.bus("choir", gain=0.45, rev=0.45, width=0.4)
    s.bus("bass", gain=0.7, rev=0.05)
    s.bus("drums", gain=0.8, rev=0.2)
    tune = [dict(notes=[(5, 1), (7, 1), (9, 2)], chords=[(5, 4)]),
            dict(notes=[(6, 1), (8, 1), (10, 2)], chords=[(6, 4)]),
            dict(notes=[(None, 4)], chords=[(0, 4)])]
    ch = place_chords(s, 0, tune)
    melody(s, "brass", "brass", 0, tune, octave=0, vel=0.95, legato=0.97)
    pads(s, "choir", "choir", ch[:2], 62, vel=0.6)
    for p in s.voicing(0, 64, 4, quality="M"):
        s.add("brass", "brass", 8, 4, p, 0.8)
        s.add("choir", "choir", 8, 4, p + 12, 0.6)
    s.add("brass", "brass", 8, 4, s.pitch(7, 0), 0.95)
    s.add("bass", "bass_dist", 0, 4, s.pitch(5, -2), 0.8)
    s.add("bass", "bass_dist", 4, 4, s.pitch(6, -2), 0.8)
    s.add("bass", "bass_dist", 8, 4, s.pitch(0, -2), 0.9)
    s.drums("drums", 0, {"taiko": "x.......x.......", "kick_big": "x.......x......."}, pitches={"taiko": 40})
    s.drums("drums", 1, {"timpani": "x.x.x.x.xxxxxxxx", "snare": "........xxxxxxxx"}, pitches={"timpani": 40},
            vel=0.7)
    s.add("drums", "crash", 8, 1, 60, 0.7)
    s.add("drums", "taiko", 8, 1, 40, 1.0)
    s.add("drums", "anvil", 8, 1, 84, 0.5)
    return s


TRACKS = {
    "cinderhold_1_slag_flats": ("3.1 Slag Flats", slag_flats),
    "cinderhold_2_the_bellows": ("3.2 The Bellows", bellows),
    "cinderhold_3_caldera_crown": ("3.3 Caldera Crown (finale)", caldera_crown),
    "cinderhold_4_coolant_vents": ("3.4 Coolant Vents (optional)", coolant_vents),
    "cinderhold_victory": ("Cinderhold's end (sting)", victory),
}
