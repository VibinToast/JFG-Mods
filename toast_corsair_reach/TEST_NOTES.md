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
