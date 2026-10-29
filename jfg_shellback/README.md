# Rolling Shellback

<img src="thumb.png" width="128" alt="Rolling Shellback">

**A new enemy: an armoured beetle that curls up, rolls at you and fires spines.**

Version **0.1.0** · Enemies · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

A new enemy for levels and packs to place: an armoured beetle that walks its patrol until it sees you, then hisses, curls into a ball and rolls at you, bouncing off walls. Its shell turns shots from the front and sides: hit it from behind, or with a blast. After a few bounces it stops, dizzy and open; then it uncurls, turns and fires a fan of three spines before it walks on. Its model, animations, spines and sounds are all its own.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off. | Off / On | On |
| **Health** | Each shellback's health, in units (a spine does 1). Replaces the health its squad gives it. | 1 to 20, steps of 1 | 12 |
| **Sound Volume (%)** | How loud its sounds are (all but the rolling, which is quiet already). | 0 to 100, steps of 5 | 60 |
| **Sight Range** | How near the hero must be (and in sight) for it to curl up and roll, in level units. | 200 to 1500, steps of 50 | 700 |
| **Roll Speed** | How fast it rolls, in tenths of a unit a move. | 40 to 300, steps of 10 | 170 |
| **Roll Turning** | How sharply it turns toward the hero while rolling (thousandths of the way a move). | 5 to 200, steps of 5 | 80 |
| **Bounces Before Dizzy** | Wall bounces before it stops, dizzy and open to hits. | 1 to 8, steps of 1 | 1 |
| **Dizzy Time (1/10 s)** | How long it stays dizzy. | 10 to 80, steps of 5 | 30 |
| **Rest Time (1/10 s)** | How long it walks, after losing sight of the hero, before it may attack again. | 10 to 100, steps of 5 | 40 |
| **Roll Time (1/10 s)** | How long a roll lasts at most (it stops sooner, dizzy, after its bounces). | 10 to 150, steps of 5 | 50 |
| **Pause Between Attacks (1/10 s)** | How long it stands between attacks (a roll or a fan of spines, at random). | 0 to 60, steps of 2 | 12 |
| **Ram Damage (1/10 health unit)** | Damage when a rolling shellback rams the hero, on top of the game's own touch (one unit). The spines deal 10. | 0 to 100, steps of 5 | 30 |
| **Ram Knockback** | How hard a ram knocks the hero back, in tenths of a unit a tick (the hero walks about 20). | 0 to 200, steps of 10 | 80 |
| **Spine Speed** | How fast its spines fly, in tenths of a unit a tick. | 40 to 250, steps of 10 | 120 |
| **Spine Damage** | Damage a spine does, in hundredths of a unit of health. | 25 to 400, steps of 25 | 100 |
| **Spine Spread (degrees)** | The angle between its three spines. | 5 to 45, steps of 1 | 15 |
| **Shell Armour** | While rolling, shots from the front and sides bounce off its shell; only shots from behind and blasts hurt. | Off / On | On |
| **Debug Line** | For testing: a line at the top left with the Shellbacks' state. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_shellback.nrm` from its release, [`jfg_shellback-v0.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_shellback-v0.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_shellback.nrm`.

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
