# Better Flamethrower

<img src="thumb.png" width="128" alt="Better Flamethrower">

**Ground fires, spreading burns and stronger flames.**

Version **1.1.0** · Weapons · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The flamethrower becomes a weapon worth carrying. A tank of fuel lasts much longer, and its flames leave big, long fires on the ground that burn anyone standing in them (enemies, Tribals and, if you choose, you) and set enemies alight. Burning enemies pass the fire to those near them, and the flames themselves hit harder. Every part can be turned up, down or off.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Fuel Use (%)** | How fast the flamethrower burns its fuel: 100 is the original game, 25 makes a tank last four times as long. | 10 to 100, steps of 5 | 25 |
| **Ground Fire** | The flames leave fires on the ground where they reach. | Off / On | On |
| **Flame Reach** | How far in front of you the flames reach, in level units: where the ground fires are left and the extra damage lands. | 60 to 400, steps of 10 | 220 |
| **Ground Fire Time (1/10 s)** | How long a ground fire burns. | 10 to 300, steps of 10 | 200 |
| **Ground Fire Size** | How big a ground fire is (and how far around it burns). 24 is the size explosions leave. | 16 to 127, steps of 4 | 40 |
| **Ground Fire Damage (% per s)** | Health a ground fire takes each second from anyone in it, in percent of one unit (100 = one unit a second). | 0 to 500, steps of 25 | 100 |
| **Fire Hurts You** | Your own ground fires hurt you too if you stand in them: a hit each second, as from an enemy's shot (at Ground Fire Damage 200 or more, two units). | Off / On | On |
| **Fire Hurts Tribals** | Ground fires and spreading flames set Tribals alight too. Careful. | Off / On | On |
| **Spreading Fire** | Enemies the flames or a fire caught burn for a while and set alight the enemies that come near them. | Off / On | On |
| **Spreading Time (s)** | How long a burning enemy can pass the fire on. | 1 to 15, steps of 1 | 3 |
| **Spreading Chance (%)** | The chance, twice a second, that a burning enemy sets those near it alight. | 0 to 100, steps of 5 | 20 |
| **Extra Flame Damage (% per s)** | Damage the flames add to what they touch, in percent of one unit each second, on top of the game's burning. | 0 to 1000, steps of 50 | 100 |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_better_flamethrower.nrm` from its release, [`jfg_better_flamethrower-v1.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_better_flamethrower-v1.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_better_flamethrower.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
