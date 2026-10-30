"""World 1, Driftwood Cay: the cay theme in four arrangements and the world's victory sting.

Bright island adventure (steel pans, marimba, flute, congas) sliding down through the day into the corsairs' sea
cave, where the same tune turns minor, slow and quiet."""

from synth import MAJOR, MINOR, Song, arp, bassline, melody, pads, place_chords, stabs, strum
from themes import CAY_A, CAY_B, minor_v


def _island_drums(s, bar, bars, full=True):
    for b in range(bar, bar + bars):
        s.drums("perc", b, {"shaker": "xoxoxoxoxoxoxoxo"}, pans={"shaker": 0.35})
        s.drums("perc", b, {"conga": "....x.......x.x."}, pitches={"conga": 55}, pans={"conga": -0.3})
        s.drums("perc", b, {"conga": "..x...xo..x...x."}, pitches={"conga": 62}, pans={"conga": -0.2})
        if full:
            s.drums("drums", b, {"kick_soft": "x.....x.x.......", "rim": "x..x..x...x.x..."},
                    pitches={"rim": 86}, pans={"rim": 0.2})


def sunwreck_beach():
    """1.1: noon on the beach. A bright, easy calypso: steel pan theme, marimba, flute, congas."""
    s = Song("driftwood_1_sunwreck_beach", bpm=112, bars=40, key=62, scale=MAJOR, reverb=1.6, damp=0.4,
             loudness=-16.5)
    s.bus("lead", gain=1.0, rev=0.22, delay=(0.75, 0.25, 0.18))
    s.bus("harm", gain=0.5, rev=0.25)
    s.bus("flute", gain=0.8, rev=0.3, delay=(0.75, 0.3, 0.2))
    s.bus("mallet", gain=0.42, rev=0.2)
    s.bus("comp", gain=0.55, rev=0.2, width=0.3)
    s.bus("pad", gain=0.22, rev=0.4, width=0.5)
    s.bus("bass", gain=0.85, rev=0.03, lp=1800)
    s.bus("perc", gain=0.7, rev=0.12)
    s.bus("drums", gain=0.75, rev=0.08)
    calypso = [(0, 1.0, 0), (1.5, 0.45, 2)]
    # 0-7: the theme on steel pan
    ch = place_chords(s, 0, CAY_A)
    melody(s, "lead", "steelpan", 0, CAY_A, octave=1, vel=0.85)
    arp(s, "mallet", "marimba", ch, 69, step=0.5, pattern=(0, 1, 2, 1, 3, 2, 1, 2), vel=0.6, pan=-0.25)
    bassline(s, "bass", "bass_round", ch, calypso, octave=-2)
    _island_drums(s, 0, 8, full=False)
    s.drums("drums", 4, {"kick_soft": "x.......x......."}, bars=4)
    # 8-15: again, with a second pan a third below and the uke
    ch = place_chords(s, 8, CAY_A)
    melody(s, "lead", "steelpan", 8, CAY_A, octave=1, vel=0.85)
    melody(s, "harm", "steelpan", 8, CAY_A, octave=1, vel=0.7, transpose=-2, pan=0.35)
    strum(s, "comp", "uke", ch, 66, pattern=".x.x.x.u", vel=0.55, pan=0.3)
    arp(s, "mallet", "marimba", ch, 69, step=0.5, pattern=(0, 1, 2, 1, 3, 2, 1, 2), vel=0.5, pan=-0.25)
    bassline(s, "bass", "bass_round", ch, calypso, octave=-2)
    _island_drums(s, 8, 8)
    # 16-23: the B tune on flute, pans comping off the beat
    ch = place_chords(s, 16, CAY_B)
    melody(s, "flute", "flute", 16, CAY_B, octave=1, vel=0.8, legato=0.97)
    stabs(s, "comp", "steelpan", ch, 69, vel=0.4, pan=-0.3)
    pads(s, "pad", "warmpad", ch, 62, vel=0.5)
    bassline(s, "bass", "bass_round", ch, [(0, 0.5, 0), (0.75, 0.25, 0), (1.5, 0.45, 2)], octave=-2)
    _island_drums(s, 16, 8)
    for b in range(16, 24):
        s.drums("perc", b, {"tambourine": "....x.......x..."}, pans={"tambourine": 0.45})
    # 24-31: breakdown: marimba on the tune, bass and congas
    ch = place_chords(s, 24, CAY_A)
    melody(s, "lead", "marimba", 24, CAY_A, octave=1, vel=0.85)
    melody(s, "harm", "marimba", 24, CAY_A, octave=0, vel=0.55, transpose=-2,
           only=lambda i, d, b: (b % 2) < 1e-6)
    bassline(s, "bass", "bass_round", ch, [(0, 1.5, 0)], octave=-2, vel=0.7)
    _island_drums(s, 24, 7, full=False)
    s.drums("perc", 31, {"conga": "x.x.xxx.x.xxxxxx"}, pitches={"conga": 62})
    s.drums("perc", 31, {"bongo": "....x.x...x.x.xx"}, pitches={"bongo": 72})
    # 32-39: B on steel pan with the flute a third above
    ch = place_chords(s, 32, CAY_B)
    melody(s, "lead", "steelpan", 32, CAY_B, octave=1, vel=0.85)
    melody(s, "flute", "flute", 32, CAY_B, octave=1, vel=0.45, legato=0.97, transpose=2)
    strum(s, "comp", "uke", ch, 66, pattern=".x.x.x.u", vel=0.5, pan=0.3)
    arp(s, "mallet", "marimba", ch, 69, step=0.5, pattern=(0, 1, 2, 1, 3, 2, 1, 2), vel=0.45, pan=-0.25)
    pads(s, "pad", "warmpad", ch, 62, vel=0.45)
    bassline(s, "bass", "bass_round", ch, calypso, octave=-2)
    _island_drums(s, 32, 8)
    s.add("perc", "crash", 0, 1, 60, 0.35, 0.3)
    s.add("perc", "crash", 32 * 4, 1, 60, 0.3, -0.3)
    return s


