# Corsair Reach: the level kit

Everything a level's session needs that isn't about one level. Read this, then your level's file in `levels/`, and
nothing else in full. Card JFG-169.

**Read:** this file; `levels/<your level>.md`; the jfg-studio MCP's `guide` (how the tools behave). **Don't read in
full:** the old brief (JFG-Modding `Docs/GALAXY_PACK_BRIEF.md`: history, its designs are in `levels/` now), the
`design_guide` tool (its rules are below), or the other levels' scripts (search `blender/sunwreck.py` and the last
built level's script for how a helper is used; read `blender/common.py`'s docstrings).

**The owner is away until all twelve levels are done.** Don't wait for play-tests or ask the owner; choose, and
write the choice under "As built" in your level's file. Needs from JFG-Studio or jfg64 go to the **JFG-Studio Dev**
session, needs from the decomp to the **Decomp Manager** (`SendMessage`; `ListAgents` lists them); carry on with
what you can meanwhile. Don't change Studio's code. Never launch the game.

## Status

| # | Level | Built | Commit |
|---|---|---|---|
| 1.1 | `sunwreck` Sunwreck Beach | passed the owner's play-test | 6a93b33 |
| 1.2 | `gullwing` Gullwing Docks | built, checked, not play-tested | 5c3543b |
| 1.3 | `blackwater` Blackwater Grotto | built, checked, not play-tested | see git log |
| 1.4 | `smugglers` Smugglers' Run (optional) | | |
| 2.1 | `stiltwater` Stiltwater Outskirts | | |
| 2.2 | `bellmarket` Drowned Bellmarket (hub) | | |
| 2.3 | `undercistern` The Undercistern | | |
| 2.4 | `stormspire` Stormspire | | |
| 3.1 | `slagflats` Slag Flats | | |
| 3.2 | `bellows` The Bellows | | |
| 3.3 | `crown` Caldera Crown (finale) | | |
| 3.4 | `vents` Coolant Vents (optional) | | |

## The pack

- Id `toast_corsair_reach`, "Corsair Reach", 0.1.0, VibinToast, tags Levels, Enemies. Project
  `corsair_reach.jfgproj`. Positions are game units: **x east, z south (north is -z), y up**; each level's origin is
  its middle.
- Story: insect corsairs raid the Reach; their prize is the **Stormglass**, a Tribal relic that calls the weather.
  Driftwood Cay: they burnt the village and hid their plunder in a sea cave; the Stormglass is already sold.
  Mirefall: a storm engine on the lighthouse runs on it and the town is drowning. Cinderhold: the engines are forged
  in a volcano; put out the summit forge, the Crown. Tell it through the places first, then 3-6 short `jfg.message`
  lines per level (`scripts/story.lua`, player-position triggers), never game names.
- One galaxy "Corsair Reach", home `driftwood`; planets left to right at map y 300:

| Planet | Disc | Opens | Entry level |
|---|---|---|---|
| `driftwood` Driftwood Cay | sandy turquoise, x 260, radius 34 | `start` | `sunwreck` |
| `mirefall` Mirefall | slate blue, x 480, radius 30 | `{"completed": "driftwood"}` | `stiltwater` |
| `cinderhold` Cinderhold | red-black, x 700, radius 38 | `{"completed": "mirefall"}` | `slagflats` |

- **Route**: 1.1 → 1.2 → 1.3 → 2.1 → 2.2 ⇄ 2.3 → 2.4 → 3.1 → 3.2 → 3.3 → the game's usual way back (stock level 21).
  Side levels: 1.2 → 1.4 → 1.3 (its east landing); 3.2 → 3.4 → 3.3 (start point 1). Each world's last level calls
  `jfg.complete_planet` when its final gate opens and plays its sting (`jfg.music`).
- **Stats screen**: once per world, when its last exit leaves the region (one region per planet; exits keep `arg1A`
  1). Level changes inside a world show none.
- **Death** (decomp, `mainRestartAfterDeath`): costs one of the world's 2 continues and restarts the same level at the
  start point the hero came in by; with none left, back to the world's first level. Each level's entry is its
  checkpoint.
- Every level has a way back (an exit by its arrival start point), except a planet's entry level.

### Key colours (7 of 10; one door each)

| Door | Level | Colour |
|---|---|---|
| The palisade gate | 1.1 | yellow |
| The gangplank gate | 1.2 | red |
| The vault | 1.3 | purple |
| The flood gate | 2.1 | light blue |
| The outer causeway gate | 2.2 | lime |
| The inner causeway gate (key from 2.3, `key_level`) | 2.2 | blue |
| The bellows chamber door | 3.2 | tango |

