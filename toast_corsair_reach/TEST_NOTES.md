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

**Placeholders:** both onward exits lead to the game's usual way back (stock level 21) until 1.3 (the cave mouth)
and 1.4 (the smugglers' door) exist. The way back at the start (the arch) leads to 1.1's gate.

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

**Placeholders:** the sea door and the way back to 1.4 lead to the game's usual way back (stock level 21) until 2.1
and 1.4 exist. The way back at the start (the tunnel's dark recess) leads to 1.2's cave mouth.