def gullwing_docks():
    """1.2: golden hour on the docks. The theme with more drive: accordion and brass, a backbeat, 8th-note bass."""
    s = Song("driftwood_2_gullwing_docks", bpm=132, bars=40, key=65, scale=MAJOR, reverb=1.4, damp=0.5,
             loudness=-15.5)
    s.bus("lead", gain=2.0, rev=0.18, delay=(0.5, 0.2, 0.12))
    s.bus("brass", gain=1.0, rev=0.2)
    s.bus("whistle", gain=0.9, rev=0.3, delay=(0.75, 0.25, 0.2))
    s.bus("comp", gain=1.3, rev=0.15, width=0.35)
    s.bus("pizz", gain=1.3, rev=0.2, delay=(0.75, 0.3, 0.25))
    s.bus("pad", gain=0.2, rev=0.35, width=0.5)
    s.bus("bass", gain=0.7, rev=0.02, lp=2000)
    s.bus("drums", gain=0.65, rev=0.07)
    s.bus("perc", gain=1.4, rev=0.1)
    eights = [(0, 0.4, 0), (0.5, 0.4, 0), (1.0, 0.4, 3), (1.5, 0.4, 0)]
    beat_a = {"kick": "x.......x.x.....", "snare": "....x.......x...", "hat": "x.x.x.x.x.x.x.xo"}
    beat_b = {"kick": "x.....x.x.x.....", "snare": "....x.......x..o", "hat": "xoxoxoxoxoxoxoxo"}
    # 0-3: the riff: brass hits over bass and drums
    intro = [dict(notes=[], chords=c) for c in ([(0, 4)], [(3, 4)], [(4, 4)], [(0, 2), (4, 2)])]
    ch = place_chords(s, 0, intro)
    stabs(s, "brass", "brass", ch, 65, offsets=(0, 0.75, 1.5, 2.5, 3.0), length=0.3, vel=0.7, n=3)
    bassline(s, "bass", "bass_pluck", ch, eights)
    s.drums("drums", 0, beat_a, bars=4, pans={"hat": 0.3})
    # 4-11: the tune on accordion with uke
    ch = place_chords(s, 4, CAY_A)
    melody(s, "lead", "reed", 4, CAY_A, octave=1, vel=0.85, legato=0.85)
    strum(s, "comp", "uke", ch, 65, pattern="x.xu.uxu", vel=0.55, pan=0.3)
    bassline(s, "bass", "bass_pluck", ch, eights)
    s.drums("drums", 4, beat_a, bars=8, pans={"hat": 0.3})
    s.drums("perc", 4, {"tambourine": "....x.......x..."}, bars=8, pans={"tambourine": -0.4})
    # 12-19: brass takes it, the whistle an octave up, pizzicato underneath
    ch = place_chords(s, 12, CAY_A)
    melody(s, "brass", "brass", 12, CAY_A, octave=0, vel=0.85, legato=0.88)
    melody(s, "whistle", "whistle", 12, CAY_A, octave=1, vel=0.45)
    arp(s, "pizz", "pizz", ch, 77, step=0.25, pattern=(0, 2, 1, 2), vel=0.55, pan=-0.35)
    strum(s, "comp", "uke", ch, 65, pattern="x.xu.uxu", vel=0.5, pan=0.3)
    bassline(s, "bass", "bass_pluck", ch, eights)
    s.drums("drums", 12, beat_b, bars=8, pans={"hat": 0.3})
    s.drums("perc", 12, {"tambourine": "..x...x...x...x."}, bars=8, pans={"tambourine": -0.4})
    # 20-27: B on accordion, brass a third below, strings
    ch = place_chords(s, 20, CAY_B)
    melody(s, "lead", "reed", 20, CAY_B, octave=1, vel=0.85, legato=0.88)
    melody(s, "brass", "horn", 20, CAY_B, octave=0, vel=0.6, transpose=-2)
    pads(s, "pad", "strings", ch, 65, vel=0.5)
    strum(s, "comp", "uke", ch, 65, pattern="x.xu.uxu", vel=0.5, pan=0.3)
    bassline(s, "bass", "bass_pluck", ch, eights)
    s.drums("drums", 20, beat_a, bars=8, pans={"hat": 0.3})
    # 28-31: the break: toms and the riff, building
    ch = place_chords(s, 28, intro)
    stabs(s, "brass", "brass", ch, 65, offsets=(0, 0.75, 1.5, 2.5, 3.0), length=0.3, vel=0.75, n=3)
    bassline(s, "bass", "bass_pluck", ch, eights)
    for b in range(28, 31):
        s.drums("drums", b, {"kick": "x.......x.......", "tom": "..x..x....x..x.x"},
                pitches={"tom": 50})
    s.drums("drums", 31, {"snare": "x.x.x.x.xxxxxxxx", "kick": "x...x...x...x..."})
    s.add("perc", "swell", 31 * 4, 4, 60, 0.6)
    # 32-39: B with everything
    ch = place_chords(s, 32, CAY_B)
    melody(s, "brass", "brass", 32, CAY_B, octave=0, vel=0.9, legato=0.9)
    melody(s, "lead", "reed", 32, CAY_B, octave=1, vel=0.6, legato=0.88, transpose=-2)
    melody(s, "whistle", "whistle", 32, CAY_B, octave=1, vel=0.4)
    arp(s, "pizz", "pizz", ch, 77, step=0.25, pattern=(0, 2, 1, 2), vel=0.5, pan=-0.35)
    pads(s, "pad", "strings", ch, 65, vel=0.5)
    bassline(s, "bass", "bass_pluck", ch, eights)
    s.drums("drums", 32, beat_b, bars=8, pans={"hat": 0.3})
    s.drums("perc", 32, {"tambourine": "..x...x...x...x."}, bars=8, pans={"tambourine": -0.4})
    for b in (0, 4, 12, 20, 32):
        s.add("perc", "crash", b * 4, 1, 60, 0.4, 0.35)
    return s


