"""World 2, Mirefall: the marsh theme in four arrangements and the world's victory sting.

Brooding and rain-soaked (piano, cello, low strings, choir, tower bells, distant thunder), rising to the storm at
the lighthouse, where the theme drives at full speed over a string ostinato and big drums."""

from synth import MINOR, Song, arp, bassline, melody, pads, place_chords, stabs
from themes import MIRE_A, MIRE_B, minor_v


def _rain(s, vel=0.35):
    """A soft hiss under the whole loop (one long note, so it wraps without a seam)."""
    s.add("rain", "hiss", 0, s.beats - 0.5, 60, vel, lo=1800, hi=9000, a=1.0, r=0.4)


def stiltwater_outskirts():
    """2.1: storm over the flooded boardwalks. A brooding tune: piano ostinato, cello, strings and choir."""
    s = Song("mirefall_1_stiltwater_outskirts", bpm=88, bars=32, key=60, scale=MINOR, reverb=2.8, damp=0.55,
             loudness=-17.5)
    s.bus("lead", gain=0.9, rev=0.3)
    s.bus("piano", gain=0.5, rev=0.3, delay=(0.75, 0.25, 0.15))
    s.bus("pad", gain=0.3, rev=0.4, width=0.5)
    s.bus("choir", gain=0.32, rev=0.5, width=0.4)
    s.bus("bass", gain=0.7, rev=0.1, lp=800)
    s.bus("drums", gain=0.6, rev=0.25)
    s.bus("rain", gain=0.35, rev=0.2, width=0.6)
    s.bus("fx", gain=0.55, rev=0.4)
    _rain(s)
    ost = (0, 2, 1, 2, 4, 2, 1, 2)
    # 0-3: piano and rain
    intro = [dict(notes=[], chords=c) for c in ([(0, 4)], [(5, 4)], [(3, 4)], [(4, 4)])]
    ch = place_chords(s, 0, intro, quality=minor_v)
    arp(s, "piano", "softpiano", ch, 64, step=0.5, pattern=ost, vel=0.55)
    pads(s, "pad", "darkpad", ch, 55, vel=0.5)
    s.add("fx", "thunder", 1 * 4 + 2, 8, 40, 0.8)
    # 4-11: the theme on cello
    ch = place_chords(s, 4, MIRE_A, quality=minor_v)
    melody(s, "lead", "cello", 4, MIRE_A, octave=-1, vel=0.85, legato=0.98)
    arp(s, "piano", "softpiano", ch, 67, step=0.5, pattern=ost, vel=0.5)
    pads(s, "pad", "darkpad", ch, 55, vel=0.5)
    bassline(s, "bass", "bass_sub", ch, [(0, 3.5, 0)], octave=-2)
    for b in range(4, 12):
        s.drums("drums", b, {"timpani": "x......." + ("....x..." if b % 2 else "........")},
                pitches={"timpani": 36})
    # 12-19: strings take the tune an octave up, the choir under it
    ch = place_chords(s, 12, MIRE_A, quality=minor_v)
    melody(s, "lead", "strings", 12, MIRE_A, octave=0, vel=0.8, legato=1.0, a=0.15)
    melody(s, "lead", "cello", 12, MIRE_A, octave=-1, vel=0.5, legato=0.98)
    pads(s, "choir", "choir_oo", ch, 60, vel=0.55)
    arp(s, "piano", "softpiano", ch, 67, step=0.5, pattern=ost, vel=0.45)
    bassline(s, "bass", "bass_sub", ch, [(0, 3.5, 0)], octave=-2)
    s.drums("drums", 12, {"timpani": "x.......x.......", "tom": "............x.x."}, bars=8,
            pitches={"timpani": 36, "tom": 43}, vel=0.8)
    s.add("fx", "thunder", 16 * 4, 8, 40, 0.9)
    # 20-27: B on horn, choir in full, the rise
    ch = place_chords(s, 20, MIRE_B, quality=minor_v)
    melody(s, "lead", "horn", 20, MIRE_B, octave=0, vel=0.9, legato=0.95)
    pads(s, "choir", "choir", ch, 62, vel=0.6)
    pads(s, "pad", "strings", ch, 55, vel=0.5)
    arp(s, "piano", "softpiano", ch, 67, step=0.25, pattern=(0, 1, 2, 4), vel=0.4)
    bassline(s, "bass", "bass_sub", ch, [(0, 1.8, 0), (2, 1.8, 0)], octave=-2)
    s.drums("drums", 20, {"timpani": "x.......x.......", "tom": "....x.x.....x.xx"}, bars=8,
            pitches={"timpani": 36, "tom": 43}, vel=0.9)
    s.add("drums", "crash", 20 * 4, 1, 60, 0.35)
    s.add("fx", "thunder", 26 * 4, 8, 40, 1.0)
    # 28-31: the storm passes over: piano alone, winding back to the start
    ch = place_chords(s, 28, intro, quality=minor_v)
    arp(s, "piano", "softpiano", ch, 64, step=0.5, pattern=ost, vel=0.5)
    pads(s, "pad", "darkpad", ch, 55, vel=0.45)
    melody(s, "lead", "cello", 28, MIRE_A[:2], octave=-1, vel=0.5, stretch=2, legato=0.98)
    return s


