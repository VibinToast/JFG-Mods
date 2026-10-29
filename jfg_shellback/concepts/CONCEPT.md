# Rolling Shellback: concept

A squad enemy: an armoured beetle, part armadillo and part pill bug. All art and sound is made by the scripts in
`art/` and `make_sounds.py`; nothing comes from the game. Rebuild these sheets with `art/make_concepts.py`.

- `shellback_concept.png`: the beetle in its main poses.
- `effects_concept.png`: the spine, deflect spark, dizzy stars, dust ring and every texture.

## Look
- Five banded shell plates, dark teal-bronze, a pale bronze lip on each plate's edges, light from above baked in.
- A soft amber underside that glows. A glowing amber pad on the back plate is the weak spot. When it is curled, the pad
  shows on the ball's underside, next to the tucked head.
- Six short dark legs, a small horned head with two glowing eyes and two antennae.
- Three amber spine slits on the middle plate.

## Size (game units)
About 140 long, 68 wide and 60 high when standing (the hero is about 211 tall). Curled, it is a ball of radius 38 with
its centre 38 above the floor. It faces +Y in Blender, which exports to glTF -Z (forward in the game).

## Behaviour (the mod's code, for reference)
Walks its patrol. When it sees the hero it hisses, curls into a ball and rolls at them, bouncing off walls (shots that
hit the shell spark off it). After some bounces it stops, dizzy and half open. Then it uncurls, flares its plates, fires a
fan of 3 spines, walks a little and curls up again.