def _drips(s, bar, bars, density=0.5, vel=0.4):
    pent = (0, 2, 3, 4, 6)  # degrees of the minor pentatonic
    r = s.rng
    for b in range(bar, bar + bars):
        for step in range(8):
            if r.random() < density:
                deg = pent[int(r.integers(0, 5))] + 7 * int(r.integers(0, 2))
                beat = b * s.bpb + step * 0.5 + 0.25 * int(r.integers(0, 2))
                s.add("drips", "drip" if r.random() < 0.6 else "musicbox", beat, 0.3, s.pitch(deg, 1),
                      vel * (0.5 + 0.5 * r.random()), float(r.uniform(-0.7, 0.7)))


def blackwater_grotto():
    """1.3: night in the corsairs' sea cave. The theme slowed, minor and quiet: celesta and drips over a drone."""
    s = Song("driftwood_3_blackwater_grotto", bpm=76, bars=28, key=62, scale=MINOR, reverb=3.2, damp=0.6,
             loudness=-19.0)
    s.bus("lead", gain=0.9, rev=0.4, delay=(0.75, 0.35, 0.3))
    s.bus("reed", gain=0.7, rev=0.35, lp=2500)
    s.bus("harp", gain=1.1, rev=0.35)
    s.bus("drips", gain=0.45, rev=0.5, delay=(0.75, 0.45, 0.45))
    s.bus("drone", gain=0.5, rev=0.3, width=0.5)
    s.bus("pad", gain=0.28, rev=0.45, width=0.5)
    s.bus("bass", gain=1.8, rev=0.1, lp=900)
    s.bus("pulse", gain=0.65, rev=0.15, lp=500)
    s.bus("perc", gain=0.35, rev=0.3)
    for b in range(0, 28, 4):
        for deg in (0, 4):
            s.add("drone", "drone", b * 4, 16, s.pitch(deg, -2), 0.55)
    for b in range(28):
        s.drums("pulse", b, {"kick_soft": "x..x............"}, vel=0.7 if b % 2 == 0 else 0.5)
    _drips(s, 0, 28, density=0.28)
    # 4-11: the theme's first half at half speed on celesta, harp under it
    ch = place_chords(s, 4, CAY_A[:4], quality=minor_v, stretch=2)
    melody(s, "lead", "celesta", 4, CAY_A[:4], octave=1, vel=0.75, stretch=2)
    arp(s, "harp", "harp", ch, 62, step=0.5, pattern=(0, 1, 2, 4, 3, 2, 1, 2), vel=0.45, pan=-0.3)
    bassline(s, "bass", "upright", ch, [(0, 3, 0), (3, 1, 2)], octave=-2, vel=0.7)
    # 12-19: its second half on a muted accordion, low strings
    ch = place_chords(s, 12, CAY_A[4:], quality=minor_v, stretch=2)
    melody(s, "reed", "reed", 12, CAY_A[4:], octave=1, vel=0.7, stretch=2, legato=0.95)
    pads(s, "pad", "darkpad", ch, 57, vel=0.6)
    bassline(s, "bass", "upright", ch, [(0, 3, 0), (3, 1, 2)], octave=-2, vel=0.7)
    s.drums("perc", 12, {"brush": "....x.......x..."}, bars=8, vel=0.6)
    # 20-27: B's first half on a cold flute; toms gather before the loop starts again
    ch = place_chords(s, 20, CAY_B[:4], quality=minor_v, stretch=2)
    melody(s, "lead", "flute", 20, CAY_B[:4], octave=1, vel=0.6, stretch=2, legato=0.97)
    arp(s, "harp", "harp", ch, 62, step=0.5, pattern=(0, 1, 2, 4, 3, 2, 1, 2), vel=0.4, pan=0.3)
    pads(s, "pad", "darkpad", ch, 57, vel=0.5)
    bassline(s, "bass", "upright", ch, [(0, 3, 0), (3, 1, 2)], octave=-2, vel=0.7)
    s.drums("perc", 26, {"tom": "x.......x...x.x."}, bars=2, pitches={"tom": 45}, vel=0.6)
    s.add("perc", "swell", 27 * 4, 4, 60, 0.4, lo=150, hi=3000)
    return s


