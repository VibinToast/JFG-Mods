# Blood

<img src="thumb.png" width="128" alt="Blood">

**Blood options: none, more, splats that stay, colours per creature, rainbow blood.**

Version **1.1.0** · Visuals · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

Blood your way. Turn blood off, spray more of it, keep splats and severed body parts where they fall, give each kind of creature its own blood colour (heroes, Tribals, insects, flyers and drones, the final boss), or turn on the game's secret rainbow blood without collecting a single drone head. Change any option in the mod's settings; changes apply at once.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **No Blood** | No blood at all, as in the Japanese version. The other options do nothing while it is on. | Off / On | Off |
| **Blood Amount (%)** | How much blood a hit sprays. 100 is the original game. | 100 to 800, steps of 10 | 200 |
| **Blood Stays** | Blood splats stay on the ground and walls instead of fading away. Leaving the level clears them. | Off / On | On |
| **Blood Splat Limit** | How many splats stay with Blood Stays on. Once reached, the oldest makes room for new blood. 64 is the original game's pool. | 64 to 4096, steps of 64 | 960 |
| **Body Parts Stay** | Severed limbs and heads stay where they fell instead of fading away (the newest 24, so the game does not run out of memory). | Off / On | On |
| **Rainbow Blood** | The game's secret rainbow blood: every drop takes a random colour. Overrides the colours below for drops. | Off / On | Off |
| **Heroes' Blood** | The colour of the heroes' (and Floyd's) blood. | Original / Red / Green / Blue / Yellow / Orange / Purple / Pink / Cyan / White / Black | Red |
| **Tribals' Blood** | The colour of the Tribals' blood. | Original / Red / Green / Blue / Yellow / Orange / Purple / Pink / Cyan / White / Black | Blue |
| **Insects' Blood** | The colour of the green-blooded creatures: the ant soldiers, the other ground insects and most bosses. | Original / Red / Green / Blue / Yellow / Orange / Purple / Pink / Cyan / White / Black | Red |
| **Flyers' and Drones' Blood** | The colour of the dark-blooded creatures: flying insects, drones and turrets. | Original / Red / Green / Blue / Yellow / Orange / Purple / Pink / Cyan / White / Black | Cyan |
| **Final Boss's Blood** | The colour of the final boss's blood. | Original / Red / Green / Blue / Yellow / Orange / Purple / Pink / Cyan / White / Black | Yellow |
| **Others' Blood** | The colour of any other creature's blood. | Original / Red / Green / Blue / Yellow / Orange / Purple / Pink / Cyan / White / Black | White |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_blood.nrm` from its release, [`jfg_blood-v1.1.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_blood-v1.1.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_blood.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
