# Corsair Reach: design

The plan the levels are built from. It follows the pack brief (JFG-Modding `Docs/GALAXY_PACK_BRIEF.md`); where it
differs, the change and its reason are under "Changes from the brief". Positions are game units: **x east, z south
(north is -z), y up**; each level's origin is its middle. Sizes are x by z. Floors are the floor height. Numbers for
levels after the vertical slice are a plan: they are measured again when each level is built.

## The pack

- Id `toast_corsair_reach`, name "Corsair Reach", version 0.1.0, author VibinToast, tags Levels, Enemies.
- One galaxy, "Corsair Reach", home `driftwood`. Three planets, left to right on the map:

| Planet | Name | Disc | Opens | Entry level (all three heroes) |
|---|---|---|---|---|
| `driftwood` | Driftwood Cay | sandy turquoise, x 260, radius 34 | `start` | `sunwreck` |
| `mirefall` | Mirefall | slate blue, x 480, radius 30 | `{"completed": "driftwood"}` | `stiltwater` |
| `cinderhold` | Cinderhold | red-black, x 700, radius 38 | `{"completed": "mirefall"}` | `slagflats` |

  Routes: driftwood right to mirefall (back left), mirefall right to cinderhold (back left). All at map y 300.
- Levels (pack names; `level_<name>` in the game):

| # | Level | Name | Type (template) | Footprint | Floors | Triangles (aim) |
|---|---|---|---|---|---|---|
| 1.1 | `sunwreck` | Sunwreck Beach | outdoor, open ground round a feature, loop | 4,000 x 3,000 | -60 to 420 | 2,800 |
| 1.2 | `gullwing` | Gullwing Docks | mixed: piers, warehouse, ship; loop | 4,500 x 3,000 | -40 to 420 | 4,000 |
| 1.3 | `blackwater` | Blackwater Grotto | indoor tiered basin, descending | 3,500 x 3,000 | -100 to 400 | 4,000 |
| 1.4 | `smugglers` | Smugglers' Run (optional) | indoor tunnel network (beads) | 3,000 x 2,000 | -150 to 20 | 2,500 |
| 2.1 | `stiltwater` | Stiltwater Outskirts | outdoor branching boardwalks over water | 4,500 x 4,000 | -40 to 260 | 3,500 |
| 2.2 | `bellmarket` | Drowned Bellmarket | mixed hub and spokes, a tower | 3,800 x 3,800 | -25 to 700 | 4,000 |
| 2.3 | `undercistern` | The Undercistern | indoor corridor maze (building) | 3,000 x 3,000 | -300 to 0 | 3,500 |
| 2.4 | `stormspire` | Stormspire | vertical: causeway, tower climb | 2,800 x 2,800 | 0 to 1,200 | 3,500 |
| 3.1 | `slagflats` | Slag Flats | outdoor canyon run onto flats | 5,000 x 3,500 | 0 to 350 | 3,500 |
| 3.2 | `bellows` | The Bellows | indoor multi-floor building | 3,500 x 3,000 | 350 to 850 | 4,000 |
| 3.3 | `crown` | Caldera Crown (finale) | vertical climb, then an arena | 4,000 x 4,000 | 600 to 1,400 | 4,000 |
| 3.4 | `vents` | Coolant Vents (optional) | indoor cluster of round rooms | 2,500 x 2,500 | 350 to 500 | 2,500 |

- Route: 1.1 → 1.2 → 1.3 → 2.1 (stats screen) → 2.2 ⇄ 2.3 → 2.4 → 3.1 (stats screen) → 3.2 → 3.3 → the game's usual
  way back, stock level 21 (stats screen). Side levels: 1.2 → 1.4 → 1.3 (east landing); 3.2 → 3.4 → 3.3 (its own start).
- Every level has a way back to where the player came in (an exit by its arrival start point). Exits inside a world
  keep `arg1A` 1 but don't change region, so no stats screen; each world's last exit leaves the region and shows it.

### Key colours (7 of 10; each used by one door only)

| Door | Level | Colour |
|---|---|---|
| The palisade gate | 1.1 | yellow |
| The gangplank gate | 1.2 | red |
| The vault | 1.3 | purple |
| The flood gate | 2.1 | light blue |
| The outer causeway gate | 2.2 | lime |
| The inner causeway gate (key from 2.3) | 2.2 | blue |
| The bellows chamber door | 3.2 | tango |

Free: magenta, green, lemon.

### Game flags (11 of 25, handed out by the tools from 103)

| Use | Level | Flag (expected) |
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

### Weapons the pack hands out

