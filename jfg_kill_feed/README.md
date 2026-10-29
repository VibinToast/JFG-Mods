# Kill Feed

<img src="thumb.png" width="128" alt="Kill Feed">

**Who killed what, with which weapon: a modern kill feed at the top right.**

Version **1.0.0** · HUD · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

A feed of kills at the top right of the screen, as in arena shooters: who fired (the hero in their colour, or Floyd), the weapon's icon, and who died. Tribals lost show in a red row. Rows slide in, newest at the bottom, and fade out after a few seconds. Enemy names come from your own game, so the feed follows any mod that changes them. The weapon icons stay the game's own, so texture packs still change them. Pairs with the Health Ring and the Ammo Ring.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Size (%)** | The rows' size. | 60 to 180, steps of 10 | 100 |
| **Opacity (%)** | How solid the rows are: lower lets more of the game show through. | 20 to 100, steps of 5 | 70 |
| **Rows** | How many kills are shown at once; older ones fade out early to make room. | 1 to 8, steps of 1 | 5 |
| **Time Shown (s)** | How long each kill stays in the feed. | 2 to 15, steps of 1 | 6 |
| **Font** | Modern: the menus' font. Game: lettering after the game's own. | Modern / Game | Modern |
| **Other Kills** | Also show deaths the heroes didn't cause: a Tribal shot by an enemy, an enemy caught in a blast. | Off / On | On |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_kill_feed.nrm` from its release, [`jfg_kill_feed-v1.0.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_kill_feed-v1.0.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_kill_feed.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
