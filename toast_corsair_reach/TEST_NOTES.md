# Corsair Reach: what to check in play

The owner plays every level once all twelve are built. Each level's session adds what it couldn't test itself: it
checks its level with Studio (`validate`, `check_placement`, `level_layout`, the previews) and with renders from the
hero's eye height, but no one has played it.

## 1.2 Gullwing Docks (JFG-169, built 2026-10-30, not played)

Start it from 1.1's gate, or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_gullwing --start-point 0`.

**The route:** the headland stair down to the fish market (machine gun chest at the way in) → fight → the canal
bridge: shoot the winch on its post in the canal → gatehouse door → the yard (boarders, the tower lookout) → the
warehouse: fight, then up the loft stair for the red key → back door opens onto the lane (the loop to the market) →
the quay: shoot the two nest lookouts → the boarding gate (red key) → the deck fight → the stern cabin → the bow
causeway through the fort wall → the far pier → the harbour gate fight → the gate opens, camera shot → the cave mouth
exit.

**Untested in a pack level (please look):**
- **The switch door**: the winch (the game's shootable switch) on the post at (-300, 450) opens the gatehouse door,
  sets game flag 103 and should stay open after a reload or a death.
- **Snipers on perches (4)**: the tower top (500), the warehouse loft (220), and the two crow's nests (400). Do they
  fire over the low rims, can they be hit back, are they seen before they fire (each has a lantern)?
- **The colliders over the ship's bulwarks**: do they stop bullets? The north one stops at 300 so the nests can be
  shot from the quay; if colliders block shots, the nests can still be shot from the yard side, and the lookouts may
  not be able to hit a hero close under the hull.
- **The patrol**: 4 deckhands walking the promenade (z 645) there and back. Do they join the market fight?
- **Boarders (shielded ants) and first mates (captains)**: the pack's first use of both bases and kinds.
- **Squad-locked doors**: the warehouse back door (its 4 deckhands) and the harbour gate (the 2 first mates; the 3
  deckhands beside them don't lock it). Their lock lights stand on the floor beside the doors.
- **The cutscene camera** when the harbour gate opens (from the gate fight's middle, looking at the gate).
- **Hand-made cover holes**: the warehouse crates and the ship's mast feet (Studio missed them under the roof and
  nests). Do the squads move between cover there, or get stuck?
- **The gangplank and boarding gate**: the door stands on the deck edge at a landing at the top of the gangplank.
  Does it open with the red key and close the gap fully?
- **Falling in the water**: everywhere is 30 deep with steps out. Can any hero get stuck in the water, or climb out
  anywhere that skips a gate (round the ship's stern or bow, onto the far pier from the water)?
- **Wall tops**: the dividing wall (320), sea walls (300), fort wall (450). Can any hero climb onto one and walk
  round a gate?
- **The lean-to ledge** in the canal street (top 170, a medium health): can a hero grab it?
- **The smugglers' cache** under the market pier: the deck is at 110, the landing at 0. Room to walk under?
- **Polylist**: the build raised it to 512 (the deck needs up to 341). Any falling through the deck?
- **The start view**: parapets 45 high at the start landing. Does the harbour show at once?

**Exits:** the cave mouth leads to 1.3, the smugglers' door (`into_the_smugglers__tunnels1`, back alley) to 1.4's
start point 0; 1.4's way back arrives at start point 2 in the back alley, facing south. The way back at the start
(the arch) leads to 1.1's gate.

## 1.3 Blackwater Grotto (JFG-169, built 2026-10-30, not played)

Start it from 1.2's cave mouth (past the harbour gate), or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_blackwater --start-point 0`.
1.4's arrival is start point 1 (the smugglers' passage off the east landing).

**The route:** the torch tunnel → the walkway (the galleon under the moon shaft; the vault door behind bars) → down
the west wall to the crab ledges (4 cave crabs; the lookout on the pillar) → bridge to the island camp (2 vault guards
and 3 deckhands) → the purple key up the lookout stair → bridge and ramp down to the east landing → the jetty: shoot
the winch on the galleon's forecastle (the crow's-nest lookout covers the landing) → hull door opens, camera shot →
the hold (3 deckhands, a first mate) → the captain's cabin → the breach into the yard (full health) → the vault door
(purple key) → the vault (3 first mates, 2 vault guards) → the grenades chest, the cells, the trade chart → the sea
door exit. The loop: the stair from the landing back up to the walkway.

**Untested in a pack level (please look):**
- **The dark:** a night cave. Is everything readable (the walkway, the ledges' edges, the hold), or is it too dark?
  The bake's ambient is already above the plan's.
- **The moon shaft:** the roof's crack over the galleon (the sky dome through it, two light beams pointing down with
  1.1's pitch, the bake brighter under it). Do the beams point down and look like moonlight?
- **The first view:** out of the tunnel, are the galleon, the moon shaft and (along the west walkway) the vault door
  behind the yard's grille all in sight over the wooden rails?
- **The grille:** posts 55 apart with colliders in their lines. Can any hero squeeze through or climb over (450 high)?
- **Cave crabs (beetles, 0xEE) and vault guards (big shields, 0x9C):** the pack's first use of both; do the crabs use
  the stalagmites, do the guards fight on the island and in the vault? Is the vault guards' shield texture right (its
  two see-through slots are ours, drawn half see-through)?
- **Snipers (2):** the pillar perch (320, rim 30) over the crab ledges and the crow's nest (480, rim 20) over the
  landing. Seen before they fire? Can they be shot back? The nest one stands at its south-east corner.
- **Shared regions:** two squads in each of three regions (island, hold, vault). Do they move between the holes?
- **The switch door:** the winch (flag 104) on the forecastle, shot from the landing or jetty: does the hull door open
  and stay open after a reload or a death? Message 3 should show when it's shot.
- **Doors in reveals:** both doors stand inside 40-deep doorways. Do they close the openings fully?
- **Glass:** three square panes (100, sills 30) in front of the cells; break them, climb in, rescue the Tribals.
- **Water:** the lagoon 30 deep everywhere, its texture scrolling; any hero who falls in walks to the landing (a step
  of 70) and up the stair. Anywhere to get stuck? The waterfall beside the ledge: does its scroll run downwards (if
  it runs up, flip `vSpeed` of `waterfall_scroll1` to +8)?
- **The ledge (secret):** the alcove beside the falls at 200 (a ledge top): can a hero grab it from the lagoon?
- **The lagoon mist:** a fog zone over the lagoon (teal, a little nearer than the level's fog). Too thick?
- **The end:** at the trade chart, its message, then 4 s later "Driftwood Cay is free...", the planet completing
  (Mirefall should open on the map) and the `driftwood_victory` sting (only the first time).
- **Falling through floors:** polyList 165 (the geometry needs 110).

**Placeholders:** the sea door leads to the game's usual way back (stock level 21) until 2.1 exists. The way back at
the start (the tunnel's dark recess) leads to 1.2's cave mouth; the smugglers' passage's end
(`back_to_the_smugglers__tunnels1`) to 1.4's start point 1, in its last passage.

## 1.4 Smugglers' Run (optional; JFG-169, built 2026-10-30, not played)

Start it from 1.2's smugglers' door (the back alley off the fish market), or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_smugglers --start-point 0`. Start point 1 is
the arrival from 1.3 (its smugglers' passage), at the far end of the level.

**The route:** the cellar stair → the rum cellar (3 drowned crew among three vats, a green lamp) → the brick tunnels
(a loop round a block; a dead end west with a Tribal, a niche south with ammo) → the drowned tavern (4 drowned crew
among three tables and the bar in 30 of water; the lookout on the gallery up the stair, a Tribal in the alcove behind
it) → the passage east past the strongroom's window (break the glass, climb in: the shotgun chest, the health upgrade,
2 Tribals) → down into the rock to the landing stage (3 deckhands among cargo) → the last passage, the grotto's
torchlight, the exit into 1.3's east landing.

**Untested in a pack level (please look):**
- **Drowned crew (undead, 0x121):** the pack's first use; the kind's texture slots were painted by size (head,
  body, limbs guessed, not looked at on the model): does it read as seaweed green-grey, anything painted on the wrong
  part? Health 11 (stock 10).
- **Enemies in water:** the tavern's 4 crew start and fight in 30 of water among the tables and the bar (Studio
  placed them there and found no problem). Do they walk and take cover in it, or float, stick or stand still? If they
  misbehave, the fix is the tavern floor dry with water only round its edges (`HOLLOW` in `blender/smugglers.py`).
- **The lookout on the gallery** (perch 180 over the floor, a rim 20 from x 520 to 700 in front of it, a board
  balustrade 100 high elsewhere): seen from the way in? Can it hit the way in, the water and the east doorway (Studio's
  raycasts say yes), and can it be shot back from the tables? Its region is the whole tavern floor.
- **The balustrade:** solid boards 100 high, no collider, up the stair and along the gallery. A hero who jumps over
  falls 180 at most, onto the dry floor or the water: fine?
- **Glass:** one square pane (140, sill 30) in the passage's south wall; a 50-deep reveal behind it, then a step of
  30 down into the strongroom.
- **The shotgun chest** (`contents` 0) and **the health upgrade** (upgrade 58, game flag 105): taken once each, gone
  after a reload?
- **Barrels and drums** (breakable) along the cellar's walls, outside the fight's region: do the drums' blasts hurt
  the crew? Any stuck in a wall?
- **The tavern mist** (fog zone, green-grey, a little nearer than the level's fog) and the water's scroll (texture 14):
  too thick, too fast?
- **Story:** 5 lines (arrival, the tavern, the window, the landing stage, the last passage). The arrival line also
  shows when coming in from 1.3.
- **The dark:** ambient (0.17, 0.21, 0.17) green-grey, candle and lantern pools, the cellar's green lamp. Readable?
- **Falling through floors:** polyList 176 (the geometry needs 117, at the tavern's water).
- **Links:** the smugglers' door in 1.2 → here; the way back (the dark recess at the stair's top) → 1.2's back alley
  (start point 2); the last passage → 1.3's smugglers' passage (start point 1); 1.3's passage end → here, start
  point 1. No stats screen between them (one region).

## 2.1 Stiltwater Outskirts (Mirefall's entry level; JFG-169, built 2026-10-30, not played)

Start it from 1.3's sea door (past the trade chart), from the planet map (Mirefall, once Driftwood is completed), or
straight in: `--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_stiltwater --start-point 0`.
Start point 1 (behind the flood gate) is for 2.2's way back; nothing leads there yet.

**The route:** the landing jetty (machine gun chest) → the crossing in the reed beds (3 storm midges over the water)
→ west to the hut plaza (4 slickers among crates and barrels; 2 lookouts on hut roofs) → the big hut (Tribal) and
the stair hut's roof (Tribal) → north to the mud island (4 marsh leeches among boulders) → the last bank (health,
ammo) → east to the leaning chapel (3 bog walkers; the light blue key on the altar dais at the flooded end) and its
bell tower (Tribal) → south to the fishers' rest (Tribal, health, ammo) → back to the crossing → north up the gate
walk → the flood gate (4 slickers and 3 bog walkers together) → the light blue key door → the passage → the exit.

**Untested in a pack level (please look):**
- **The new planet:** completing Driftwood (1.3's chart) should open Mirefall on the map, right of Driftwood (slate
  blue disc, x 480), its route from Driftwood to the right; picking it starts 2.1 at the jetty for every hero. The
  sea door from 1.3 should show the stats screen (Driftwood's region left) and arrive at the jetty.
- **Rain:** the game's rain (level 42's, intensity 180, opacity 220, `weatherFlags` 1 so the level keeps its own fog).
  Too heavy, too light, any slowdown? Does the fog stay the dark blue-grey (60, 70, 85) that matches the storm dome's
  horizon?
- **Lightning (Lua):** every 20-40 s the fog flashes pale blue-white (190, 205, 235) for 3 ticks and fades back over
  20; sometimes a second flicker. The first one 8-16 s after arrival. Does `jfg.fog` flash read as lightning, does the
  fog come back to the level's own exactly, anything left pale after a level change or a death?
- **The storm sky** (`pack:sky/storm`): dark clouds, paler rents. Seams with the fog at the horizon?
- **Storm midges (0x2D flyers)** and **marsh leeches (0x122)**: the pack's first use of both bases and kinds (slots
  painted by size, not looked at on the model). The leeches' squad is the base's only kind, a sentry (behaviour 9):
  they stand on the island and fire. Size right (stock 42%)? Health 29.
- **Bell lookouts (snipers, 2):** roofs at 240, 20 rims on the sides they fire over, a brazier with flames beside each.
  Seen from the walk up to the plaza before they fire? The stair hut's lookout can't hit the stair's foot (its rim).
- **Wading:** the marsh is 40 deep everywhere; every boardwalk is 100 over the bed with ramps every 400-600 and the
  islands a step of 60. Can any hero get stuck, or wade round anything that matters? Juno doesn't swim at 40?
- **The secret** under the big hut: wade in between the stilts (140 clear under its floor at 100): full health, full
  machine gun ammo. Reachable, visible enough (a faint warm glow)?
- **The leaning chapel:** tilted 9°, its floor sloping east into 40 of water. Do the bog walkers fight on the slope
  (holes made by hand round 3 upright pew-ends)? Can every hero climb the dais (a step of about 55 out of the water) to
  the key? Does the lean look right from outside?
- **The bell tower's stair and loft** (180, balustrades 100 without colliders: a fall is 220 into water).
- **Two squads at the gate** share one region and its 7 holes: do they spread over the cover, or crowd?
- **The flood gate** (wooden door 0x1AC, light blue key) in a 50-deep reveal; behind it the passage. Coming back from
  2.2 later (start point 1, behind the gate): the door stays open once unlocked?
- **Falling through floors:** polyList 152 (the geometry needs 101, at the big hut).
- **Size:** 264 KB unpacked, 6,500 triangles (fits the track buffer; bigger than 9 in 10 of the game's levels).

**Placeholders:** the exit behind the flood gate leads to the game's usual way back (stock level 21) until 2.2
exists (TODO in `levels/2.2_bellmarket.md`).