def drowned_bellmarket():
    """2.2: the town square in the storm. The same tune with the town's bells and lit windows: oboe, harpsichord,
    a turn to the warm relative major in its middle."""
    s = Song("mirefall_2_drowned_bellmarket", bpm=96, bars=32, key=60, scale=MINOR, reverb=2.6, damp=0.5,
             loudness=-17.0)
    s.bus("lead", gain=0.9, rev=0.3, delay=(0.75, 0.2, 0.12))
    s.bus("bells", gain=0.38, rev=0.5, width=0.3)
    s.bus("harpsi", gain=1.1, rev=0.25, width=0.3)
    s.bus("pad", gain=0.28, rev=0.4, width=0.5)
    s.bus("bass", gain=1.8, rev=0.1, lp=1000)
    s.bus("drums", gain=0.55, rev=0.2)
    s.bus("rain", gain=0.28, rev=0.2, width=0.6)
    s.bus("fx", gain=0.45, rev=0.4)
    _rain(s, 0.3)
    toll = [0, 4, 2, -3]
    # 0-3: the bells toll the theme's head
    for b in range(4):
        s.add("bells", "bell", b * 4, 4, s.pitch(toll[b], 0), 0.7, -0.2 + 0.15 * b)
    intro = [dict(notes=[], chords=c) for c in ([(0, 4)], [(5, 4)], [(3, 4)], [(4, 4)])]
    ch = place_chords(s, 0, intro, quality=minor_v)
    pads(s, "pad", "darkpad", ch, 55, vel=0.5)
    s.add("fx", "thunder", 2 * 4, 8, 40, 0.7)
    # 4-11: the tune on oboe over harpsichord
    ch = place_chords(s, 4, MIRE_A, quality=minor_v)
    melody(s, "lead", "oboe", 4, MIRE_A, octave=1, vel=0.85, legato=0.95)
    arp(s, "harpsi", "harpsi", ch, 64, step=0.5, pattern=(0, 1, 2, 3, 2, 1, 2, 1), vel=0.5, pan=-0.25)
    pads(s, "pad", "darkpad", ch, 55, vel=0.45)
    bassline(s, "bass", "upright", ch, [(0, 1.8, 0), (2, 1.8, 2)], octave=-2)
    s.drums("drums", 4, {"brush": "....x.......x...", "rim": "x.....x...x....."}, bars=8, pitches={"rim": 76})
    # 12-19: the lit windows: B in the relative major (the same notes, major chords), bells on the downbeats
    ch = place_chords(s, 12, MIRE_B)
    melody(s, "lead", "strings", 12, MIRE_B, octave=1, vel=0.8, legato=1.0, a=0.12)
    arp(s, "harpsi", "harpsi", ch, 67, step=0.25, pattern=(0, 1, 2, 1), vel=0.42, pan=-0.25)
    pads(s, "pad", "warmpad", ch, 58, vel=0.5)
    bassline(s, "bass", "upright", ch, [(0, 1.8, 0), (2, 1.8, 2)], octave=-2)
    for beat, beats, root, q in ch[::2]:
        s.add("bells", "bell", beat, 4, s.pitch(root, 0), 0.45, 0.3)
    s.drums("drums", 12, {"brush": "....x.......x...", "rim": "x.....x...x....."}, bars=8, pitches={"rim": 76})
    # 20-27: back to the storm: the tune on cello and oboe together, timpani
    ch = place_chords(s, 20, MIRE_A, quality=minor_v)
    melody(s, "lead", "oboe", 20, MIRE_A, octave=1, vel=0.75, legato=0.95)
    melody(s, "lead", "cello", 20, MIRE_A, octave=-1, vel=0.6, legato=0.98)
    arp(s, "harpsi", "harpsi", ch, 64, step=0.5, pattern=(0, 1, 2, 3, 2, 1, 2, 1), vel=0.45, pan=-0.25)
    pads(s, "pad", "choir_oo", ch, 60, vel=0.5)
    bassline(s, "bass", "upright", ch, [(0, 1.8, 0), (2, 1.8, 2)], octave=-2)
    s.drums("drums", 20, {"timpani": "x.......x.......", "brush": "....x.......x..."}, bars=8,
            pitches={"timpani": 36})
    s.add("fx", "thunder", 24 * 4, 8, 40, 0.8)
    # 28-31: the tower: bells over a held chord
    ch = place_chords(s, 28, intro, quality=minor_v)
    pads(s, "pad", "darkpad", ch, 55, vel=0.5)
    for b in range(4):
        s.add("bells", "bell", (28 + b) * 4, 4, s.pitch(toll[b], 0), 0.6, 0.2 - 0.15 * b)
        s.add("bells", "bell", (28 + b) * 4 + 2, 2, s.pitch(toll[b] + 4, 0), 0.3, 0.4)
    bassline(s, "bass", "upright", ch, [(0, 3.5, 0)], octave=-2)
    return s


