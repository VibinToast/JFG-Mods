# Toggle Aim

<img src="thumb.png" width="128" alt="Toggle Aim">

**Press the aim button once to aim, again to stop.**

Version **1.1.0** · Controls · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

Manual aiming without holding the button: press the aim button (N64 R, or what you bound to it) once to start aiming and again to stop. Works with every control scheme, Swap Triggers included. Aiming stops by itself when you die or leave the level, and (an option) when you jump or swim.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **Toggle Aim** | On: the aim button toggles aiming. Off: hold it, as in the original game. | Off / On | On |
| **Stop Aiming on Jump or Swim** | Aiming stops when you jump or swim, so you land or surface walking. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_aim_toggle.nrm` from its release, [`jfg_aim_toggle-v1.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_aim_toggle-v1.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_aim_toggle.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
