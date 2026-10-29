# Ricochet Plasma

<img src="thumb.png" width="128" alt="Ricochet Plasma">

**Charged plasma shots bounce off walls and split at every bounce.**

Version **1.0.0** · Weapons · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The plasma shotgun's charged shots ricochet and split. Instead of dying on the first wall, a ball bounces off walls, floors and ceilings, and at each bounce it splits: three pieces by default (from two up to six) fly off different ways, each smaller and weaker, and each can bounce and split again. The more you charge, the more times it bounces: none for a quick shot, up to four at full charge, which ends in a spray of small shots filling the room. A bounce also turns the shots a little toward the nearest enemy ahead. Every part can be turned up, down or off.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. Off leaves the plasma shotgun as the game made it. | Off / On | On |
| **Bounces** | How many times a fully charged shot bounces (and splits); less charged ones bounce less, a quick shot not at all. | 1 to 8, steps of 1 | 4 |
| **Split** | Each bounce splits the shot in two. Off: a bounce makes the shot bigger and stronger instead. | Off / On | On |
| **Split Pieces** | How many shots a split makes, fanned out across the split angle. Each can bounce and split again, so more pieces fill a room fast. | 2 to 6, steps of 1 | 3 |
| **Split Angle** | How wide the pieces fan out, in degrees each side of a plain bounce (the outermost pieces fly at this angle). | 5 to 60, steps of 5 | 60 |
| **Split Damage (%)** | How much of the shot's damage each piece keeps. | 20 to 100, steps of 5 | 70 |
| **Homing (%)** | How far a bounce turns the shot toward the nearest enemy ahead of it. 0: a plain bounce, as off a mirror. | 0 to 100, steps of 10 | 10 |
| **Bounce Sound** | A zap at each bounce. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_plasma_ricochet.nrm` from its release, [`jfg_plasma_ricochet-v1.0.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_plasma_ricochet-v1.0.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_plasma_ricochet.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