def undercistern():
    """2.3: the drowned cisterns under the town. Slow dread: a low drone, glass tones playing fragments of the
    theme, drips, a far heartbeat."""
    s = Song("mirefall_3_the_undercistern", bpm=66, bars=24, key=53, scale=MINOR, reverb=4.0, damp=0.65,
             loudness=-19.5)
    s.bus("lead", gain=0.85, rev=0.5, delay=(1.5, 0.35, 0.3))
    s.bus("drone", gain=0.5, rev=0.3, width=0.5)
    s.bus("pad", gain=0.3, rev=0.5, width=0.6)
    s.bus("drips", gain=1.2, rev=0.55, delay=(0.75, 0.5, 0.45))
    s.bus("pulse", gain=0.6, rev=0.2, lp=400)
    s.bus("bass", gain=0.6, rev=0.15, lp=500)
    s.bus("fx", gain=0.4, rev=0.6)
    for b in range(0, 24, 4):
        s.add("drone", "drone", b * 4, 16, s.pitch(0, -2), 0.6)
        s.add("drone", "drone", b * 4, 16, s.pitch(0, -1), 0.3)
    for b in range(24):
        s.drums("pulse", b, {"kick_soft": "x...............", "tom": "........o......."},
                pitches={"tom": 38}, vel=0.6)
    r = s.rng
    for b in range(24):
        for k in range(2):
            if r.random() < 0.55:
                beat = b * 4 + float(r.integers(0, 8)) * 0.5
                s.add("drips", "drip", beat, 0.3, s.pitch(int(r.choice([0, 2, 4, 7, 9])), 2), 0.5,
                      float(r.uniform(-0.8, 0.8)))
    # 4-11: the tune's first phrase at half speed on glass
    ch = place_chords(s, 4, MIRE_A[:4], quality=minor_v, stretch=2)
    melody(s, "lead", "glass", 4, MIRE_A[:4], octave=0, vel=0.7, stretch=2, legato=1.0)
    pads(s, "pad", "darkpad", ch, 52, vel=0.55)
    bassline(s, "bass", "bass_sub", ch, [(0, 7.5, 0)], octave=-2, vel=0.7)
    # 12-15: only a cluster: the minor second rubbing in the dark
    for b in (12, 14):
        for deg, oc in ((0, 0), (1, 0), (4, -1)):
            s.add("pad", "strings", b * 4, 8, s.pitch(deg, oc), 0.45, cut=700)
    s.add("fx", "swell", 15 * 4, 4, 60, 0.5, lo=100, hi=2000)
    # 16-23: B's opening on celesta, far off, with the low strings
    ch = place_chords(s, 16, MIRE_B[:4], quality=minor_v, stretch=2)
    melody(s, "lead", "celesta", 16, MIRE_B[:4], octave=1, vel=0.6, stretch=2)
    melody(s, "lead", "glass", 16, MIRE_B[:4], octave=-1, vel=0.4, stretch=2, legato=1.0)
    pads(s, "pad", "darkpad", ch, 52, vel=0.55)
    bassline(s, "bass", "bass_sub", ch, [(0, 7.5, 0)], octave=-2, vel=0.7)
    return s