Free: magenta, green, lemon.

### Game flags (11 of 25, handed out by the tools from 103; record the real one in the status of your level)

| Use | Level | Expected |
|---|---|---|
| Switch: canal winch | 1.2 | 103 |
| Switch: galleon winch | 1.3 | 104 |
| Health upgrade: strongroom | 1.4 | 105 |
| Switch: tower pulley | 2.2 | 106 |
| Health upgrade: fountain grotto | 2.2 | 107 |
| Switch: sluice valve | 2.3 | 108 |
| Switch: stairwell pulley | 2.4 | 109 |
| Switch: rail signal | 3.1 | 110 |
| Switch: crane release | 3.2 | 111 |
| Health upgrade: pump hall | 3.4 | 112 |
| Switch: rim counterweight | 3.3 | 113 |

Levels may be built out of this order, so the tools' numbers may differ: what counts is no clash (`validate`).

### Weapons the pack hands out

| Weapon | Where | Required? |
|---|---|---|
| Machine gun (2) | chests: 1.2 fish market, 2.1 landing jetty, 3.1 canyon niche | yes: before every switch of its world |
| Grenades (8) | chest in the 1.3 vault | optional (stays in the save's main game) |
| Shotgun (3) | chest in the 1.4 strongroom | optional |
| Rockets (5) | chest in the 3.4 pump hall | optional |

Ammo only for the pistol (0) and machine gun (2), plus grenade, shotgun and rocket ammo next to and after their chests.
A chest's `contents` has **its own numbering**, not the weapon's: 2 machine gun, 5 grenades, 0 shotgun, 20 rockets
(8 is cluster bombs; `describe_type chest` lists them).

### Kinds (textures drawn by our own code in `blender/kinds.py`, never the game's)

| World | Kind | Base | Look |
|---|---|---|---|
| 1 | `deckhand` | 0x78 soldier | red-and-white striped shirt, black bandana |
| 1 | `skitterer` | 0xEE beetle | sand-speckled |
| 1 | `gull_raider` | 0x54 flyer | white and grey, orange beak colour |
| 1 | `lookout` | 0x8C sniper | navy coat, gold buttons |
| 1 | `boarder` | 0x99 shielded | tan canvas, rope bands |
| 1 | `first_mate` | 0x12F captain | long red coat, gold trim |
| 1 | `cave_crab` | 0xEE beetle (0xBE if it reads poorly) | coral orange, barnacle spots |
| 1 | `vault_guard` | 0x9C big shield | black and gold |
| 1 | `drowned_crew` | 0x121 undead | seaweed green-grey |
| 2 | `slicker` | 0x78 | yellow oilskins, dark straps |
| 2 | `marsh_leech` | 0x122 bug | slimy green-brown spots |
| 2 | `storm_midge` | 0x2D flyer | slate, electric-blue stripes |
| 2 | `bog_walker` | 0x121 | peat brown, moss |
| 2 | `tower_warden` | 0x99 | rain-dark steel |
| 2 | `bell_lookout` | 0x8C | grey hood |
| 2 | `cistern_crawler` | 0xBD beetle (or 0xEF) | pale, white spots |
| 2 | `drain_rat` | a small ground base (not 0xE1: it hangs in the air) | wet grey-brown |
| 2 | `spire_captain` | 0x12F | storm-blue coat, lightning stripe |
| 2 | `engine_guard` | 0x9C | brass and black |
| 3 | `furnace_hand` | 0x78 | leather apron brown, soot |
| 3 | `ember_beetle` | 0xBE | heat pattern |
| 3 | `cinder_wasp` | 0x29 flyer | ash grey and orange |
| 3 | `forge_turret` | 0xF5 turret | soot black, glowing seams |
| 3 | `slag_gunner` | 0x143 armoured gunner (big: check `modelSize`) | black basalt, orange seams |
| 3 | `catwalk_lookout` | 0x8C | soot and goggles |
| 3 | `forgemaster` | 0x12F | obsidian and gold |
| 3 | `crown_guard` | 0x9C | molten gold |
| 3 | `vent_swarmer` | a small ground base (not 0xE1) | pale ash |
| 3 | `ash_walker` | 0x121 | ash grey, ember cracks |

Check each base with `describe_type` and `kind_slots` first; draw at each slot's exact size. Kinds' names describe a
role. Health and speed belong to the squad.

### Difficulty (set on top of the stock squad `place_squad` copies; health a multiple of stock; aim is `aimSpread`)

| | Members | Health | Aim | Dodge | Other |
|---|---|---|---|---|---|
| 1.1 | 2-3 | stock | stock + 2; lookout + 4 | stock | |
| 1.2 | 3-4 | stock | stock + 1; lookouts + 3 | stock | one patrol |
| 1.3 / 1.4 | 3-4 | x 1.1 | stock; lookouts + 2 | stock | |
| 2.1 | 3-5 | x 1.2 | stock | + 10 | two squads together at the gate |
| 2.2 / 2.3 | 4-5 | x 1.25 | stock - 1; lookouts + 1 | + 10 | |
| 2.4 | 4-5 | x 1.35 | stock - 1; lookouts stock | + 15 | lamp room squad `flags` 0x40 |
| 3.1 / 3.2 / 3.4 | 4-6 | x 1.5 | stock - 2; lookouts stock | + 20 | |
| 3.3 | 5-6 | x 1.6 | stock - 3; lookouts - 1 | + 25 | three types at once; wave 3 `flags` 0x40 |

Health and ammo after every big fight; a full health before each world's last fight.

### Mood, sky, music, weather

| Level | Light (sun / ambient) | Fog colour, near / far | Sky | Track (`music_src/`) |
|---|---|---|---|---|
| 1.1 | (1.0, 0.97, 0.9) high / (0.45, 0.55, 0.7) | (200, 220, 240), 988 / 1021 | `pack:sky/noon` | `driftwood_1_sunwreck_beach` |
| 1.2 | (1.0, 0.75, 0.45) low west / (0.35, 0.3, 0.5) | (235, 160, 130), 986 / 1020 | `pack:sky/sunset` | `driftwood_2_gullwing_docks` |
| 1.3 | moon shaft / (0.08, 0.14, 0.18) | (10, 30, 40), 986 / 1021 | own night dome (for the crack) | `driftwood_3_blackwater_grotto` |
| 1.4 | candles / dim green-grey | (30, 40, 30), 986 / 1021 | none | `driftwood_4_smugglers_run` |
| 2.1 | (0.5, 0.55, 0.6) above / (0.25, 0.3, 0.35) | (60, 70, 85), 985 / 1019 | own storm dome | `mirefall_1_stiltwater_outskirts` |
| 2.2 | as 2.1, more lanterns | as 2.1 | as 2.1 | `mirefall_2_drowned_bellmarket` |
| 2.3 | oil lamps / (0.07, 0.1, 0.16) | (15, 25, 35), 986 / 1021 | none | `mirefall_3_the_undercistern` |
| 2.4 | (0.45, 0.5, 0.6) / (0.2, 0.25, 0.32); warmer after | (55, 65, 80), 984 / 1018; then (120, 110, 100), 988 / 1021 | as 2.1 | `mirefall_4_stormspire` |
| 3.1 | (0.9, 0.35, 0.2) low / (0.2, 0.12, 0.1) | (70, 30, 20), 986 / 1020 | own dark red dome | `cinderhold_1_slag_flats` |
| 3.2 | furnaces / (0.12, 0.07, 0.06) | (50, 25, 15), 986 / 1021 | none | `cinderhold_2_the_bellows` |
| 3.3 | lava from below / (0.15, 0.06, 0.05) | (90, 25, 15), 986 / 1020; calm dark red after | as 3.1 | `cinderhold_3_caldera_crown` |
| 3.4 | coolant / (0.1, 0.12, 0.14) | white-grey steam zones | none | `cinderhold_4_coolant_vents` |

- **Skies: always the pack's own custom skybox** (owner, 2026-10-30; Studio's pack skies, 405722c), never one of the
  game's. Every level that shows the sky (all outdoor levels, and 1.3's roof crack) gets a dome drawn for its mood:
  a `blender/sky_<name>.py` script like `sky_noon.py` (gradient, clouds, sun or moon glow, distant silhouettes where
  they help: the volcano, the lighthouse), then `import_sky` and `set_level sky pack:sky/<name>`. `make_sky` (from
  colours) is only a stand-in. Reuse a dome where the table says "as". Match the fog colour to the dome's horizon.
