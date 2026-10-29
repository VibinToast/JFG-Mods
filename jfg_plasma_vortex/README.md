# Plasma Vortex

<img src="thumb.png" width="128" alt="Plasma Vortex">

**Charged plasma shots pull enemies in, then burst.**

Version **1.0.0** · Weapons · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The plasma shotgun becomes a vortex gun. A charged shot slows to a hover and drags the enemies around it in: they slide toward the ball, glowing blue, bunch up around it and take damage while they are close. When the ball's time runs out or it hits a wall, it bursts in a plasma flash that hits everything it gathered, hard enough to blow the weak ones apart. The more you charge, the further it reaches and the harder it pulls. Tribals are never pulled or hurt by it, and nothing is pulled through walls. Every part can be turned up, down or off.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. Off leaves the plasma shotgun as the game made it. | Off / On | Off |
| **Charge Needed** | How charged a shot must be to become a vortex: 1 every shot, 4 only a full charge. | 1 to 4, steps of 1 | 2 |
| **Hover Time (s)** | A vortex slows to a stop and hangs in the air this long before it bursts, pulling all the while. 0: it flies on as the game's shot does and bursts where it ends. | 0 to 3, steps of 0.5 | 1 |
| **Pull Reach** | How far a fully charged shot pulls from, in the game's units (a less charged one reaches less). | 100 to 600, steps of 25 | 300 |
| **Pull Strength (%)** | How hard enemies are dragged in. | 25 to 400, steps of 25 | 200 |
| **Vortex Damage (%)** | Damage to enemies close to the ball while it flies, as a share of one unit of health a second. | 0 to 500, steps of 25 | 100 |
| **Burst Damage** | The burst's blow at full charge, in units of health (an ant soldier has a few). | 0 to 20, steps of 1 | 6 |
| **Stun** | Caught enemies are stunned (shaking, held by the current) instead of just turning on you. | Off / On | Off |
| **Blue Glow** | Caught enemies glow blue. | Off / On | On |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_plasma_vortex.nrm` from its release, [`jfg_plasma_vortex-v1.0.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_plasma_vortex-v1.0.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_plasma_vortex.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