| Weapon | Where | Required? |
|---|---|---|
| Machine gun (2) | chests: 1.2 fish market, 2.1 landing jetty, 3.1 canyon niche | yes (before every switch) |
| Grenades (8) | chest in the 1.3 vault | optional reward (stays in the save's main game) |
| Shotgun (3) | chest in the 1.4 strongroom | optional (stays in the save) |
| Rockets (5) | chest in the 3.4 pump hall | optional (stays in the save) |

Ammo placed is only for the pistol (0) and the machine gun (2), plus grenade, shotgun and rocket ammo next to and
after their chests.

### Kinds (reskins; textures drawn by our own code, never the game's)

| World | Kind | Base | Look |
|---|---|---|---|
| 1 | `deckhand` | 0x78 soldier | red-and-white striped shirt, black bandana |
| 1 | `skitterer` | 0xEE beetle (0xE1 hung in the air in play) | sand-speckled |
| 1 | `gull_raider` | 0x54 flyer | white and grey, orange beak colour |
| 1 | `lookout` | 0x8C sniper | navy coat, gold buttons |
| 1 | `boarder` | 0x99 shielded | tan canvas, rope bands |
| 1 | `first_mate` | 0x12F captain | long red coat, gold trim |
| 1 | `cave_crab` | 0xEE beetle (0xBE if 0xEE reads poorly) | coral orange, barnacle spots |
| 1 | `vault_guard` | 0x9C big shield | black and gold |
| 1 | `drowned_crew` | 0x121 undead | seaweed green-grey |
| 2 | `slicker` | 0x78 | yellow oilskins, dark straps |
| 2 | `marsh_leech` | 0x122 bug | slimy green-brown spots |
| 2 | `storm_midge` | 0x2D flyer | slate, electric-blue stripes |
| 2 | `bog_walker` | 0x121 | peat brown, moss |
| 2 | `tower_warden` | 0x99 | rain-dark steel |
| 2 | `bell_lookout` | 0x8C | grey hood |
| 2 | `cistern_crawler` | 0xBD beetle (or 0xEF) | pale, white spots |
| 2 | `drain_rat` | 0xE1 | wet grey-brown |
| 2 | `spire_captain` | 0x12F | storm-blue coat, lightning stripe |
| 2 | `engine_guard` | 0x9C | brass and black |
| 3 | `furnace_hand` | 0x78 | leather apron brown, soot |
| 3 | `ember_beetle` | 0xBE | heat pattern |
| 3 | `cinder_wasp` | 0x29 flyer | ash grey and orange |
| 3 | `forge_turret` | 0xF5 turret | soot black, glowing seams |
| 3 | `slag_gunner` | 0x143 armoured gunner | black basalt, orange seams |
| 3 | `catwalk_lookout` | 0x8C | soot and goggles |
| 3 | `forgemaster` | 0x12F | obsidian and gold |
| 3 | `crown_guard` | 0x9C | molten gold |
| 3 | `vent_swarmer` | 0xE1 | pale ash |
| 3 | `ash_walker` | 0x121 | ash grey, ember cracks |

Each base is checked with `describe_type` and `kind_slots` before its kind is made; textures are drawn in Python at
each slot's exact size (stripes, bandanas, spots, seams), not only `paint_kind_texture`'s patterns.

### Difficulty over the pack

Squads copy a stock squad of their base (`place_squad`); the numbers below are set on top of what it copies.
"Stock" is the copied value; health is a multiple of it; aim is `aimSpread` (lower is more accurate).

| | Members | Health | Aim (`aimSpread`) | Dodge | Other |
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

### Mood by level (sky, fog, music: the game's numbers, matched by theme; checked in game)

| Level | Light (sun / ambient) | Fog colour, near / far | Sky | Music (own track; game tune until imported) |
|---|---|---|---|---|
| 1.1 | (1.0, 0.97, 0.9) from high / (0.45, 0.55, 0.7) | pale blue (200, 220, 240), 988 / 1021 | `pack:sky/noon`: our own dome, deep blue over a pale horizon with clouds (`blender/sky_noon.py`) | `sunwreck_beach`; 4 (bright outdoor) |
| 1.2 | (1.0, 0.75, 0.45) low from the west / (0.35, 0.3, 0.5) | orange-pink (235, 160, 130), 986 / 1020 | `pack:sky/sunset`: our own golden-hour dome, its horizon the fog's colour (`blender/sky_sunset.py`; owner, 2026-10-30) | `gullwing_docks`; 5 (more drive) |
| 1.3 | moon shaft only / (0.08, 0.14, 0.18) | dark teal (10, 30, 40), 986 / 1021 | 193 (night) for the crack | `blackwater_grotto`; 12 (tense, quiet) |
| 1.4 | candles / dim green-grey | green-grey (30, 40, 30), 986 / 1021 | none (no opening) | `smugglers_run`; 16 (dark) |
| 2.1 | (0.5, 0.55, 0.6) from above / (0.25, 0.3, 0.35) | dark blue-grey (60, 70, 85), 985 / 1019 | a dark storm sky (196 or 206) | `stiltwater_outskirts`; 46 (brooding) |
| 2.2 | as 2.1, more lanterns | as 2.1 | as 2.1 | `drowned_bellmarket`; 46 |
| 2.3 | oil lamps / (0.07, 0.1, 0.16) | deep blue-green (15, 25, 35), 986 / 1021 | none | `the_undercistern`; 30 (slow dread) |
| 2.4 | (0.45, 0.5, 0.6) / (0.2, 0.25, 0.32); after the engine: warmer | blue-grey, closer (55, 65, 80), 984 / 1018; then (120, 110, 100), 988 / 1021 | as 2.1 | `stormspire`; 41 |
| 3.1 | (0.9, 0.35, 0.2) low / dark brown (0.2, 0.12, 0.1) | dark red-brown (70, 30, 20), 986 / 1020 | dark red (197 or 203) | `slag_flats`; 18 (heavy) |
| 3.2 | furnaces / (0.12, 0.07, 0.06) | smoky (50, 25, 15), 986 / 1021 | none | `the_bellows`; 31 (machines) |
| 3.3 | lava from below / (0.15, 0.06, 0.05) | red (90, 25, 15), 986 / 1020; after: calm dark red | as 3.1 | `caldera_crown`; 38 |
| 3.4 | coolant / (0.1, 0.12, 0.14) | white-grey steam zones | none | `coolant_vents`; 50 |

Music is the pack's own, one track per level (owner, 2026-10-29), composed by the music session in `music_src/`
(see `music_src/MUSIC.md`): each level plays its track (`import_music`, `set_level` music); the game tune after it is
the stand-in until the level's track is imported. Each world's last gate plays its sting from Lua (`jfg.music`:
`driftwood_victory`, `mirefall_victory`, `cinderhold_victory`). Skies are the pack's own (Studio's pack skies,
2026-10-30): a dome per mood drawn in `blender/` (`import_sky`) or from colours (`make_sky`); the game numbers in
the table are the fallback.

**Weather.** Rain in Mirefall and falling ash at the Crown need the level header's weather block. Studio writes only
its first field (`weather`, the particle count at +0xA0); the type (+0xA3: 0 snow, 1 rain), strength (+0xA4,
+0xA5) and drift (+0xA6-0xAB) stay 0, so a pack level that sets `weather` gets snow at zero strength, not rain (read
from the decomp: `level.c` calls `setupWeather` with those bytes; `weather.c` picks rain only for type 1). So
Mirefall is planned **without the game's rain**: dark blue-grey fog, wet vertex colours, scrolled water and run-off,
mist zones, rain and thunder sounds, and Lua lightning (`jfg.fog` to pale blue-white over 3 ticks, back over 20,
every 20-40 s; every 10-20 s at Stormspire). If jfgformats and Studio gain the weather fields, rain goes in with
level 42's values. Reported as a tool gap.

## Pack-wide rules kept in every level

- Closed: jfg64 boundary colliders on; outer walls over 300 high or slopes over 45 degrees; no gap over 300 outwards;
  high walkways with 150-high parapets and a collider to 400 over them. No kill floors anywhere.