def stormspire():
    """2.4: the lighthouse climb in the storm at its worst. The theme at full speed: string ostinato, brass, choir,
    big drums, thunder; its second half climbs a tone."""
    s = Song("mirefall_4_stormspire", bpm=144, bars=48, key=60, scale=MINOR, reverb=2.4, damp=0.5,
             loudness=-15.0)
    s.bus("brass", gain=0.85, rev=0.25)
    s.bus("strings", gain=0.45, rev=0.2, width=0.3)
    s.bus("choir", gain=0.4, rev=0.4, width=0.4)
    s.bus("bass", gain=0.65, rev=0.05, lp=1200)
    s.bus("drums", gain=0.55, rev=0.15)
    s.bus("fx", gain=0.5, rev=0.35)
    s.bus("rain", gain=0.3, rev=0.15, width=0.6)
    _rain(s, 0.35)
    ost = (0, 0, 2, 0, 1, 0, 2, 1)
    big = {"taiko": "x.....x...x.....", "snare": "....x.......x...", "tom": "..........x..x.x",
           "hat": "x.x.x.x.x.x.x.x."}
    half = {"taiko": "x.......x.......", "tom": "......x.......xx"}

    def section(bar, bars, key, lead_parts, beat):
        s.key = key
        ch = place_chords(s, bar, bars, quality=minor_v)
        arp(s, "strings", "pizz", ch, 60, step=0.25, pattern=ost, vel=0.6, pan=-0.3, t60=0.35)
        arp(s, "strings", "cello", ch, 48, step=0.5, pattern=(0, 0, 0, 0), vel=0.45, pan=0.3, a=0.01, r=0.05)
        bassline(s, "bass", "bass_pluck", ch, [(0, 0.4, 0), (0.5, 0.4, 0), (1, 0.4, 3), (1.5, 0.4, 0)])
        s.drums("drums", bar, beat, bars=len(bars), pitches={"taiko": 41, "tom": 48}, pans={"hat": 0.3})
        for preset, octave, vel in lead_parts:
            melody(s, "brass" if preset != "choir" else "choir", preset, bar, bars, octave=octave, vel=vel,
                   legato=0.95)
        return ch

    # each section sets the key for its own notes; notes keep their pitch once added
    s.key = 60
    intro = [dict(notes=[], chords=c) for c in ([(0, 4)], [(5, 4)], [(3, 4)], [(4, 4)])]
    ch = section(0, intro, 60, [], half)
    pads(s, "choir", "choir_oo", ch, 60, vel=0.5)
    s.add("fx", "thunder", 0, 8, 40, 1.0)
    section(4, MIRE_A, 60, [("brass", 0, 0.9)], big)
    ch = section(12, MIRE_A, 60, [("brass", 0, 0.85), ("brass", 1, 0.45)], big)
    pads(s, "choir", "choir", ch, 64, vel=0.55)
    s.add("fx", "thunder", 16 * 4, 8, 40, 0.9)
    ch = section(20, MIRE_B, 60, [("brass", 0, 0.9), ("choir", 1, 0.6)], big)
    s.add("drums", "crash", 20 * 4, 1, 60, 0.4)
    ch = section(28, MIRE_B, 62, [("brass", 0, 0.95), ("choir", 1, 0.65), ("horn", -1, 0.5)], big)
    pads(s, "strings", "strings", ch, 62, vel=0.45)
    s.add("drums", "crash", 28 * 4, 1, 60, 0.45)
    s.add("fx", "thunder", 30 * 4, 8, 40, 1.0)
    ch = section(36, MIRE_A[:4], 62, [("horn", 0, 0.8)], half)
    pads(s, "choir", "choir_oo", ch, 62, vel=0.5)
    # 40-47: the drums alone with the ostinato, falling back to the start's key
    ch = section(40, intro + intro, 60, [], big)
    s.drums("drums", 47, {"snare": "x.x.x.x.xxxxxxxx", "taiko": "x...x...x...x..."}, pitches={"taiko": 41})
    s.add("fx", "swell", 47 * 4, 4, 60, 0.7)
    s.add("fx", "thunder", 44 * 4, 8, 40, 1.0)
    for b in (0, 4, 12, 40):
        s.add("drums", "crash", b * 4, 1, 60, 0.4)
    s.key = 60
    return s


