# More Enemies

<img src="thumb.png" width="128" alt="More Enemies">

**Two or three times the enemies in every squad.**

Version **0.1.0** · Enemies, Gameplay · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

Every squad of enemies comes with more members: twice as many, three times, or anything in between. Flying enemies have their own setting. The extra enemies arrive the way the squad's own do, and a squad's door opens once all of them are down. Tribals, bosses and big enemies keep their numbers. The extra enemies save no kills, so your saves work the same at any setting: a squad you wiped out stays wiped out, and after loading, the extras come back only for the enemies still alive. A change takes effect at the next level you enter.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off (from the next level you enter). | Off / On | On |
| **Enemies (%)** | Each squad's size: 200 is twice as many, 300 three times (rounded per squad). | 100 to 300, steps of 25 | 200 |
| **Flying Enemies (%)** | Each flying squad's size (drones, sniper drones, flying insects), apart from the rest: more of them spread out along their formation, sometimes over ground you can't reach. | 100 to 300, steps of 25 | 100 |
| **Sentries Too** | Also multiply enemies that stand guard at one post. They gather in a clump there. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_more_enemies.nrm` from its release, [`jfg_more_enemies-v0.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_more_enemies-v0.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_more_enemies.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
