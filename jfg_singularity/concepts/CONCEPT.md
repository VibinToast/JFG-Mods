# Singularity: concept

A thrown weapon: a small core that tears open a black hole where it lands, pulls enemies in, then collapses in a blast.
All art and sound is made by the scripts in `art/` and `make_sounds.py`; nothing comes from the game. Rebuild the sheet
with `art/make_concepts.py`.

- `singularity_concept.png`: the models (the black hole and the thrown core), the HUD icon, the swirl and the collapse
  burst frames.

## Look
- A dark violet sphere at the heart, with a spinning accretion disc around it: violet and pink, white-hot near the
  middle, fading to clear at its edge. Two tilted rings give it depth.
- The thrown core: a small dark sphere with magenta cracks and a blue-violet ring.
- The HUD icon: the black hole side on, with its disc.

## Behaviour (the mod's code, for reference)
Thrown along the aim like a grenade. It opens on its first bounce, grows, spins and hums, and pulls the enemies around it
in by mass (flyers easily, heavy ones slowly, Tribals optionally). Then it collapses with the game's grenade explosion
and a blast of its own.
