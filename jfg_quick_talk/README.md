# Quick Talk

<img src="thumb.png" width="128" alt="Quick Talk">

**Hint characters turn to you and talk at once: no walking up, no slow turn.**

Version **0.1.0** · Gameplay · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

The characters who give you hints no longer make a show of it. Walk up and they turn to face you at once and start talking from where they stand: no stroll round to stand in front of you, no slow turn on the spot, and no wait for their greeting before the words come up. Their talk range can be made shorter too, so you can walk past without being stopped for a chat. Characters that never move already talk face to face and work as before.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Turn Speed** | How fast a hint character turns to face you. Game's: the original slow turn. Fast: about a quarter of a second. Instant: at once. | Game's / Fast / Instant | Fast |
| **Walk Up To You** | On: they still walk round to stand in front of you first, as in the game. Off: they talk from where they are. | Off / On | Off |
| **Skip Greeting** | The words come up at once instead of after the character's greeting move. | Off / On | On |
| **Talk Range (%)** | How close you must be before a hint character talks to you. 100 is the game's range; lower means you can pass by closer without stopping. | 25 to 100, steps of 5 | 100 |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_quick_talk.nrm` from its release, [`jfg_quick_talk-v0.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_quick_talk-v0.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_quick_talk.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
