# Better Floyd

<img src="thumb.png" width="128" alt="Better Floyd">

**Floyd shoots enemies, warns you of Tribals and talks; Hide Floyd.**

Version **1.2.0** · Gameplay · by VibinToast · needs Jet Force Gemini: Recompiled 1.3.0 or newer

## About

Once Floyd joins you he earns his keep: while he follows you he picks out the nearest enemy he can see in front of him and, after a moment's aim, fires his lasers at it, not always dead on, never at a Tribal (and never through one); enemies already dying on the ground he leaves alone. Choose how often he fires, how many bolts at a time, how hard they hit, how far he looks, how wide his view is, how quickly he reacts and how well he aims. Tribal Alert blinks his lights blue and he chirps while a Tribal is near, as he blinks red at an enemy. Floyd Talks has him remark on what happens: new levels, Tribals near, rescued or lost, your health and ammo running low, kill streaks and his own kills, and a quiet word when all is calm. Hide Floyd hides him, his shadow and his sounds, and stops his shooting. When a player flies Floyd, or in his own missions, he is the game's as usual.

## Options

Change them in the game's Mods menu (the mod's Configure page) or on the launcher's Mods page.

| Option | What it does | Choices | Default |
|---|---|---|---|
| **On** | The mod on or off: the mods menu's On/Off switch, which works during play too. | Off / On | On |
| **Floyd Shoots** | Floyd fires at enemies by himself while he follows you. | Off / On | On |
| **Fire Interval (1/10 s)** | Time between his volleys. | 3 to 40, steps of 1 | 15 |
| **Bolts per Volley** | How many bolts he fires at a time. | One / Two / Three | Two |
| **Bolt Damage** | Health each bolt takes (the heroes' pistol takes 1). | 1 to 10, steps of 1 | 1 |
| **Range** | How far he looks for enemies, in level units. | 200 to 1500, steps of 50 | 600 |
| **Only Fire Ahead** | He only fires at enemies in front of him, not behind him or off to the side. | Off / On | On |
| **Firing Arc (degrees)** | How wide the view in front of him is, in which he fires (with Only Fire Ahead on). | 30 to 300, steps of 10 | 120 |
| **Aim Spread** | How far off his bolts may go, in level units (an enemy is about 30 wide). 0 = every bolt dead on. | 0 to 100, steps of 5 | 60 |
| **Reaction Time (1/10 s)** | How long he watches a new target before he opens fire. | 0 to 30, steps of 1 | 12 |
| **Ignore Dying Enemies** | He leaves alone enemies lying on the ground who will die by themselves. | Off / On | On |
| **Hide Floyd** | Floyd, his shadow and his sounds are gone while he follows you (he does not shoot then). Floyd missions and a second player flying him show him as usual. | Off / On | Off |
| **Tribal Alert** | Floyd blinks blue while a Tribal is near, as he blinks red at an enemy, and chirps when he spots one. | Off / On | On |
| **Alert Range** | How near a Tribal must be for Floyd to notice it. | 200 to 2000, steps of 50 | 700 |
| **Floyd Talks** | Floyd remarks on what happens while he follows you, in a box at the bottom of the screen. | Off / On | On |
| **How Chatty** | How often he speaks: Quiet (at most every 40 s), Normal (20 s) or Chatty (10 s). Small talk comes after 4, 2 or 1 minutes of calm. | Quiet / Normal / Chatty | Normal |
| **Text Size** | The size of his speech box, in percent. | 60 to 200, steps of 10 | 100 |
| **Talk: Arrivals** | His first words once he joins you, and new levels. | Off / On | On |
| **Talk: Tribals** | A Tribal near, rescued or killed. | Off / On | On |
| **Talk: Low Health** | When your health runs low. | Off / On | On |
| **Talk: Empty Weapon** | When the weapon in your hand runs out of ammo. | Off / On | On |
| **Talk: Kills** | Your kill streaks, and his own kills. | Off / On | On |
| **Talk: Small Talk** | A remark now and then when all is calm. | Off / On | On |

## Install

- **In the game's launcher:** open **Get Mods**, pick this mod and press **Install** (it keeps it up to date).
- **By hand:** download `jfg_better_floyd.nrm` from its release, [`jfg_better_floyd-v1.2.0`](https://github.com/VibinToast/JFG-Mods/releases/tag/jfg_better_floyd-v1.2.0), and put it in the game's `mods` folder.

## Build

From this folder, as in the [collection's README](../README.md#building-a-mod):

```sh
make SYMS=/path/to/JFGRecompSyms && make nrm SYMS=/path/to/JFGRecompSyms
```

The mod is written to `build/jfg_better_floyd.nrm`.

## What's here

- `src/`: the mod's C code
- `include/`: the port's mod API headers (`jfg_api.h`, `jfg_util.h`), copied from the port
- `sounds/`: the mod's sound effects (made by `make_sounds.py`)
- `mod.toml`: the manifest: name, version, tags, options
- `Makefile`: builds the mod (`make`, then `make nrm`)
- `mod.ld`: the linker script
- `thumb.png`: the picture shown in the Mods menu and on Get Mods
- `jfg_sounds.json`: which sounds the mod plays or replaces