- **Music**: `import_music` the level's track, pick it with `set_level`. Stings at each world's last gate:
  `driftwood_victory`, `mirefall_victory`, `cinderhold_victory`.
- **Weather** (Studio 3f4674d; the owner saw rain in a pack level, 2026-10-30): `set_level {"weather": "rain"}` (or
  `{"like": 42, ...}` for the game's rainy level's values) in every Mirefall level, heaviest at Stormspire. Snow
  (`"snow"`) may read as falling ash at the Crown: try it, keep it if it looks like ash. Lightning from Lua in Mirefall:
  `jfg.fog` to pale blue-white over 3 ticks and back over 20, every 20-40 s (10-20 s at Stormspire; stops when the
  engine dies).

## Binding rules (the owner's, and the play-tests')

- **No dependency** on another mod; no stock-level edits, portals or `jfg.warp`. **No game names** anywhere (project,
  README, messages, kinds, commits). **Own art only**: the game's level textures by number, our own images by our
  code; never edit or recolour the game's images. Nothing from the ROM committed: the `.glb` and `.blend` are
  gitignored and rebuilt from `blender/`.
- **Closed levels**: boundary colliders on; outer walls over 300 high or slopes over 45 degrees; no gap over 300
  outwards; high walkways with 150-high parapets and a collider to 400 over them. **No kill floors, no bottomless
  pits**: a drop lands on floor you can climb back from or water under 40 deep.
