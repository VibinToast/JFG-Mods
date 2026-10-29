# Singularity

<img src="thumb.png" width="128" alt="Singularity">

**A thrown black hole that pulls enemies in, then collapses in a blast.**

Version **0.2.0** · Weapons · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

A new weapon: throw a Singularity and where it lands it tears open a black hole. For a few seconds it drags the enemies around it in: small ones fly across the ground, heavy ones only creep, and flyers are pulled down out of the air (they find their way back if they survive); those at its heart can take damage too. Then it collapses in a blast that hits what it gathered. Tribals are pulled too (an option) but never hurt by it, and nothing is pulled through walls. It sits with your other weapons (next / previous weapon), and what you carry is saved with your file; more come from enemy drops, grenade pickups, some grenade pickups turned into Singularities, and an optional recharge. Set how far it reaches, how hard it pulls, how long it lasts and how much it hurts.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Start With It** | Your hero has the Singularity from the start, with three to throw. | Off / On | On |
| **Throw Distance** | How hard you throw it: higher throws it further (30 lands a few steps away, 60 about where a grenade lands, 150 far across a clearing). | 30 to 150, steps of 5 | 100 |
| **Reach** | How far the black hole pulls from, in level units. | 200 to 1200, steps of 50 | 1000 |
| **Pull Strength** | How hard it pulls, in percent. | 20 to 300, steps of 10 | 240 |
| **Duration (1/10 s)** | How long it pulls before it collapses. | 10 to 100, steps of 5 | 20 |
| **Heart Damage** | Health a second it takes from enemies at its heart, in percent of a unit. | 0 to 500, steps of 25 | 0 |
| **Collapse Damage** | Health the collapse takes from everything it gathered (the pistol takes 1 a shot). | 1 to 40, steps of 1 | 10 |
| **Collapse Radius** | How far the collapse's blast reaches, in level units (an enemy is about 30 wide). Enemies it gathered take the full blow inside it. | 50 to 600, steps of 10 | 210 |
| **Pull Tribals** | Tribals are pulled in too (the mod never hurts them; the grenade explosion at the end hurts anything in its blast, as a grenade does). Off: Tribals stay where they are. | Off / On | On |
| **Caught Glow** | Enemies caught in its pull glow violet. | Off / On | Off |
| **Ammo: Enemy Drops** | Enemies you kill sometimes drop a Singularity cell (big ones twice as often): walk into it to take one. | Off / On | On |
| **Drop Chance (%)** | How likely a kill is to drop a cell. Shared with other mods' drops: a kill drops at most one, and from squads made bigger by More Enemies the chance is shared out over the extra enemies. | 1 to 50, steps of 1 | 8 |
| **Ammo: Grenade Pickups** | Picking up grenades or grenade ammo gives one Singularity too. | Off / On | On |
| **Ammo: Singularity Pickups (%)** | This share of the level's grenade pickups give the Singularity instead (they still look like grenades). 0: none. | 0 to 100, steps of 5 | 25 |
| **Ammo: Recharge** | One Singularity comes back by itself every so often, while you have fewer than it holds. | Off / On | Off |
| **Recharge Time (s)** | Seconds for one Singularity to come back (with Recharge on). | 5 to 180, steps of 5 | 45 |
| **Debug Line** | For testing: a line at the top left with each thrown Singularity's state. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_singularity.nrm` from its release, [`jfg_singularity-v0.2.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_singularity-v0.2.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_singularity.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `assets/`: the built models, textures and animations the mod adds to the game (made by `build_assets.py`)
- `art/`: the scripts (Blender, Python) and source pictures the assets are made from
- `concepts/`: concept sheets and notes for the design
- `sounds/`: the mod's sound effects (made by `make_sounds.py`)
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
- `jfg_sounds.json`: which sounds the mod plays or replaces
- `jfg_assets.json`: the assets the mod adds, for the port to load
- `build_assets.py`: makes `assets/` from `art/`
- `make_sounds.py`: synthesizes the sounds in `sounds/`
