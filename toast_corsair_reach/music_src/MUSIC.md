# Corsair Reach music

Our own synthesized music: no game audio and no samples. `python make_music.py` remakes every file the same way
each run (numpy and scipy; Blender 5.2 encodes the OGG Vorbis, 44.1 kHz stereo, 128 kbps).

- `synth.py`: the synthesizer. It has filtered wavetable oscillators, additive bells, pans and piano, plucked
  strings, noise drums, and circular reverb and delay, so a loop has no seam.
- `themes.py`: the three world themes, written in scale degrees.
- `driftwood_cay.py`, `mirefall.py`, `cinderhold.py`: each level's arrangement of its world's theme, and the
  world's sting.
- `oggtags.py`: writes the loop tags.

**Loops.** Each level track is its loop plus 4096 samples of the loop's own end before it and 8192 samples of its
start after it. It is tagged `LOOPSTART=4096` and `LOOPLENGTH=<loop length>` (in samples). The port reads these tags
(`jfg_music.cpp`): it plays the 93 ms lead-in once, then loops the exact loop, so the encoder's edges at the file's
ends never land in it. The stings play once.

| File | Level | Mood (brief) | Loop length | LOOPSTART | LOOPLENGTH |
|---|---|---|---|---|---|
| driftwood_1_sunwreck_beach.ogg | 1.1 Sunwreck Beach | noon; bright, easy: steel pan, marimba, flute, congas (D major, 112 bpm) | 85.71 s | 4096 | 3780000 |
| driftwood_2_gullwing_docks.ogg | 1.2 Gullwing Docks | golden hour; more drive: accordion, brass, backbeat (F major, 132 bpm) | 72.73 s | 4096 | 3207273 |
| driftwood_3_blackwater_grotto.ogg | 1.3 Blackwater Grotto | night cave; tense, quiet: theme in minor at half speed, celesta, drips, drone (76 bpm) | 88.42 s | 4096 | 3899368 |
| driftwood_4_smugglers_run.ogg | 1.4 Smugglers' Run (optional) | drowned tavern; darker and quieter: swung tavern tune heard through water (G minor, 68 bpm) | 84.71 s | 4096 | 3735529 |
| driftwood_victory.ogg | Driftwood Cay's end (sting) | fanfare on pans and brass | 9.5 s, once | - | - |
| mirefall_1_stiltwater_outskirts.ogg | 2.1 Stiltwater Outskirts | storm; brooding: piano ostinato, cello, strings, choir, thunder (C minor, 88 bpm) | 87.27 s | 4096 | 3848727 |
| mirefall_2_drowned_bellmarket.ogg | 2.2 Drowned Bellmarket | storm over the town: bells, oboe, harpsichord, a warm turn to major (96 bpm) | 80.00 s | 4096 | 3528000 |
| mirefall_3_the_undercistern.ogg | 2.3 The Undercistern | cold and dark; slow dread: drone, glass, drips, heartbeat (F minor, 66 bpm) | 87.27 s | 4096 | 3848727 |
| mirefall_4_stormspire.ogg | 2.4 Stormspire | the storm at its worst: string ostinato, brass, choir, taiko; climbs a tone (144 bpm) | 80.00 s | 4096 | 3528000 |
| mirefall_victory.ogg | Mirefall's end (sting) | the storm breaks: minor turning to major, bells and choir | 13.6 s, once | - | - |
| cinderhold_1_slag_flats.ogg | 3.1 Slag Flats | red dusk; heavy, driving: power chords, anvils, brass (E phrygian, 112 bpm) | 77.14 s | 4096 | 3402000 |
| cinderhold_2_the_bellows.ogg | 3.2 The Bellows | indoor heat, machines: pistons, pumping distorted bass, buzzing lead (124 bpm) | 77.42 s | 4096 | 3414194 |
| cinderhold_3_caldera_crown.ogg | 3.3 Caldera Crown (finale) | the summit arena: everything at 150 bpm; brings back the cay's and the marsh's themes | 76.80 s | 4096 | 3386880 |
| cinderhold_4_coolant_vents.ogg | 3.4 Coolant Vents (optional) | the one cool place; quiet: glass bells, pads, steam, soft pump (84 bpm) | 80.00 s | 4096 | 3528000 |
| cinderhold_victory.ogg | Cinderhold's end (sting) | the forge goes out: timpani roll, brass and choir, ending in E major | 12.5 s, once | - | - |

All 15 files come to about 14.6 MB. Peaks are at -1.5 dBFS or lower and nothing clips. Every loop's seam, decoded
from the OGG, is within the track's normal sample-to-sample movement.