def smugglers_run():
    """1.4 (optional): the drowned tavern. A slow, swung tavern tune heard through water; quieter than the rest."""
    s = Song("driftwood_4_smugglers_run", bpm=68, bars=24, key=55, scale=MINOR, swing=0.7, reverb=2.6, damp=0.7,
             loudness=-21.0)
    s.bus("lead", gain=0.85, rev=0.35, lp=2200, delay=(1.5, 0.3, 0.2))
    s.bus("keys", gain=0.5, rev=0.35, lp=2600)
    s.bus("box", gain=0.6, rev=0.45, delay=(0.75, 0.4, 0.3))
    s.bus("pad", gain=0.25, rev=0.4, lp=1500, width=0.5)
    s.bus("bass", gain=0.75, rev=0.1, lp=900)
    s.bus("drums", gain=0.45, rev=0.2, lp=5000)
    s.bus("drips", gain=0.35, rev=0.5, delay=(0.75, 0.45, 0.45))
    walk = [(0, 0.9, 0), (1, 0.9, 1), (2, 0.9, 2), (3, 0.9, 1)]
    # 0-7: the tune on a far-off accordion
    ch = place_chords(s, 0, CAY_A, quality=minor_v)
    melody(s, "lead", "reed", 0, CAY_A, octave=1, vel=0.75, legato=0.9, tremolo=0.3)
    stabs(s, "keys", "softpiano", ch, 62, offsets=(1, 3), length=0.6, vel=0.45)
    bassline(s, "bass", "upright", ch, [(0, 1.8, 0), (2, 1.8, 2)], octave=-1)
    # 8-15: B on piano, walking bass
    ch = place_chords(s, 8, CAY_B, quality=minor_v)
    melody(s, "keys", "softpiano", 8, CAY_B, octave=1, vel=0.7)
    pads(s, "pad", "warmpad", ch, 58, vel=0.45)
    bassline(s, "bass", "upright", ch, walk, octave=-1)
    # 16-23: the tune's echo on a music box, the accordion holding chords
    ch = place_chords(s, 16, CAY_A, quality=minor_v)
    melody(s, "box", "musicbox", 16, CAY_A, octave=2, vel=0.6)
    pads(s, "lead", "reed", ch, 62, vel=0.35, legato=0.95, tremolo=0.3)
    bassline(s, "bass", "upright", ch, walk, octave=-1)
    for b in range(24):
        s.drums("drums", b, {"brush": "....x.......x...", "rim": "x.......x......."},
                pitches={"rim": 79}, vel=0.6)
    _drips(s, 0, 24, density=0.12, vel=0.35)
    return s


