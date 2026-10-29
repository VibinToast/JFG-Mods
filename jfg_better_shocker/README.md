# Better Shocker

<img src="thumb.png" width="128" alt="Better Shocker">

**The shock arcs from enemy to enemy and stuns them.**

Version **1.1.0** · Weapons · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The shocker's lightning no longer stops at one enemy: it arcs on to the next enemy nearby, and the next, each jump a little weaker, and every enemy it reaches is stunned, shaking in place while the current drains it. Tribals are never chained. Choose how many jumps, how far they reach, how hard they hit and whether they stun.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Chain Lightning** | The shock arcs from the enemy you hit to others nearby. | Off / On | On |
| **Chain Jumps** | How many more enemies the shock can jump to. | 1 to 8, steps of 1 | 3 |
| **Jump Reach** | How far the shock can jump from one enemy to the next, in level units. | 100 to 600, steps of 25 | 350 |
| **Stun** | Enemies the shock reaches are held in place, shaking, for about two seconds while it drains them. | Off / On | On |
| **Shock Damage (% per pulse)** | Extra health each pulse takes, in percent of one unit, on top of the shocker's own. | 0 to 500, steps of 25 | 100 |
| **Chain Falloff (%)** | How much of the damage each jump keeps. | 25 to 100, steps of 5 | 70 |
| **Pulse Interval (1/10 s)** | How often the shock arcs while the beam touches an enemy. | 2 to 20, steps of 1 | 5 |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_better_shocker.nrm` from its release, [`jfg_better_shocker-v1.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_better_shocker-v1.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_better_shocker.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
