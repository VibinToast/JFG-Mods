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
Start point 1 (behind the flood gate) is where 2.2's way back arrives.

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

**Links:** the exit behind the flood gate leads into 2.2's gate arcade (start point 0); 2.2's way back arrives at
start point 1, in the passage behind the gate. No stats screen between them (one region).

## 2.2 Drowned Bellmarket (Mirefall's hub; JFG-169, built 2026-10-30, not played)

Start it from 2.1's flood gate passage, or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_bellmarket --start-point 0`. Start points 1
(the north lane by the forecourt) and 2 (outside the cistern's arch) are for 2.3's exits, 3 (behind the inner gate)
for 2.4's way back; nothing leads there yet.

**The route:** the gate arcade (the whole hub in view: the fountain, the tower north-west, the cistern's blue lamp
east) → the flooded square (wade 20 deep) to the fountain court (4 tower wardens behind market stalls, 4 slickers
patrolling round the fountain; 2 lookouts on the tower's balconies) → the west lane and street (3 bog walkers among
rubble; the open house: Tribal, health) → the tower's foot: shoot the pulley over the door (flag 106) → inside, up
the ramps: the first landing (3 slickers), the second floor (Tribal by the window), the third landing (2 tower
wardens), the bell chamber (the lime key, a Tribal, health, ammo) → out of its east door and down the roofs (520,
340, 180: the low roof has a Tribal), the stair to the forecourt → the gates' fight (3 tower wardens and 3 bog walkers)
→ the lime gate → (blue gate shut) → the north lane east, the east street, the cistern's arch → 2.3. Back from 2.3
with the blue key at start point 1 → the blue gate → the exit to 2.4. The secret: wade round the fountain to the gap
in its north face (Tribal, the world's health upgrade).

**Untested in a pack level (please look):**
- **Tower wardens (0x99, shielded):** the pack's second kind on this base (rain-dark steel plates, rivets, a pale bell
  on the shield; slots painted by role, not looked at on the model). Size the stock squad's (40%). Health 10.
- **The switch door:** the game's shootable switch (0x48) over the tower door at 236 (a beam and brackets round it):
  seen and shot from the west street? Does the door open, the jingle play, and stay open after a reload (flag 106)?
- **Squads on the tower's half-floors** (180 and 540, a ceiling at 960 above): `place_squad` saw the ceiling as the
  floor, so members were set by hand and the blocks' holes added by hand. Do the slickers and wardens move between
  their blocks, or stand? Do any walk off the edge (a drop of 160-180, harmless) or onto a ramp?
- **The ramps** (26.6-29.4°, 140 wide) and **half-floors without rails**: can every hero climb them, and does
  anything read as a ledge or snag? A fall between floors is 160-180 at most.
- **The shortcut:** from the bell chamber's east door a drop of 180 onto roof A, then 180 onto B, 160 onto C, and
  the stair down. Do the drops hurt (they shouldn't: under 240)? Do the parapets' colliders (to 400) feel like
  invisible walls? Can anyone climb back up (they shouldn't)?
- **The patrol:** squad 2 walks a chain round three sides of the plinth (its north half stands in the water); do they
  walk it, and fight off it once they see the hero?
- **Squads on the court** (paving 5 over the water): squad 1 stays on its south band behind the stalls (holes); do
  any step into the water?
- **Lookouts on the balconies** (450 and 600, 20 rims): seen from the arcade before they fire? Each stands at the
  corner it fires over (`raycast`: clear to the north lane, the court and the west street; the tower's foot is under
  them, a dead zone). Its region is the ground it watches.
- **The blue key door:** 2.3 will hold its key; until then it can't open (and `validate` warns). The **lime key door**
  and its key in the bell chamber: does the door open with the key, and stay open (2.3's return lands outside it)?
- **The grotto:** the gap in the plinth's north face (120 wide, 110 over the drowned cobbles, 20 of water): can every
  hero wade in? The health upgrade (upgrade 60, flag 107) taken once?
- **Rain, lightning, the storm sky** as 2.1 (the same values and `LIGHTNING` row). The lighthouse's glowing lamp room
  far north-east: seen from the chamber's door?
- **Story:** 5 lines (the arcade, the tower's foot, the forecourt, the bell chamber's door, through the inner gate).
  Arrivals at start points 1-3 show none of them.
- **Size:** 207 KB unpacked, 5,094 triangles; polyList need 86 (the game's 90).

**Placeholders:** none left: the causeway's exit leads to 2.4 (start point 0) since 2.4 was built, the cistern's to 2.3
(start point 0).

## 2.3 The Undercistern (JFG-169, built 2026-10-30, not played)

Start it from 2.2's cistern arch (the ramp's foot), or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_undercistern --start-point 0`. One start
point (0, the foot of the entry stair).

**The route:** down the entry stair → the pump gallery (3 cistern crawlers among three pumps) → the sluice gate is
shut: shoot the valve across the channel, behind the bars (flag 108) → the sluice passage down to the cell block (4
marsh leeches; three cells with glass windows, a Tribal in each) → the channel walks: rats wade across the channel
out of a tunnel east (the ammo cache at its end) and out of one south (a Tribal at its end) → west along the walk,
the stair down to the guard room (quiet: health, ammo, a Tribal) → the great cistern (knee-deep water, 7 pillars, 5
cistern crawlers, 3 bog walkers at the far end, a lookout on the south gallery; the blue key on the plinth in the
middle; the gallery's stair along the east wall for ammo) → the east door opens when the bog walkers are dead → the
return stair up → the exit into 2.2's north lane by the causeway gates. The loop: from the walks' west end, the
return stair up to the pump gallery (its door opens when the south rats are dead).

**Untested in a pack level (please look):**
- **The two new kinds.** Cistern crawlers on 0xEF (pale bone-white, chalk spots, a grey underside; the base's
  smart squad, size 39): do they walk between the pillars and pumps and take cover? Drain rats on 0xEE at size 26
  (stock 37), wet grey-brown with a dull red eye: small enough to read as vermin, big enough to hit? Slots painted by
  size, not looked at on the model.
- **Squads in water** (the great cistern: crawlers and bog walkers placed by hand in 30 of water, as 1.4's tavern
  crew): do they walk, take cover at the pillars and fight? Do the rats wade the 30-deep channels from their tunnels
  to the walkway, or stop at the water?
- **Rats with no cover** (`validate` `squad-cover`): their regions are straight strips (tunnel, channel, walkway).
  Do they rush, or stand at the tunnel's end and fire? If they stand, a block in each tunnel is the fix.
- **The valve switch** (0x48) on the alcove's back wall at 136, behind four iron bars (gaps about 18), across the
  channel: easy to see and hit from the gallery's floor? Do the bars stop shots? Does the sluice gate open and stay
  open after a reload (flag 108)? Can a hero squeeze between the bars (harmless: a dead end)?
- **Glass:** three panes 138 a side in square windows (140, sill 30): do they fill the openings, break, and let
  every hero step over the sill to the Tribal?
- **The lookout** on the gallery (perch 230, a 20 rim, its lamp behind it, the game's flames beside it): seen from
  the way in before it fires? Its lines to the way in and the plinth are clear (`raycast`); the east door's passes a
  pillar.
- **Squad doors:** the return door (squad 4, the south rats) and the east door (squad 6, the bog walkers) open when
  their squads are dead?
- **The blue key carried back (`key_level`-style, placed here for 2.2's door):** take it from the plinth, leave by
  the return stair to 2.2 start point 1: does the inner (blue) gate open? And the way back (2.2 start point 2)?
- **Falls:** the gallery's balustrade (100, no collider) and its 20 rim: a fall of 200 into the water must not hurt.
  The gallery stair (21.8°) and the other stairs (26.6-27.3°): every hero climbs them?
- **Darkness:** fog (15, 25, 35), oil lamps (24 lights: the header's limit), bake ambient (0.12, 0.16, 0.25). Too
  dark to see the crawlers, or the switch?
- **No rain, no lightning** underground (a choice: no sky or opening; `story.lua` has no `LIGHTNING` row for it).
- **Story:** 6 lines (the entry landing, the sluice gate, the valve shot, the cell block, the channel walks, the key).
- **Size:** 137 KB unpacked, 3,430 triangles; polyList need 91 (the build sets 137).

## 2.4 Stormspire (Mirefall's last level; JFG-169, built 2026-10-30, not played)

Start it from 2.2's causeway passage (behind both gates), or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_stormspire --start-point 0`. One start
point (0, the causeway's south end).

**The route:** the causeway north (two storm midge squads come down over it; fallen parapet blocks and a cart as
cover) → the keeper's islet (3 engine guards between the causeway and the tower; the cottage west: health, ammo, a
Tribal) → the tower door opens when the guards are dead → inside, up the west ramp to the north half-floor (4
slickers among stone blocks) → shoot the pulley on the north wall (flag 109) → up the east ramp to the gallery door
→ out on the gallery: up the east side (3 storm midges over the sea) → the north balcony (3 tower wardens, 2 lookouts
on perches above it) → up the west side (Tribal on the broken balcony) → the south balcony (health, ammo) → the
keeper's floor (4 spire captains and 3 engine guards; a Tribal in the storeroom nook) → the lamp room door opens
when both squads are dead → the quiet stair (full health, ammo) up into the lamp room → 4 engine guards round the
storm engine → the lift door opens: Mirefall complete → the lift cage's exit (the stats screen, then stock level 21
until 3.1 exists).

**Untested in a pack level (please look):**
- **The world's end (never run):** when the lamp room's guards die and the lift door opens: does `story.lua`'s new
  door beat fire (message "The engine's dead. The storm is breaking.", then "Their maker's mark: Cinderhold..."), is
  Mirefall completed (Cinderhold shows on the map), does the `mirefall_victory` sting play, only the first time? Does
  the **lightning stop** for good (flag 127), and the **fog fade** to the warmer (120, 110, 100) over 3 seconds? Leave
  and come back (or die after it): the fog should come back warm at arrival, with no lightning and no message. The
  rain goes on (Lua can't stop it).
- **The stats screen** as the lift's exit leaves Mirefall's region (`arg1A` 1), and no stats screen between 2.2 and
  2.4.
- **The two new kinds:** spire captains (0x12F, storm-blue coat, a yellow lightning stripe) and engine guards (0x9C,
  black and brass, a brass cog on the shield, a cold blue shield glow). Slots painted by role, not looked at on the
  model. Do the engine guards take cover (they carry big shields)?
- **Flyers:** storm midges over the causeway (both squads at once, over its two halves) and over the gallery's east
  side (the squadron set high by hand so they drop to the gallery, not to the islet under it). Do they come over the
  rails, and can they be hit?
- **The lookouts on their perches** (880, over the north balcony at 650): seen from the east ramp as the tower turns,
  before they fire? `raycast` clear to the ramps and the balcony. If one is still alive when the player climbs the
  west side, it is behind them.
- **Squads under floors** (the slickers on G1 under the keeper's floor, the wardens on the balcony under the perches,
  the keeper's floor under the lamp room, the lamp room): members, region points and holes set by hand. Do they move
  between their blocks, or stand? Squad 11 has `flags` + 0x40 (go for the hero at once).
- **Two squads, one door** (the lamp room door, id 2): does it open only when both the captains and the guards are
  dead?
- **The pulley switch** (0x48 at 560 on the north wall over G1): seen and shot from G1 or R2? Does the gallery door
  open and stay open after a reload (flag 109)?
- **The gallery:** rails at 150 with colliders to 1,300 (no fall into the sea): do they feel like invisible walls?
  The ramps (9-11°) and the inside ramps (25.9-29.4°): every hero climbs them? The two open ends (parapets 150 with
  colliders).
- **The broken balcony** (side 12, a `ledge` top 140 over the ramp, Tribal 2): can any hero jump and grab it, or only
  some? Optional.
- **The lamp room's barred windows** (bars and a collider in the outer face: a grille, it may read as an invisible
  wall) and the slot's balustrades (100, no collider; drops of 110-237 onto the stair: harmless?).
- **The lift door** in the lamp room's east wall (a 30 reveal, the cage beyond): does the door fill its opening?
- **Heaviest rain** (intensity 191, opacity 240, steeper and windier than 2.1's) and lightning every 10-20 s: too
  much? The storm sky's horizon against the fog (55, 65, 80).
- **Story:** 6 lines (the causeway, G1, the first ramp, the lamp room, the engine dead, Cinderhold).
- **Size:** 224 KB unpacked, 5,449 triangles; polyList need 281 (the build sets 422).

**Placeholders:** none left: the lift's exit ("down the keeper's lift", `arg1A` 1) leads to 3.1's landing ledge
(start point 0) since 3.1 was built. 2.2's causeway exit leads here.

## 3.1 Slag Flats (Cinderhold's entry level; JFG-169, built 2026-10-30, not played)

Start it from 2.4's lift (after the engine dies), from the planet map (Cinderhold, once Mirefall is completed), or
straight in: `--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_slagflats --start-point 0`.
Start point 1 (in the foundry's vestibule, facing out) is where 3.2's way back will arrive.

**The route:** the landing ledge (a small lava pool beside it) → up the basalt canyon: the machine gun chest and a
Tribal in a niche on the right → 4 furnace hands where the canyon widens (basalt columns as cover) → 3 ember beetles
at the last bends → the flats: bridge 1 under a turret's fire (slag lumps on the near bank), 3 cinder wasps over the
ground beyond → bridge 2 (a second turret), or round the north end of the middle river, past its spring (the loop) →
bridge 3: 2 slag gunners at its far end → the cut into the ore yard under the signal gantry: 4 furnace hands and 3
ember beetles among ore carts and bins → shoot the rail signal hanging under the gantry (flag 110) → the yard gate
opens → up the ramp to the forge gate: 2 slag gunners lock the foundry door; it opens on a camera shot → the exit at
the back of the vestibule (for now the game's way back).

**Untested in a pack level (please look):**
- **The planet:** does Cinderhold (a red-black disc right of Mirefall) appear on the map once Mirefall is completed,
  reached with the stick right from Mirefall (left goes back)? Does the map start this level, for every hero? Does
  2.4's lift arrive on the landing ledge, with the stats screen first?
- **Lava (the pack's first):** three rivers, a spring, a lake and the landing's pool, all a surface 30 over a solid
  bed with banks 36 high. Does it hurt Vela and Lupus, can they walk straight out anywhere, is Juno unhurt and does
  he wade (not fall through)? Does it scroll (texscroll texture 12; if the wrong surface moves, the lava's index is
  another one)? Does it glow (its vertex colours are near white; red-orange pools are baked along the banks)?
- **The lava-walker's cache:** an island in the lake bay south of the middle river, about 200 of lava from the north
  shore: a Tribal and full machine gun ammo. Juno's secret; how much does it cost Vela or Lupus to wade there?
- **Falling ash:** the game's snow, light and slow (intensity 70, opacity 140, weatherFlags 1). Does it read as ash
  under the red sky, or as snow? If snow, remove it (`set_level weather "none"`).
- **The sky** (`pack:sky/cinder`, its first use): a dark red dome, the volcano due north with fire and smoke at its
  top, 40 degrees up. Seen over the canyon walls from the start, and over the north rim from the flats? Does the
  horizon meet the fog (70, 30, 20)?
- **Five new kinds and four new bases:** furnace hands (0x78: leather apron, goggles), ember beetles (0xBE, the
  pack's first: black crust, glowing seams; their stock size 35 is a big beetle), cinder wasps (0x29, first: ash grey
  and orange, flyers over the ground between rivers 1 and 2), forge turrets (0xF5, first: on stone plinths 70 high on
  the far banks of bridges 1 and 2; can they hit the hero on the bridge, can he hit them?) and slag gunners (0x143,
  first: big armoured gunners, size 40 of a 368-tall model; the game's only squad of them is a smart one, so they
  move behind the slag lumps at bridge 3 and the ingot stacks in the court). Slots painted by role, not looked at on
  the models.
- **The switch hanging under a beam:** the rail signal (0x48) at 450 under the gantry over the yard's way in, facing
  into the yard. Can it be seen and shot from the yard floor? Does the yard gate (0x19D, a new door type for the
  pack) open, fill its opening, and stay open after a reload (flag 110)?
- **The foundry door** (0xF9, 338 x 256, a new door type for the pack) in a 300 x 216 opening: does it fill it? Does
  it open when both gunners die, with the camera shot from the court (lock light 0xDE on the court floor beside it)?
  Message "The foundry doors."
- **Squads sharing a region** (the yard's two) and their 7 cover holes (carts and bins). Do they move between cover?
- **The column stair** (secret, any hero): basalt columns 70, 140 and 210 high against the canyon's west wall, a full
  health on top.
- **Arriving at start point 1** (from 3.2, when it exists): if the gunners are alive again, the foundry door stays
  locked from inside: the player can only go back into 3.2. Fine?
- **Story:** 5 lines (the landing, the canyon's mouth, bridge 1, the yard, the foundry door).
- **Size:** 245 KB unpacked, 5,237 triangles; polyList need 74 (fits the game's 90).

**Placeholders:** none now: the vestibule's exit leads into 3.2's loading dock (done by 3.2's session).

## 3.2 The Bellows (JFG-169, built 2026-10-30, not played)

Start it from 3.1's foundry vestibule, or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_bellows --start-point 0`. Start points 1 (top
of the exit passage) and 2 (the side recess) are where 3.3's and 3.4's ways back arrive.

**The route:** the loading dock (quiet; the way back to 3.1 in its west wall; a ramp up to a locked door in its east
wall) → corridor south → furnace room 1: 4 furnace hands among coal bunkers → furnace room 2: 4 more → (side room:
a Tribal, health, ammo) → the casting hall's west door: three catwalk lookouts above on perches, two turrets on
plinths across the molten channel; ingot stacks and the mould bed to hide behind (**secret**: a low opening in the
mould bed's south face, a crawlspace with full health and full machine gun ammo) → over a bridge → 4 forgemasters at
the stair → up the stair to the gallery: the patrol of 4 furnace hands → shoot **the crane's release** across the
hall (the switch under the crane's jib on the south wall, flag 111) → the foreman's office: **the tango key**, a
Tribal → the patrol dead opens the shortcut door down to the dock (the loop) → the stair room up to the catwalk →
across the hall over the channel past the lookouts' perches (a Tribal in a railed bay) → the tango key door → the
bellows chamber: 4 furnace hands and 2 slag gunners lock the exit door; a Tribal behind the bellows → the exit door
→ the passage up to the Crown (3.3). The side door east, under a blue light, leads to the vents (3.4's vent hatch).

**Untested in a pack level (please look):**
- **Snipers on perches over a hall** (three catwalk lookouts, a new kind of 0x8C): perches 110 out from the
  catwalk's west side, no rim, the lookout 25 from the edge, a red lamp and the game's flames beside each. Seen
  before they fire from the west door? Can they hit the hero on the west floor, and can he hit them? Do they ever
  fall or step off their perches?
- **Forgemasters** (0x12F, a new kind: obsidian and gold), 4 of them among ingot stacks and the turrets' plinths at
  the stair foot. Do they move between cover? Health 18 each: too tough for this point?
- **The molten channel** under two iron bridges (rails 90, no collider) and under the catwalk: does it scroll
  (texscroll texture 15), glow, hurt, and can a hero who falls in walk straight out (banks 36)?
- **A switch shot across a hall:** the crane's release (0x48, stock size 20) at 960 on the south wall, about 900 from
  the gallery. Can it be seen and hit from the gallery (and the floor)? Does the foreman's door (a mine door, 0x19D)
  open and stay open after a reload (flag 111)? Message "The crane let go...".
- **A patrol on a gallery** (4 furnace hands walking a straight 1,060 chain at 600, under the catwalk at its
  middle): do they walk it, and fight when they see the hero (no cover in their strip)? Does their death open the
  shortcut door at the top of the dock's ramp (door 2)?
- **The gallery's open rail** (kerb 30, posts, a rail at 100, no collider; a fall of 250 to the hall floor): can the
  hero slip between the posts? Is the hall in view from it?
- **The catwalk** (grating 200 wide at 850, rails at 150 with a collider to 400 over them): any invisible-wall feel
  at the rails? The perches open off it with no rail (a 500 fall: hurts, onto the floor, not death).
- **The tango key and its door** (the pack's tango colour; the key on the office floor).
- **The bellows chamber:** furnace hands and slag gunners sharing a region and one door; the bellows as a big cover
  hole (added by hand). Do the gunners spawn clear of the bellows (their squadron stands at (380, 850, 600))? Does
  the exit door open when all six die (`door = 3` message)?
- **The side door** (an open mine door, keyLock 0, as 1.2's door to 1.4): does it open as the hero comes?
- **Light:** no sky, every room lit by furnaces, the channel and lamps (ambient lifted from the kit's as in 3.1). Too
  dark anywhere (the dock and the furnace rooms are the darkest)? The cold blue light at the side door visible?
- **Story:** 6 lines (the dock, the hall's west door, the gallery by the foreman's door, the release shot, the
  chamber, the exit door).
- **Size:** 156 KB unpacked, 3,924 triangles; polyList need 91 (the build sets 137).

**Links:** the exit up to the Crown leads to 3.3's roof door (its start point 0); the side door to 3.4's vent hatch
(its start point 0).

## 3.3 Caldera Crown (Cinderhold's last level, the pack's finale; JFG-169, built 2026-10-30, not played)

Start it from 3.2's exit passage, or straight in:
`--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_crown --start-point 0`. Start point 1 (the
service lift, beside start point 0) is where 3.4 arrives. 3.2's exit up to the Crown now leads here.

**The route:** the roof door ledge (the doorhouse: the way back down to 3.2 and the service lift to the vents; the
flats far below over a railing) → leg 1 west under lookout 1 on its perch → the west landing: ember beetles, cinder
wasps over them and lookout 2 above, all at once → leg 2 east (a Tribal in an alcove at its end) → leg 3 west → leg 4
east → the ash shelf: 4 crown guards round a fire drum → shoot **the counterweight** on the basalt pillar in the
lava pool (flag 113) → the rim gate opens (a Tribal in an alcove east of the shelf) → the rim walk round the crater
(a Tribal at its dead end left of the gate), the lava lake below: 2 slag gunners in a bay, 3 cinder wasps → the quiet
room (full health, full ammo) → the Crown: wave 1 at the way in, wave 2 as you come round the ring, wave 3 on the
causeways and the island → the core door opens: the end (complete, sting, fog) → inside: a Tribal and the shuttle
pad home (the game's usual way back, with the stats screen).

**Untested in a pack level (please look):**
- **The waves on trigger zones** (squadron `trigger` 1, the zones set by hand; validate's `squad-trigger` warnings on
  them are expected): wave 1 (5 furnace hands, 3 forgemasters) should appear as you step into the Crown from the
  quiet room; wave 2 (2 slag gunners, 4 cinder wasps on the west ring) as you come round the north or south ring,
  before either causeway; wave 3 (5 crown guards on the island, 3 forgemasters by the south causeway; `flags` 0x40:
  they come straight for you) as you step onto a causeway. Do all three appear? If wave 3 never appears the core door
  stays locked (a softlock): the fallback is `trigger` 3 on all six wave squads (all at once).
- **The end:** when the last of wave 3 dies the core door opens (a camera shot of it, 3 s), "The Crown's fires are
  out.", the fog fades to a calm dark red, `cinderhold_victory` plays, Cinderhold is completed; "Mirefall stays dry;
  the cay stays free. Corsair Reach is quiet." 4 s later. On a later visit: no sting, the calm fog at arrival. Does
  the map show Cinderhold completed? The way home inside the core: the stats screen, then the game's usual way back.
- **Crown guards** (0x9C, the new kind: molten gold plate, ember seams, a crown on the shield): health 16, on the
  ash shelf (4) and the island (5). Too tough for the island's narrow ring round the core?
- **The counterweight switch** (0x48) on a pillar in a lava pool at the shelf's north-east corner, 120 over the
  shelf: easy to see and hit? Does the rim gate (a mine door) open and stay open after a reload (flag 113)? Message
  "The counterweight's down...".
- **Lookouts on perches over the switchbacks** (catwalk lookouts, 160 and 220 over the leg below, braziers beside
  them): seen before they fire? Can the hero hit them from below?
- **Three types at once** at the west landing (beetles, wasps, lookout 2 sharing one region): too much?
- **The rim walk's railing** over the crater (posts every 150, a rail at 150, a collider to 400): any invisible-wall
  feel? Is the lava lake in view below?
- **The lava:** the crater lake (far below, out of reach), the Crown's pit (30 deep, banks 36: walk out) and the
  shelf's pool: do they scroll (texscroll texture 14), glow and hurt?
- **Ash:** 3.1's snow settings (intensity 70). Does it read as falling ash here?
- **The sky:** `cinder_rim`, Cinderhold's dome without the volcano (you stand on it). Does the fog meet its horizon?
- **Light:** night, the lava glowing from below, braziers and the forge's fire on the core (22 lights). Too dark on
  the legs?
- **Size:** 260 KB unpacked, 5,979 triangles; polyList need 189 (the build sets 284).

**Links:** the service lift leads down to 3.4's lift room (its start point 1).

## 3.4 Coolant Vents (Cinderhold's optional level; JFG-169, built 2026-10-30, not played)

Start it from 3.2's side door (the bellows chamber's east wall), from 3.3's service lift (start point 1), or straight
in: `--mods-only toast_corsair_reach --start-level toast_corsair_reach:level_vents --start-point 0`.

**The route:** the vent hatch (quiet; the way back to 3.2 on its south wall; message 1) → a short pipe north into K1
(ammo; message 2) → round the ring of six round chambers either way, or across through the manifold in the middle:
vent swarmers (4) in K2 (south-west), in the manifold and in K5 (north-east), each pack among four vent stacks; health
and ammo in K3 and K6 → the dead ends off K3 (north-west) and K6 (south-east): 4 ash walkers among coolant tanks and
a Tribal behind them in each → K4 (north, quiet: health, full machine gun ammo) → the pump hall: 5 ash walkers and 4
swarmers at once among five pumps and four vent stacks → the rockets chest in the west alcove (message 3, then the
lift's message 4), the health upgrade across the coolant channel in the north wall's alcove, Tribals in the south and
east alcoves → the service lift (east wall) up to 3.3.

**Untested in a pack level (please look):**
- **Vent swarmers** (0xEE, the new kind: pale ash, soot flecks) at size 28, health 27: their squadrons spawn the
  pack round themselves at a pipe's mouth between the stacks. Do they appear clear of the stacks, use them as cover,
  and read as a swarm? Too tough at 27?
- **Ash walkers** (0x121, the new kind: ash grey, ember cracks), health 15, among four coolant tanks in a small round
  room (r 230). Do they move between the tanks or crowd?
- **Two squads sharing one region** in the pump hall (5 walkers + 4 swarmers, nine holes): too much for an optional
  level? Can the hero get between the pumps (gaps 65)?
- **Steam** (fog zones): white-grey (150, 156, 162, 980 / 1,018) in the seven fighting and side chambers, the
  level's own (55, 66, 76, 986 / 1,021) in the hatch, K1, K4 and the hall. Too thick or too faint? Does a zone's fog
  stay after leaving it (each room sets its own, so it shouldn't show)?
- **The coolant channel** (water 27 deep, texture 0x11D0, texscroll texture 5): does it scroll and read as coolant?
  Can every hero wade across to the health upgrade's alcove (a step of 35 up out of it)?
- **The health upgrade** (flag 112): does it stay taken after a reload?
- **The rockets chest** (`contents` 20): rockets, with rocket ammo beside it and a rocket clip in the lift room.
- **Round rooms:** walls of 20-degree pieces, domes up to a glowing grille; any seams where a pipe meets a chamber
  (the mouths are cut exactly 200 wide)? Any spot where the hero catches on a floor edge?
- **Light:** coolant blue under every grille, warm glows at the pumps and the hatch (16 lights; ambient lifted from the
  kit's). Too dark or too blue?
- **Sound:** steam hiss (sound 130 at pitch 190) in the steam chambers, the pumps (56 at pitch 45): do they read as
  steam and pumps?
- **Size:** 131 KB unpacked, 3,245 triangles; polyList need 57 (the build leaves 90).

**Links:** the vent hatch's exit leads back to 3.2's side recess (its start point 2); the service lift up to 3.3's
service lift (its start point 1). 3.2's side door and 3.3's service lift now lead here (start points 0 and 1).