def victory():
    """The storm breaks: bells and choir, the theme's head turning from minor to major."""
    s = Song("mirefall_victory", bpm=84, bars=3, key=60, scale=MINOR, loop=False, tail=5.0, reverb=3.0,
             loudness=-16.0)
    s.bus("lead", gain=0.9, rev=0.35)
    s.bus("choir", gain=0.5, rev=0.45, width=0.4)
    s.bus("bells", gain=0.45, rev=0.5)
    s.bus("bass", gain=0.7, rev=0.1)
    s.bus("drums", gain=0.6, rev=0.3)
    tune = [dict(notes=[(0, 1.5), (1, .5), (2, 1), (4, 1)], chords=[(0, 2), (5, 2)]),
            dict(notes=[(3, 1), (6, 1), (7, 2)], chords=[(3, 2), (4, 2)]),
            dict(notes=[(None, 4)], chords=[(0, 4)])]
    ch = place_chords(s, 0, tune, quality=minor_v)
    # the last chord is C major: the storm is over
    s.chords[-1] = (8, 4, 0, "M")
    melody(s, "lead", "horn", 0, tune, octave=0, vel=0.85, legato=0.98)
    pads(s, "choir", "choir", ch[:-1], 62, vel=0.6)
    final = s.voicing(0, 64, 4, quality="M")
    for p in final:
        s.add("choir", "choir", 8, 4, p, 0.7)
        s.add("lead", "strings", 8, 4, p, 0.55)
    s.add("lead", "horn", 8, 4, s.pitch(7, 0, 0, "M"), 0.8)
    s.add("bass", "bass_sub", 8, 4, s.pitch(0, -2), 0.8)
    for i, deg in enumerate((0, 2, 4)):
        s.add("bells", "bell", 8 + i * 0.5, 4, s.pitch(deg, 0, 0, "M"), 0.6, -0.3 + 0.3 * i)
    s.drums("drums", 1, {"timpani": "x.x.xxxxxxxxxxxx"}, pitches={"timpani": 36}, vel=0.6)
    s.add("drums", "timpani", 8, 1, 36, 1.0)
    s.add("drums", "crash", 8, 1, 60, 0.4)
    return s


TRACKS = {
    "mirefall_1_stiltwater_outskirts": ("2.1 Stiltwater Outskirts", stiltwater_outskirts),
    "mirefall_2_drowned_bellmarket": ("2.2 Drowned Bellmarket", drowned_bellmarket),
    "mirefall_3_the_undercistern": ("2.3 The Undercistern", undercistern),
    "mirefall_4_stormspire": ("2.4 Stormspire", stormspire),
    "mirefall_victory": ("Mirefall's end (sting)", victory),
}