- Required path walkable by any hero with the pistol: ramps under 30 degrees, steps of 70, no ledge grabs, water at
  most 40 deep, lava never on it. Secrets say which hero they need.
- A switch only after a machine gun chest on the required path before it: 1.2's chest comes before every world 1
  switch, 2.1's before world 2's, 3.1's before world 3's. A level reached only through those (1.3, 2.2-2.4, 3.2,
  3.3) needs no chest of its own; a death restarts inside the world, so the gun is never lost on the way.
- Snipers: one-member sentries (0x8C kinds) on level floor, a lantern (a `light`, flames) beside each, seen before
  they fire, cover on the approach, never behind the player; line of sight checked with `raycast` both ways. The
  sentry's region covers the ground it watches (members notice only a hero inside a region).
- Cover: modelled blocks and rocks about 100 tall and 80 across, one per squad member, inside the squad region and off
  its edge; regions of 4 corners.

**From the owner's play-tests (2026-10-30), binding for every level:**
- **Squads fight on open ground with simple cover** (boulders, plain blocks, a boat). No breakable crates or drums,
  raised decks, huts, stairs or thin props inside a squad's region: ants get stuck on them. Clutter goes round the
  edges, outside the region. Pick the squad's centre on open floor and check every member stands on the ground.
- **No glow sprites** (0xC8) anywhere: too distracting. Light with `light` objects, baked vertex colour and the game's
  flames object (0x76) for fires and torches.
- **No long thin floor triangles**: walkable ground is a plain 100 grid (`common.heightfield`, merged only on cliff tops
  over 440), decks in squares of about 130, the hull floor in 80 x 100 pieces, shallow water in pieces of 200 x 100
  at most. The game gathers every triangle near the hero into a list (level header polyList, 90 in its own levels);
  big triangles fill it and the floor drops out (decomp MSR 15). Studio sizes the list when it builds (Sunwreck 414);
  small tiles keep the need down.
- **No hidden ground under blocks**: a fall there lands inside them (`skip` in `common.heightfield`).
- **No two faces in one plane** (flicker): walls of neighbouring blocks set apart, a decal's back 2 units behind.
- **No water under a floor**: every water sheet inside its hollow, never reaching under sand or decks.
- **Natural edges the hero can't climb** where the level meets open water (a rock reef), never an invisible wall in
  open water; the backdrop sea runs out to the horizon.
- **Enemies that hang** (the 0xE1 base) are not used in open rooms; ground beetles (0xEE) instead.
- Death (read from the decomp, `mainRestartAfterDeath`): a death costs one of the world's 2 continues and restarts
  **the same level at the start point the hero came in by**; with no continues left, the hero goes back to the
  world's first level and the world's Tribals and squads reset. So each level's own entry is its checkpoint, and
  each world's levels end in their exits rather than in long returns. To be confirmed in play.

---

## World 1: Driftwood Cay (a descent through a day)

### 1.1 Sunwreck Beach (the vertical slice)

Outdoor round the beached hull, a loop. x -2,000 to 2,000, z -1,500 (north) to 1,500 (south). The sea is east, the
headland north-east, cliffs west and south.

| Area | Centre (x, z) | Size | Floor | What happens |
|---|---|---|---|---|
| A. The sandbar (start) | (350, 1,150) | 600 x 400 | 0 | start point 0 at (350, 1,250) facing north; the broken rowboat beside it; palms and a rock arch at (350, 900) framing the view of the beach, the hull and the gate's red light; no enemy in view. Message 1. |
| B. The burnt village | (-1,150, 450) | 900 x 700 | 20-60 (two low terraces) | an open square (x -1,380 to -770, z 290 to 780) with 3 boulders and an overturned boat for cover, where squad 1 fights; 4 huts round its edges (the whole one, with Tribal 1, at (-1,500, 250)); message 2 on entering |
| B-C path | (-450, 400) to (300, 300) | 250 wide | 60 → 0 | a sandy path back east to the beach, driftwood along it |
| C. The crescent beach | (700, 150), curving | 600 x 1,600 | 0 | rocks every 400-600 (cover), tide pools, driftwood; the shallows east of x 1,000 slope 0 → -60 to a reef at x 1,750 (surf `texscroll`, collider behind, sea backdrop beyond); squad 2 (gulls) halfway at (750, 100); medium health at the stern (600, -350) |
| D. The beached hull | stern (650, -450) to bow (-250, -900) | 900 x 220 | 0 → 120 | the stern breach at floor 0; the hold lit by `lightbeam`s through the planks; squad 3 at the bow end; a cargo ramp (steps of 70) up to the deck rail at 120 where the yellow key lies in an open sea chest; the captain's cabin off the hold (Tribal 2); out of the bow hole onto the dunes. Message 3 at the key. |
| E. The dunes | (-900, -850) | 1,000 x 800 | 60-140 | rolling dunes, grass tufts (`nocollide`); the camp at (-1,050, -1,000), floor 140: crates (modelled blocks), a cookfire (glow and light), 2 explosive drums; squad 4; ammo after; a path down south to the village (the loop) |
| F. The cliff path | from (-150, -1,150) to (1,350, -1,150) | 250 wide, ~1,200 long | 140 → 420 | two switchbacks, slopes under 20 degrees, rock walls on the inside, a rock lip 150 high and a collider on the outside; boulders as cover; the lookout's spire across the gap at (450, -650) after the first switchback, perch at floor 390 (about 250 over the path there); wind sound |
| G. The gate | (1,500, -1,250) | 300 x 300 | 420 | the palisade gate (key door, yellow) between two rock pillars at (1,500, -1,400), facing south; its lock light on the frame; the lookout point at the landing's east edge (railed, a view down onto the harbour backdrop); message 4 there; the exit behind the gate |
| S. The tide-pool cave (secret) | (1,250, 1,350) | 350 x 250 | -30 (water to 0) | reached by wading round the sandbar's east side (30 deep); Tribal 3, a medium health; a ledge (`ledge` top, 160 up, any hero who can grab) with an ammo crate |

- **Critical path**: A → B (fight) → C (gulls) → D (key) → E (camp) → F (lookout) → G (gate, exit).
- **Loop**: B → C → D → E → back down to B.
- **Squads** (all kinds of world 1; squads face the way the player comes in):