def victory():
    """The world's end: a bright fanfare on pans and brass with a conga roll."""
    s = Song("driftwood_victory", bpm=120, bars=3, key=62, scale=MAJOR, loop=False, tail=3.5, reverb=1.8,
             loudness=-15.0)
    s.bus("lead", gain=1.0, rev=0.25)
    s.bus("brass", gain=0.6, rev=0.25)
    s.bus("pad", gain=0.4, rev=0.35, width=0.4)
    s.bus("bass", gain=0.8, rev=0.05)
    s.bus("perc", gain=0.7, rev=0.15)
    tune = [dict(notes=[(-3, .5), (0, .5), (2, 1), (4, .5), (2, .5), (4, 1)], chords=[(0, 2), (3, 2)]),
            dict(notes=[(5, .5), (4, .5), (5, .5), (6, .5), (7, 2)], chords=[(4, 2), (0, 2)]),
            dict(notes=[(None, 4)], chords=[(0, 4)])]
    ch = place_chords(s, 0, tune)
    melody(s, "lead", "steelpan", 0, tune, octave=1, vel=0.9)
    melody(s, "brass", "brass", 0, tune, octave=0, vel=0.8)
    for p in s.voicing(0, 66, 4):
        s.add("brass", "brass", 6, 4, p, 0.75)
        s.add("pad", "strings", 6, 4, p, 0.6)
    for p in s.voicing(0, 78, 3):
        s.add("lead", "steelpan", 6, 4, p, 0.6)
    bassline(s, "bass", "bass_round", ch[:-1], [(0, 1.0, 0), (1.5, 0.45, 2)], octave=-2)
    s.add("bass", "bass_round", 6, 4, s.pitch(0, -2), 0.9)
    s.drums("perc", 0, {"conga": "x.x.xxx.x.x.xxxx"}, pitches={"conga": 62})
    s.drums("perc", 1, {"conga": "xxxxxxxxxxxxxxxx", "shaker": "xxxxxxxxxxxxxxxx"}, pitches={"conga": 57})
    s.add("perc", "crash", 6, 1, 60, 0.7)
    s.add("perc", "kick_soft", 6, 1, 60, 1.0)
    return s


TRACKS = {
    "driftwood_1_sunwreck_beach": ("1.1 Sunwreck Beach", sunwreck_beach),
    "driftwood_2_gullwing_docks": ("1.2 Gullwing Docks", gullwing_docks),
    "driftwood_3_blackwater_grotto": ("1.3 Blackwater Grotto", blackwater_grotto),
    "driftwood_4_smugglers_run": ("1.4 Smugglers' Run (optional)", smugglers_run),
    "driftwood_victory": ("Driftwood Cay's end (sting)", victory),
}
