# Minimap

<img src="thumb.png" width="128" alt="Minimap">

**An always-on map of the area, with you, tribals and pickups.**

Version **1.0.0** · HUD · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

A map of the area you are in, always on screen while you play: drawn from the level itself, so it works in every area, custom levels included. You are the yellow arrow, pointing where you face; enemies are red dots (turn them on in its options), tribals blue ones, pickups yellow, ammo orange, upgrades purple, health pink and tokens cyan; unopened chests and totem poles not yet touched are boxes. Choose its corner, size and opacity.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Corner** | Where the map sits on the screen (the next free corner when another mod's HUD piece is there). | Top Left / Top Right / Bottom Left / Bottom Right | Bottom Right |
| **Size (%)** | The map's size, as a share of the screen's height. | 15 to 60, steps of 1 | 30 |
| **Opacity (%)** | How solid the map is: lower lets more of the game show through. | 20 to 100, steps of 5 | 75 |
| **Enemies** | Enemies shown as red dots. Off by default, so the map doesn't give them away. | Off / On | Off |
| **Tribals** | Tribals shown as blue dots. | Off / On | On |
| **Items** | Keys, ship parts, Floyd's parts and other pickups (yellow), ammo (orange, small), upgrades (purple), chests not yet opened (yellow boxes) and totem poles (brown). | Off / On | On |
| **Health and Tokens** | Health shown as small pink dots and tokens as small cyan dots until taken. | Off / On | Off |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_minimap.nrm` from its release, [`jfg_minimap-v1.0.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_minimap-v1.0.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_minimap.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
