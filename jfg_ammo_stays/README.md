# Ammo Stays

<img src="thumb.png" width="128" alt="Ammo Stays">

**Ammo dropped by enemies no longer disappears.**

Version **1.1.0** · Gameplay · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

Ammo that enemies drop stays where it fell instead of blinking out after a few seconds, so you can finish the fight and collect it after. The newest drops are kept (as many as you choose), so the game never runs short of memory in long fights. Drone heads can be kept the same way.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Drops Kept** | How many of the newest drops stay; older ones disappear as in the game. More than about 64 can run the game short of memory in big fights. | 8 to 128, steps of 8 | 48 |
| **Drone Heads Stay Too** | Drone heads dropped by enemies stay as well. | Off / On | On |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_ammo_stays.nrm` from its release, [`jfg_ammo_stays-v1.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_ammo_stays-v1.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_ammo_stays.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