| # | Kind | Members | Where | Cover | Notes |
|---|---|---|---|---|---|
| 1 | deckhand | 3 | the village square | 3 boulders | smart, goes for the hero (`flags` 0x40); `aimSpread` 60; drop small health |
| 2 | gull_raider | 3 | over the beach at (680, 200), cruising 150 up | open sand | flying |
| 3 | skitterer (0xEE) | 2 | the hold's bow end, region inside the hull | none | the squadron spawns them; drop small health |
| 4 | deckhand | 3 | the camp, region 730 x 580 | 3 modelled crate stacks | smart, `flags` 0x40; `aimSpread` 60 |
| 5 | lookout | 1 | the spire's top at (1,420, 500, -1,150), facing the path | none (sentry) | `aimSpread` 90 (stock 50); its region covers the cliff path |

- **Gates**: one key door, yellow (the gate; key in the hull).
- **Tribals (3)**: the whole hut (-1,500, 250); the captain's cabin in the hull; the tide-pool cave.
- **Pickups**: ammo crates in the village (2), small health after squad 1 (drop), medium health at the stern, ammo
  after the camp, a medium health and ammo at the first switchback, a full health at the gate landing.
- **Lights**: point lights at the cookfire, the gate and the lookout's lantern; the hull's two light beams; the
  game's flames on the cookfire's logs and on the gate's two pillars; no glow sprites.
- **Sounds**: surf along the reef, wind on the cliff path, the fire's crackle.
- **Story triggers** (Lua, player position): start (on level, once); village (inside B); the key (within 120 of
  the chest); the lookout point (within 150 of the landing's east edge). Lines:
  1. "Driftwood Cay. The corsairs came in on the morning tide."
  2. "The village is burnt. Its people were taken."
  3. "Their gate key. Careless."
  4. "The harbour's theirs. Whatever they took, it's down there."
- **Exits**: the gate → 1.2's start point 0 (top of the headland stair). A way back from 1.2 arrives at a start point
  by the gate. 1.1's own way out at the start: none needed (it is the planet's entry; the map is the way back).
- **Build**: `terrain` (hills, height 110, seed fixed) for the beach and dunes, `flat` spots for A, B, E and G; the
  cliff path cut as `paths` with depth plus hand-made rock walls; the hull by hand in `bmesh` (a tilted shell, ribs as
  boxes, a plank floor, a breach and a bow hole; about 600 triangles); huts as boxes with thatch roofs; the spire and
  the arch as `rock`s stacked; the harbour and watchtower as a low-poly backdrop outside the boundary.
- **Textures** (8-14 of the game's, by role, picked from the game's bright outdoor and coastal levels with
  `stock_level_textures` and `texture_sheet`): sand floor (repeating both ways), rock wall, cliff rock, grass top,
  weathered plank, dark hull wood, thatch, water, a path. Our own images: the corsair flag (32 x 32), the warning
  sign (32 x 32).

### 1.2 Gullwing Docks

Mixed: the headland stair down into a harbour; the warehouse is indoor. x -2,250 to 2,250, z -1,500 to 1,500. The
start is on the south-west headland; the harbour gate is far north-east.