- **Any hero, pistol only, no jetpack, hover, diving or lava walking** on the required path: ramps under 30
  degrees, steps of 70, no ledge grabs, water at most 40 deep, lava never on it. Secrets say which hero they need.
- **Switches** only after a machine gun chest earlier on the required path (1.2, 2.1 and 3.1 hold them).
- **Snipers**: one-member sentries (0x8C kinds) on level floor high up, a `light` and the game's flames (0x76) beside
  each, seen before they fire, cover on the approach, never behind the player; `raycast` both ways; the sentry's
  region covers the ground it watches (members notice only a hero inside a region).
- **Squads fight on open ground with simple cover**: boulders and plain blocks about 100 tall and 80 across, one per
  member, inside the region and off its edge; regions of 4 corners. **No crates, drums, raised decks, huts, stairs or
  thin props inside a region** (ants get stuck): clutter round the edges. Pick the centre on open floor and check
  every member stands on the ground. Where a level's plan puts a squad among huts, stalls or crates, move the fight to
  open ground beside them.
- **No glow sprites (0xC8)**: `light` objects, baked colour and the game's flames (0x76).
- **No long thin floor triangles**: walkable ground on a plain 100 grid (`common.heightfield`), decks in squares of
  about 130, shallow water in pieces of 200 x 100 at most. Studio sizes the hero's collision list per level (MSR 15);
  small tiles keep the need down.
- **No hidden ground under blocks** (`skip` in `heightfield`). **No two faces in one plane** (flicker): set
  neighbouring walls apart, a decal's back 2 behind. **No water under a floor**: every water sheet inside its hollow.
- **Open water ends at rock the hero can't climb**, never an invisible wall in open water; backdrop sea to the
  horizon.
- **The 0xE1 enemy hangs in the air** on a thread: not for rooms; use a ground base.
- Lava: a surface 30 over a solid floor, banks under 40, `texscroll`, red-orange baked near it, never on the path.
- Glass cells: square openings with sills of 30 at most (`place_glass`).

## Method

1. **Script**: `blender/<level>.py` builds the level from nothing on `common.py` (`G(x, z, y)` game to Blender;
   `heightfield` with `skip` / `merge_above`; `water_surface` cut at the shore; `boulder`, `low_rock`, `decal`;
   built shapes with `block`, `sides`, `tiled`, `post`, `collider`, `water_box` (added for 1.2); `game(tex_id)` and
   `own_image` / `own_material`; `bake` with sun, ambient, lamps, `soft`, AO). Copy the shape of the last built
   level's script (`gullwing.py` for built places, `sunwreck.py` for open ground, `blackwater.py` for caves and
   tunnels: its `cave_wall`, `plane_rect` (walls with openings), `fence` (see-through rails), `rim`, `lip` with
   `caps`/`under`, `strip`, `sides` with a sloping bottom): build, bake, `jfg64.budgets`,
   export to `blender/out/<level>.glb`. Fixed seeds. Add a helper to `common.py` when two levels would need it.
2. **Run** in background Blender: `blender --background --factory-startup --addons jfg64 --python blender/<level>.py`.
3. **Studio**: `import_geometry` (first time) or `reimport_geometry`, `add_level` on planet, `set_level` (fog, sky,
   weather, music, lights), start points, objects, squads, gates, exits (`connect`), Tribals, pickups, `story.lua`.
   Kinds: add yours to `blender/kinds.py` and `make_kind`. `scripts/story.lua` beats: `start`, `box`, `near`, `flag n`
  (a switch shot), `after n` + `delay` (seconds after beat n), with `complete = planet` and `music = track` for
  a world's last level (1.3's chart beat). Reconnect the MCP server if Studio changed under you (an
   old server writes level.json back without newer fields).
4. **Textures**: 8-14 of the game's per level by role (`stock_levels`, `stock_level_textures`, `texture_sheet`;
   repeat both ways for big surfaces) plus a few own images at small power-of-two sizes.
