# Reticle

<img src="thumb.png" width="128" alt="Reticle">

**No snapping to enemies; reticle shape, colour and size.**

Version **1.1.0** · HUD · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

Make the aiming reticle your own. Stop it from jumping onto an enemy whenever your aim passes over one, and pick another shape (a dot, a cross, a circle, corner brackets), its colour, its colour while locked on and its size. Changes in the mod's settings apply at once.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Snap to Enemies** | Off: the reticle no longer jumps onto an enemy your aim passes over; it stays where you point. Homing weapons still lock on. | Off / On | Off |
| **Shape** | The reticle's shape. Game's keeps the original reticle (colour and size then stay the game's). | Game's / Dot / Cross / Cross and Dot / Circle / Circle and Dot / Brackets | Circle and Dot |
| **Colour** | The reticle's colour. | White / Red / Green / Cyan / Yellow / Magenta / Orange | Red |
| **Locked Colour** | The reticle's colour while it is locked on a target (homing weapons, or with Snap to Enemies on). | White / Red / Green / Cyan / Yellow / Magenta / Orange | Magenta |
| **Size (%)** | The reticle's size. 100 is a small reticle; it grows with the screen's resolution. | 50 to 300, steps of 10 | 150 |
| **Dark Outline** | A dark edge around the reticle, so it shows on bright and dark ground alike. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_reticle.nrm` from its release, [`jfg_reticle-v1.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_reticle-v1.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_reticle.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