| Area | Centre | Size | Floor | What happens |
|---|---|---|---|---|
| A. The headland stair (start) | (-1,800, 1,100) | switchback ramps 300 wide | 420 → 20 | the harbour view at golden hour; message 1 |
| B. The fish market | (-1,100, 300) | 800 x 600 | 20 | stalls (counters 100 tall), crane; machine gun chest at the back of a stall facing the way in; squads 1-2 (3 deckhands + 2 boarders); patrol 3 on the promenade (a chain along the quay, 4 deckhands); health and ammo after |
| B'. The back alley | (-1,500, -50) | 200 wide | 20 | the smugglers' door (blue lantern, sign): exit to 1.4 |
| C. The canal gatehouse | (-300, 200) | canal 350 wide; bridge 250 | 20 (water -40, surface -10) | the winch on a post across the canal at (-300, 450) facing the bridge: switch → gatehouse door; message 2 when first in view |
| D. The watchtower yard | (400, -300) | 700 x 700 | 20 / 70 / 120 tiers | cargo stacks; squad 4 (3 boarders); the watchtower (600 tall) at (650, -550): lookout 5 on top (perch 500), stairs inside to the balcony at 260 (Tribal 1) |
| E. The warehouse | (-200, -900) | 1,000 x 700, 650 high | 20; loft 220 | squad 6 (4 deckhands) on the floor, lookout 7 on the loft's far end; the red key and Tribal 2 in the loft; squad 6 locks the back door (shortcut to B) |
| F. The ship | moored along (900, 600) | 800 x 200, deck 90 | 90 | gangplank gate (red key door) and ramp; squad 8 (4 deckhands) on deck with hatches, cannons and cargo as cover; lookouts 9 and 10 in the crow's nests (400), visible from the quay; the stern cabin: Tribal 3, ammo chest; message 3 on deck; the bow plank to the far pier |
| G. The harbour gate | (1,700, -1,000) | 600 x 500 | 20 | squad 11 (2 first mates + 3 deckhands: the first mates' squad locks the gate, its lock light on the frame, `cutcamera` on the cave mouth); message 4 when it opens; the exit in the cave mouth |
| S. Under the market pier (secret) | (-1,100, 750) | wading, 30 deep | -10 | smugglers' cache: Tribal 4, ammo; steps back up every 300 |
| S2. Warehouse roof (secret) | (-200, -900) | | 300 | a ledge (grab) with a medium health |

- Critical path: A → B (machine gun) → C (switch) → D → E (key) → F (ship) → G.
- Loop: B → C → D → E → back door → B.
- Tribals 4. Snipers: 4 (5, 7, 9, 10). Flags: 103 (winch).
- Lines: "The corsairs' harbour. The sun's going down; so are they." / "That winch holds the gatehouse door." /
  "Their flagship. The hold's empty: the plunder's somewhere else." / "Torches in the cliff. That's where they keep it."
- Build: piers as plank decks on six-sided pilings (cut pilings before the ship), the ship by hand, the warehouse
  with `building`; repeating planks.

### 1.3 Blackwater Grotto

Indoor tiered basin, walked down round its sides. x -1,750 to 1,750, z -1,500 to 1,500. The main cavern's roof
1,000-1,200 high, a crack letting in the moon.

| Area | Centre | Size | Floor | What happens |
|---|---|---|---|---|
| A. The torch tunnel (start) | (-1,500, -1,100) | 250 wide, 600 long | 400 → 360 | lanterns, painted marks; message 1 |
| B. The high walkway | along the north and west wall | 220 wide | 360 | railed (150 + collider); the first view: the galleon in the moon shaft, the vault door's two lock lights; message 2 |
| C. The crab ledges | (-1,300, 0) | shelves down the west wall | 260 → 160 | stalagmites 110 tall as cover; squad 1 (4 cave crabs); lookout 2 on a pillar across the water (perch 320) with a lantern; Tribal 1 in an alcove |
| D. Rope bridges and the island | island (-300, 200) | bridges 200 wide | 160 | squad 3 (2 vault guards + 3 deckhands: two squads), tents, drums; the purple key up the island's lookout stair (steps of 70 to 260); Tribal 2 in a tent; the second bridge east |
| E. The east landing | (900, 500) | 600 x 500 | 40 | health, ammo, a machine gun ammo crate; the stair back up to the walkway (loop); 1.4's arrival start point here |
| F. The galleon's gangway (switch) | (500, -100) | | 40 | the winch on the galleon's deck in view across the water: switch → hull door; message 3 when it opens |
| G. Inside the galleon | (300, -400) | corridor 220 wide, tilted under 15 degrees | 0 → 80 | squad 4 (3 deckhands + 2 first mates); lookout 5 on the broken mast top covering the landing (seen before the switch); the captain's cabin: Tribal 3; out of the stern, a stair down to the vault door |
| H. The vault | (-200, -1,000) | 700 x 600 | -100 | behind the purple key door; squad 6 (3 first mates + 2 vault guards); the grenades chest, a full health, ammo, gold (own images); 3 cells with glass (sills 30): Tribals 4-6; the trade chart (message 5, then `jfg.complete_planet("driftwood")` and message 6 when the player reaches the treasure); message 4 on entering |
| I. The sea door (exit) | (-800, -1,300) | tunnel 250 wide | -100 → 0 | to a hidden cove at dawn: the exit into 2.1's start point 0 (stats screen) |
| S. Behind the waterfall | lagoon north end | | 200 | a ledge (grab): ammo and a medium health |

- Lagoon under 40 deep, its floor joins the landing; every walkway railed.
- Tribals 6; snipers 2 (2, 5); flags 104 (galleon winch).
- Lines: "The corsairs' grotto. Mind the drop." / "A whole galleon, wedged in the rock. The vault must be past it." /
  "The winch dropped the gangway." / "Their hoard... but the Stormglass's crate is empty." / "A trade chart: sold to
  the storm-builders of Mirefall." / "Driftwood Cay is free. Mirefall appears on the map."

### 1.4 Smugglers' Run (optional)

Tunnels 200 wide, 280 high, from floor 20 down to -150. x -1,500 to 1,500, z -1,000 to 1,000.

| Area | Centre | Floor | What happens |
|---|---|---|---|
| A. The cellar stair (start) | (-1,300, -800) | 20 → -60 | message 1; the way back to 1.2's back alley |
| B. The rum cellar | (-900, -400), 500 x 400 | -60 | barrels (`damagecrate`, some drums); squad 1 (3 drowned crew); green light |
| C. The tunnels | a small loop (-400, 0) | -60 → -80 | Tribal 1 at a dead end; an ammo cache |
| D. The drowned tavern | (400, 200), 800 x 600, 650 high | -80 (water 30 deep) | tables and the bar counter as cover; squad 2 (4 drowned crew); lookout 3 on the gallery (perch 180, up a stair; Tribal 2 behind it); fog zone; message 2 |
| E. The strongroom | (1,000, 600) | -80 | seen through a square glass window (sill 30): chest (shotgun), the world's health upgrade (flag 105), Tribals 3-4 |
| F. The grotto passage (exit) | (1,300, -600) | -80 → -150 | message 3; exit into 1.3's east landing start point |

- Tribals 4; snipers 1.
- Lines: "Smugglers' tunnels. Something's still down here." / "The crew never left." / "Torchlight ahead: the grotto."

World 1 Tribals: 3 + 4 + 6 + 4 = 17.

---

## World 2: Mirefall (a hub you choose your way through)

No game rain (see Weather). Lightning from Lua in every level.

### 2.1 Stiltwater Outskirts

Outdoor boardwalks over 40-deep flood water. x -2,250 to 2,250, z -2,000 to 2,000. South to north.

| Area | Centre | Floor | What happens |
|---|---|---|---|
| A. The landing jetty (start) | (0, 1,700) | 60 | the heroes' ship, lantern post, the colony sign; the machine gun chest; the lighthouse silhouette far north (backdrop); message 1; the way back (none needed: entry level) |
| B. The reed beds | (0, 900), 1,200 x 900 | water 0, boardwalks 60 | the junction: left to the huts, right across the reeds; squad 1 (3 storm midges) over open water; the flood gate's lock light seen north |
| C. The hut cluster | (-1,300, 200), 800 x 800 | huts 120, roofs 260 | squad 2 (4 slickers, hut walls, crates, barrels); lookouts 3-4 on two roofs (one roof has stairs: Tribal 1); Tribal 2 in a hut; health; message 2 |
| D. The mud islands | (-600, -500) | 10-40 | squad 5 (4 marsh leeches on the banks); ammo and medium health on the last bank |
| E. The leaning chapel | (900, -500), nave 700 x 300, 500 high, tilted 10 degrees | 0-70 | squad 6 (3 bog walkers); the light blue key on the altar dais (candles); Tribal 3 in the bell loft up a stair; message 3 |
| F. The fishers' rest | (900, 300) | 80 | brazier, health, ammo, Tribal 4 |
| G. The flood gate | (0, -1,700), wall 600 wide | 60 | squads 7-8 (4 slickers + 3 bog walkers) on a raised platform with sandbags and carts; the light blue key door; message 4; the exit into 2.2 |
| S. Under the biggest hut | (-1,400, 400) | wading | a full health and ammo |

- Loop: B → C → D → E → F → B. Ramps out of the water every 300.
- Tribals 4; snipers 2.

### 2.2 Drowned Bellmarket (the hub)

x -1,900 to 1,900, z -1,900 to 1,900. Square in the middle, tower north-west, cistern door east, causeway north.

| Area | Centre | Floor | What happens |
|---|---|---|---|
| A. The gate arcade (start 0) | (0, 1,300) | 60 | the view of the hub; message 1; the way back to 2.1's gate |
| B. The market square | (0, 300), 1,400 x 1,200 | -25 (water 25) | stalls, the fountain; squad 1 (4 tower wardens, smart); squad 2 (4 slickers) on a patrol ring round the fountain; lookouts 3-4 on the tower's outer balconies (450 and 600) |
| C. The street loop | west (-1,300, 300), east (1,300, 300), back lane (0, -700) | 0 | squad 5 (3 bog walkers) in the west street; an open house: Tribal 1, medium health; an arcade loft: Tribal 2 |
| D. The bell tower | (-1,300, -900), 600 x 600, 900 tall | 0 / 180 / 360 / 540; bell chamber 700 | the door a switch door (the pulley over it, flag 106); squad 6 (3 slickers) on the first landing; squad 7 (2 tower wardens) on the third; window on the second: Tribal 3; the bell chamber: the lime key, Tribal 4, message 3; the rooftop walkway down to the arcade by the causeway (the shortcut) |
| E. The cistern door | (1,500, 0) | 0 | under a blue lamp: exit into 2.3 |
| F. The causeway gates | (0, -1,500) | 0 | two key doors in a short passage: outer lime, inner blue (`key_level` undercistern); squad 8 (3 tower wardens + 3 bog walkers); start point 1 here (2.3's return); message 2 on first sight; message 4 when both are open; the exit to 2.4 |
| S. The fountain's grotto | (0, 400) | wading | Tribal 5 and the world's health upgrade (flag 107) |

- Tribals 5; snipers 2.

### 2.3 The Undercistern

`building`: square rooms, right-angled corridors (200 wide, 300 high), three tiers 0 / -150 / -300.

| Area | Floor | What happens |
|---|---|---|
| A. The entry stair (start) | 0 | message 1; the way back to 2.2's cistern door |
| B. The pump gallery, 600 x 400 | 0 | squad 1 (3 cistern crawlers); the sluice door held by a valve wheel seen through bars (switch, flag 108) |
| C. The cell block | -150 | 3 cells with glass (sills 30): Tribals 1-3; squad 2 (4 marsh leeches); ammo; message 2 |
| D. The channel walks | -150 | drain rats in two packs of 3 (squads 3-4) from side tunnels; ammo at a dead end; Tribal 4 at another |
| E. The guard room | -300 | quiet: health, ammo, Tribal 5 |
| F. The great cistern, 1,200 x 1,000, 700 high | -300 (water 30) | pillars 120 across every 300; the blue key on the plinth (message 3); squad 5 (5 crawlers), squad 6 (3 bog walkers) from the far end; lookout 7 on the gallery (perch 250) with a lamp; a stair to the gallery |
| G. The return stair (exit) | -300 → 0 | into 2.2's start point 1 by the causeway gates |

- Loop: the channel walks back to the pump gallery. Tribals 5; snipers 1.

### 2.4 Stormspire

Vertical: causeway, islet, tower. x -1,400 to 1,400, z -1,400 to 1,400.

| Area | Floor | What happens |
|---|---|---|
| A. The causeway (start south) | 0 | 300 wide, 1,200 long, parapets 140 + collider; broken blocks and a cart as cover; squads 1-2 (3 storm midges each, in turn); message 1 |
| B. The keeper's islet, 900 x 900 | 40-120 | the cottage (health, ammo, Tribal 1), sheds; squad 3 (3 engine guards) locks the tower door |
| C. The inner stair, round room 500 across | 0 → 400 | squad 4 (4 slickers) on the landings; the gallery door held by a pulley across the stairwell (switch, flag 109) |
| D. The outer gallery, 220 wide | 400 → 900 | parapet 150 + collider to 1,300; balconies every half turn; squad 5 (3 storm midges) over the sea; lookouts 6-7 on balconies a turn up; squad 8 (3 tower wardens) on a balcony; Tribal 2 on a broken balcony (grab); message 2 |
| E. The keeper's floors | 900 → 1,100 | storerooms, cables; Tribal 3 in a storeroom; squads 9-10 (4 spire captains + 3 engine guards) lock the lamp room door |
| F. The lamp room, 700 across | 1,200 | the storm engine and the glowing glass (glows); squad 11 (4 engine guards, `flags` 0x40); when it dies: fog lightens, lightning stops, messages 3-5, `jfg.complete_planet("mirefall")`, the lift door opens: the exit into 3.1 (stats screen); Tribal 4 |

- Tribals 4; snipers 2.

World 2 Tribals: 4 + 5 + 5 + 4 = 18.

---

## World 3: Cinderhold (an ascent to a finale)

Lava everywhere: a surface 30 over a solid floor, banks under 40, `texscroll`, a red-orange glow baked into the
vertices near it, glows along it; never on the required path.

### 3.1 Slag Flats

Canyon run onto flats, rising 0 → 350 in three tiers. x -2,500 to 2,500, z -1,750 to 1,750; south-west to north-east.

| Area | Floor | What happens |
|---|---|---|
| A. The landing ledge (start) | 0 | the view up the valley to the volcano and the Crown (backdrop cone); message 1 |
| B. The basalt canyon, 250-350 wide, 1,200 long | 0 → 100 | basalt columns; the machine gun chest in a niche (Tribal 1 in the niche); squad 1 (4 furnace hands), squad 2 (3 ember beetles); ammo, health; a ledge with a full health (secret) |
| C. The flats, 2,000 x 1,500 | 100-200 | slag heaps every 400-600; three lava rivers 200-300 wide, railed bridges; squad 3 (3 cinder wasps); turrets 4-5 on the far banks of bridges 1-2; slag gunners 6 (2, sentries) at bridge 3; the second river also crossed round its source (the loop); Tribal 2 in a slag heap hollow; message 2 |
| D. The ore yard, 800 x 600 | 220 | rails, ore carts; office: Tribal 3; squads 7-8 (4 furnace hands + 3 ember beetles); the gate up to the rise a switch door (the rail signal on the gantry, flag 110) |
| E. The forge gate, 500 x 400 | 350 | squad 9 (2 slag gunners) locks the foundry door; braziers; `cutcamera` on it opening; message 3; the exit inside |
| S. The lava-walker's cache | off the flats | an island in a lava pool: Tribal 4 and ammo, reached only by walking the lava (Juno) |

- Tribals 4; snipers 0 (turrets and gunners instead).

### 3.2 The Bellows

`building`: ground floor 350, gallery 600, catwalks 850; rooms 700-900 high.

| Area | Floor | What happens |
|---|---|---|
| A. The loading dock (start) | 350 | crates, carts, a crane; message 1; the way back to 3.1's gate |
| B. The furnace rooms (three) | 350 | squads 1-2 (3 furnace hands each); Tribal 1 in the third; ammo |
| C. The casting hall floor, 1,400 x 900, 900 high | 350 | the molten channel, two iron bridges; turrets 3-4; lookouts 5-7 on the catwalks (perches about 500 up) under red lamps; ingot stacks and moulds as cover; squad 8 (3 forgemasters) at the stair; message 2 |
| D. The gallery offices | 600 | patrol 9 (4 furnace hands, a chain); the far door a switch door (the crane's release across the hall, flag 111); the foreman's office: the tango key, Tribal 2; the gallery squad locks a door down to the dock (shortcut) |
| E. The upper catwalks, 200 wide | 850 | railed with parapets and a collider; Tribal 3 in an alcove; the tango key door to F |
| F. The bellows chamber, 900 x 700 | 850 | the bellows (by hand); squad 10 (2 slag gunners + 4 furnace hands) locks the exit up to 3.3; Tribal 4 behind the bellows; message 3; a side door under a blue light: exit to 3.4 |
| S. Under the moulds | 350 | a crawlspace 150 high: full health, ammo |

- Tribals 4; snipers 3.

### 3.3 Caldera Crown (the finale)

x -2,000 to 2,000, z -2,000 to 2,000; floors 600 → 1,400.

| Area | Floor | What happens |
|---|---|---|
| A. The roof door (start 0) | 600 | the view down over the flats; message 1; the way back to 3.2 |
| A'. The service lift (start 1) | 600 | 3.4's arrival, beside A |
| B. The switchbacks, 250 wide, four legs | 600 → 1,000 | rock lip 150 + collider; lookouts 2-3 on outcrops a leg up with braziers; squad 4 (cinder wasps) over the face; squad 5 (ember beetles) on the landings; boulders on every leg; Tribal 1 in an alcove off leg 2 |
| C. The ash shelf, 900 x 600 | 1,000 | squad 6 (4 crown guards) round a brazier; health, ammo, Tribal 2; message 2 |
| D. The rim gate | 1,100 | a switch door held by a chain counterweight across a gap (flag 113) |
| E. The rim walk | 1,100 → 1,300 | walled; slag gunners 7 (2 sentries) on perches; squad 8 (3 cinder wasps); Tribal 3 in an alcove |
| F. The Crown, 1,400 across | 1,400 | a ring walkway 300 wide round a molten pit (shallow lava over a floor, steps out), two bridges to the island; waves on trigger zones (`trigger` 1): wave 1 at the entrance (5 furnace hands + 3 forgemasters), wave 2 at the halfway point (2 slag gunners + 4 cinder wasps), wave 3 at the bridges (5 crown guards + 3 forgemasters, locking the core door); health and ammo between; message 3 on entering. If trigger zones don't fire in a pack level: all three at once, spread round the ring |
| G. The forge core | 1,400 | Tribal 4; messages 4-5; the glow dims (Lua fog); `jfg.complete_planet("cinderhold")`; the shuttle pad door: exit to stock level 21 (stats screen) |

- Tribals 4; snipers 2.

### 3.4 Coolant Vents (optional)

Eight round chambers (radius 150-300) in a loop with two cross-links, pipes 200 wide; floors 350-500.

| Area | What happens |
|---|---|
| A. The vent hatch (start) | message 1; the way back to 3.2's side door |
| B. The chamber cluster | vent swarmer packs (squads 1-3, 4-5 each) from the pipes; ash walkers (squads 4-5) in two dead ends with Tribals 1-2; ammo in most chambers |
| C. The pump hall, 700 x 500 | squad 6 (5 ash walkers) and a swarmer pack 7; the world's health upgrade (flag 112), the rockets chest, Tribals 3-4; message 2 |
| D. The service lift (exit) | into 3.3's start point 1 |

- Tribals 4.

World 3 Tribals: 4 + 4 + 4 + 4 = 16. Pack total: 51.

---

## Untested in a pack level (for the owner to check)

Flying squads (gulls, midges, wasps), the non-soldier enemies (all but 0x78), snipers on high perches, glass cells,
switch doors, squad trigger zones (the Crown's waves), the key carried from 2.3 (`key_level`), the Lua lightning,
the stats screen's Tribal count per world, and where a death restarts (above).

## Changes from the brief

- **Rain**: not the game's rain (Studio can't write the weather block's type and strength yet); fog, sounds,
  scrolling water and Lua lightning instead. Falling ash at the Crown: same, left out.
- **Death**: the brief expected a restart at the world's first level; the code restarts the level the hero is in,
  at its entry, while continues last. The pacing keeps health generous anyway.
- 1.1 has no exit back at its start: it is the planet's entry level, reached from the map.
- 1.1 as built (vertical slice): the cliff path is three stacked legs (x -250 to 950 at z -1050, -1300, -1550),
  each a block whose wall is the next one's cliff, so it is longer than the brief's 1,200 (about 3,200 walked);
  the gate is at x 1250, z -1550, floor 420, the exit just behind it. The lookout's region covers the whole path
  (members only notice a hero inside a region). Grass tufts were dropped: decoration that isn't solid can't share a
  piece of the level with the sea. 2,882 triangles, 136 KB (over the 121 KB warning, under the buffer). Its gate's
  exit now leads into 1.2's start point 0; 1.2's way back arrives at 1.1's start point 1, by the gate (1080, 420,
  -1550), facing the gate.

### 1.2 Gullwing Docks as built (2026-10-30, not play-tested yet)

Built by `blender/gullwing.py` (by hand on `common.py`'s new `block`/`sides`/`tiled`/`post`/`collider`/`water_box`
helpers; no jfg64 `layout`/`building`), kinds `boarder` and `first_mate` in `blender/kinds.py`. **Sky: our own
sunset dome** (owner, 2026-10-30: a custom skybox, not a game sky), `blender/sky_sunset.py` → `pack:sky/sunset`:
violet overhead through rose to the fog's orange-pink at the horizon, cloud banks lit warm from below, the low sun's
disc and glow due west; the vertex colours warm the west and cool the east overhead but are white at the horizon, so
the horizon row is exactly the fog colour (235, 160, 130) all round and the haze meets the sky without a seam.
4,042 triangles, 165 KB, 7 images of our own (sail, fish sign, KEEP OUT sign, awning canvas, rope coil, flag,
shutters), 13 game textures. Fog (235, 160, 130) 986 / 1020, tune 5, music `pack:music/gullwing_docks`.

**The plan, where it differs from the table above (my choices, owner away):**

| Area | As built |
|---|---|
| A. Headland stair | x -2210..-1450, z -50..1460: start landing L0 at 420 (start point 0 at (-2040, 420, 1330), facing the harbour), leg 1 north 420 → 300, L1, leg 2 south 300 → 190, L2, leg 3 north 190 → 20 to the market. Legs 260 wide (brief 300). Parapets 45-60 high with colliders over them where the drop is to the sea. The way back to 1.1: an arch on L0's south edge (exit at (-2040, 420, 1485)) |
| B. Fish market | x -1450..-475, z -50..700, floor 20. Machine gun chest in a stall at the way in (-1392, 160), facing west, outside the squads' region. 3 deckhands + 2 boarders share one region (x -1290..-560, z 30..610) with 5 fish counters (105 tall) as cover; patrol of 4 deckhands on the promenade (z 645, x -1380 → -620, there and back). Awning counters along the houses (outside the region). Crane on the canal bank |
| B'. Back alley | x -1450..-1250, z -450..-50: the smugglers' door (an unlocked wooden door in a 160 doorway, KEEP OUT sign, blue lantern), the exit behind it |
| S. Smugglers' cache | the market pier is raised (deck at 110, a ramp up from the promenade) so the cache fits under it: a dry stone landing at 0 under the pier's end, Tribal 4 and ammo; steps out of the water every ~300 |
| C. Canal and gatehouse | canal x -475..-125 (water -40/-10), stone bridge z 75..325 into the gatehouse (x -175..25) in the **dividing wall** (x -125..-75, 320 high), which splits the harbour west/east: the gatehouse door (switch, flag 103) is the only way east. The winch on a post in the canal at (-300, 230, 450), lamp over it, facing the bridge |
| D. Yard | tiers 20 (the yard, x -75..560), 70 (loading terrace) and 120 (tower terrace), joined by ramps; 3 boarders among 3 cargo stacks. Watchtower x 600..800, z -950..-750, top 500 (a curb, not a parapet: the lookout fires over it). The brief's inside stair became a wooden ramp up the tower's front to a landing at 200 (brief 260) and a door into a room at 200: Tribal 1 and a clip |
| E. Warehouse | x -700..300, z -1300..-550, eave 600, gable to 720; loft along the north wall at 220 (rail 30 high), stair up the east wall; front doorway (no door) into the yard, back door to the lane west, kept locked by its 4 deckhands (door id 2, lock light beside it in the lane). Red key and Tribal 2 in the loft, lookout 7 at the loft's west end. S2: a lean-to in the canal street with a ledge top at 170 and a medium health |
| F. Ship | hull x 450..1240, z 410..650, deck 90, **moored flush against the quay** (no water gap to fall into), a blunt bow butting the causeway. Boarding gate on the quay side (posts + lintel, red key door), gangplank with a landing at its top. Colliders over both bulwarks (north 150 → 300, low enough to shoot the nests over from the quay; south 150 → 450). Masts at x 690 and 1150, nests at 400 (12-high rims), lookouts 9 and 10; sails braced 30° so they show from the quay. 4 deckhands on deck, cover: the two mast feet and two cargo stacks. Stern cabin: Tribal 3 and ammo |
| F'. Bow causeway | from the bow (90) through a postern in the **fort wall** (x 1400..1460, 450 high) down to the far pier (20), railed with colliders |
| G. Harbour gate | far pier x 1460..1950 (full health and ammo), storehouse east of it; gate between two towers in the north cliff at (1900, -1298), fires on the towers; 2 first mates (door id 3: they keep the gate locked, lock light by the east tower, cutcamera 1 at (1900, 170, -880)) + 3 deckhands, one region, 5 stone blocks as cover. Tunnel behind with fires, the exit at (1900, 20, -1440) |

**Closed:** the west and east halves are split by walls the hero can't climb (the dividing wall 320, the sea walls
300, the fort wall 450, the sheds' eaves 450, the warehouse's 600); every wall top within a jump is 250 or more over
the floor beside it; the ship and causeway have colliders over their rails. Boundary colliders behind the cliffs and
buildings only (never over open water). Water everywhere 30 deep, with steps out.

**Difficulty:** deckhands and boarders `aimSpread` 52 (1.1: 60), lookouts 75 (1.1: 90), smart deckhand squads
`flags` 729 (0x40 set). Drops: small and medium health. Snipers: 4 (tower, loft, two nests).

**Exits (TODO for the next sessions):**
- **TODO 1.3 (Blackwater Grotto):** the exit `todo_1_3__exit_into_the_grotto...` at (1900, 20, -1440) in the cave
  mouth behind the harbour gate leads to the game's way back (stock level 21) for now. When 1.3 exists: point it at
  `pack:level/blackwater` start point 0 (`update_object` target and `startPoint`), rename it, and give 1.3 its way
  back to a new start point in 1.2 in the cave mouth (about (1900, 20, -1350), facing south).
- **TODO 1.4 (Smugglers' Run):** the exit `todo_1_4__exit_into_the_smugglers_tunnels...` at (-1350, 20, -498)
  behind the smugglers' door leads to stock level 21 for now. When 1.4 exists: point it at its start point 0, and
  1.4's way back to a new start point in the back alley (about (-1350, 20, -380), facing south).

**Tool gaps met (reported, worked round):** place_squad found no cover under a roof or a crow's nest (it reads
the highest floor): the warehouse's 4 crates and the ship's 2 mast feet got their holes by hand in `objects.json`; it
also merged three close covers at the gate into one big hole (split by hand). Squad members and Tribals placed by
[x, z] land on roofs, counters and nests: every one was moved by hand. The texscroll's water index (14) came from
Studio's `track_textures` run by hand (no MCP tool). The far sea had holes where the importer cut big water pieces
at the water texture's repeats: its grid now breaks every 6000 (the repeat), so nothing is cut.