5. **Look**: `blender/render_views.py` from eye height (55) at the start, each fight and each gate; `level_preview`
   with and without `colours`. Fix what looks wrong.

## Known tool gaps (worked round; reported to JFG-Studio Dev)

- `place_squad` reads the highest floor: it finds no cover under a roof or up a crow's nest, and can merge close
  covers into one hole. Add or split those holes by hand in the level's `objects.json`.
- Squad members, Tribals and pickups placed by `[x, z]` land on roofs, counters and nests: give `[x, y, z]` under a
  roof, and check every one in `level_preview`.
- `texscroll`'s texture index: no MCP tool; run Studio's `track_textures` by hand.
- Big water pieces are cut at the water texture's repeats (holes in the far sea): break the water grid every 6000.
- A level's collision list (polyList) is sized by Studio per level; 1.2 needed 341 on its deck (built 512).
- Water must be one grid through every hole's edges: T-junctions read as hovering water.
- A parapet's sides start at the floor, not under it, or they flicker against the wall below.
- A lookout needs its rim below its gun height: `raycast` from the lookout, not only to it.
- `texscroll` index: `jfgstudio.track_textures` in Studio's venv after `formats.load()` (1.2's water was 14; 1.3's
  water 3, falls 16).
- Under a roof (1.3): `surface_at` gives the roof as the floor, but placing by `[x, z]` takes the lowest dry floor
  with room, so it works in a cave; region corners at a wall and members spread by `place_squad` still land on the
  roof, boulder flanks, tents, crates and in the water: set every member, perch lookout and corner by `[x, y, z]`.
- Cover: Studio merges obstacles whose boxes come within about 40 (20 plus its 20 grid; chained) into one hole, and
  gives none to one touching the region's edge: model cover at least 45 apart (box to box) and 25 inside the
  region. An up-facing surface over the region (a crow's nest) is an obstacle too.
- A second `place_squad` into the same region makes a copy of the region and its holes: delete the copy and set
  the squadron's `region` to the first one's. `place_tribal` makes a 240 square region: shrink it to the room
  (cells, alcoves) by hand.
- A door in a wall: give the doorway a reveal 40 deep and stand the door in it, on a level floor 70 deep; at the
  wall's face `check_placement` measures the open floor beyond ("wider than the door"). An exit's radius must stay
  inside its room ("clipping").
- A sheet that doesn't collide (`nocollide`) beside see-through water is an import error (the segment loses its
  collision): make waterfalls a solid sheet 2 in front of the rock, with an image of our own and a texscroll.
- Solid 150 parapets hide the view at eye height: rails (posts, a rail at 150) with a collider in their line
  (`fence`). A lookout's rim over 20 blocks it firing steeply down: stand it near the rim it fires over.
- A visible grille (posts, a collider in its line) still reads as an invisible wall (warning): leave it.
- 0x0DED (water) doesn't tile: water pieces across its repeats get cut; add zero-width holes at the multiples of
  the water's `uv_size` to `water_box` (1.3's `HOLES`).
- Bake a roofed level with `shadow=0`: the roof shades everything, and an opening to the sky lets the sun through
  (1.3's moon shaft). Its sky dome shows through the opening.
- Stock squad values (health, aim) aren't in `objects.json`: read them from the ROM with Studio's
  `catalog.stock_entry` + `objects.decode_entry(..., schema 'squadron')` in its venv. Health is whole units (x 1.1
  of 3 stays 3).

## Before you finish

- `validate` with no errors (it includes the play-test geometry checks), `check_placement` clean, `level_layout` in
  the game's ranges, `geometry_info` under the limits; `play` with `launch` false to build and install.
- Your level's file: "As built" (changes from the plan and why, triangles, KB, flags and keys used).
- The **Links** of every level your exits lead to (start point numbers, where they arrive) and any TODO you leave.
- The status table above: built, commit.
- `TEST_NOTES.md`: what the owner should check in your level (untested features: flyers, non-soldier enemies,
  snipers on perches, glass, switch doors, patrols, trigger waves, weather, `key_level`).
- Commit in JFG-Mods (plain `git commit`, files by name, never push); card JFG-169's note; a short report to the
  coordinating session ("Custom galaxy mod with three themed worlds").

## Design checklist

A landmark ahead at the start and every choice; the lock seen before its key; a loop and a late shortcut; fights with
cover, a flank, enemies seen first; flyers only over open ground; health and ammo after every big fight, a quiet room
before the hardest; teach a new thing safely, then under pressure; every side room and ledge holds something; natural
edges; no softlocks; about 5-10 minutes per main level, 3-6 for an optional one.
