# Concussion Cannon: concept

A held weapon that charges like the plasma shotgun and lets go a cone of force. All art and sound is made by the scripts
in `art/` and `make_sounds.py`; nothing comes from the game. Rebuild the sheet with `art/make_concepts.py`.

- `concussion_cannon_first_look.jpg`: the first render of the cannon, its wave (still a cone then) and the effects.
- `concussion_cannon_concept.png`: the cannon close up, the models as they ship (the wave is a ring now), the HUD icon
  and every texture.

## Look
- A gunmetal cannon with blue bands: a grip, a glowing blue core, a stack of ribbed coils, and a flared muzzle.
- The blast: two thin rings of blue force with a white-hot rim, see-through in the middle, that spread and fade.
- The charge orb at the muzzle (a bright core in a crackling glow shell) and the spiky wall-slam impact.
- The HUD icon: the cannon side on with two shock arcs leaving the muzzle.

## Size
Held in the hand like the stock guns: the grip at the hand joint and the barrel toward (+X, -Y, -Z), about 70 units from
grip to muzzle, with a `barrel` point at the muzzle.

## Behaviour (the mod's code, for reference)
Hold to charge, let go to fire. Enemies in the cone are flung back by mass (flyers spin away), and slam into walls for
damage. The hero is pushed back and the screen shakes.
