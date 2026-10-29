# Health Ring

<img src="thumb.png" width="128" alt="Health Ring">

**A sharp, modern health meter that grows into a full ring with every health upgrade.**

Version **1.0.0** · HUD · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The health meter redrawn sharp at any resolution: a ring of segments around an emblem. Each health upgrade adds a segment, and with all of them the ring closes. Health fills the segments five times over, a colour each round (green is full, red the last); lost health flashes white and drains away, health crystals fill it back in, and a red ring pulses when health is low. Choose its corner, size and opacity.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. Off shows the game's own meter. | Off / On | On |
| **Corner** | Where the ring sits on the screen (the next free corner when another mod's HUD piece is there). | Top Left / Top Right / Bottom Left / Bottom Right | Bottom Left |
| **Size (%)** | The ring's width, as a share of the screen's height. | 12 to 40, steps of 1 | 22 |
| **Opacity (%)** | How solid the ring is: lower lets more of the game show through. | 20 to 100, steps of 5 | 70 |
| **Low Health Pulse** | A red ring pulses around the meter when a quarter of your health or less is left. | Off / On | On |
| **Next Upgrade Slot** | A faint outline shows where the next health upgrade's segment goes. | Off / On | Off |
| **Health Animation** | How fast lost health drains away and gained health fills in. Instant: no animation. | Instant / Fast / Normal / Slow | Fast |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_health_ring.nrm` from its release, [`jfg_health_ring-v1.0.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_health_ring-v1.0.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_health_ring.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
