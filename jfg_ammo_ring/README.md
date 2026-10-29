# Ammo Ring

<img src="thumb.png" width="128" alt="Ammo Ring">

**A sharp, modern weapon panel: an ammo ring, a weapon fan, a Tribal badge and a pick-up feed.**

Version **1.0.0** · HUD · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The weapon panel redrawn sharp at any resolution, to pair with the Health Ring: your ammo as a ring around the weapon's icon, the charge bar as a thin arc inside it and the count at its foot. Change weapons and the ones you own fan out beside it with the new one's name; save a Tribal and a badge shows how many are saved and left; pick-ups (ammo, keys, parts) come up as a short feed under it. The weapon icons stay the game's own, so texture packs still change them.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. Off shows the game's own panel. | Off / On | On |
| **Size (%)** | The ring's width, as a share of the screen's height. | 14 to 40, steps of 1 | 24 |
| **Opacity (%)** | How solid the panel is: lower lets more of the game show through. | 20 to 100, steps of 5 | 70 |
| **Font** | Modern: the menus' font. Game: lettering after the game's own. | Modern / Game | Game |
| **Pick-up Feed** | Pick-ups (ammo, keys, parts) shown as short lines under the ring, with the ammo gained. | Off / On | On |
| **Tribal Badge** | When a Tribal is saved or lost, a badge under the ring shows how many are saved, lost and left. | Off / On | On |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_ammo_ring.nrm` from its release, [`jfg_ammo_ring-v1.0.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_ammo_ring-v1.0.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_ammo_ring.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
