-- Corsair Reach: the story lines, shown once per visit to a level when the player reaches each spot.
-- Each beat: start (on arrival), box {x0, x1, z0, z1} (inside it), near {x, y, z, r} (within r), flag n (when that
-- game flag turns on during the visit: a switch shot; already on at arrival, the beat is skipped), or after n (delay
-- seconds after beat n was shown), or door n (when that door unlocks during the visit: its squads are dead). A beat
-- may also complete a planet (complete = id), play a track (music = name), set a game flag for good (set_flag = n:
-- with it, the beat counts as done on later visits and its fog is put back at arrival) and fade the level's fog
-- (fog = {r, g, b, near, far, ticks}).

local BEATS = {
  level_sunwreck = {
    { start = true, text = "Driftwood Cay. The corsairs came in on the morning tide." },
    { box = { -1650, -640, 130, 870 }, text = "The village is burnt. Its people were taken." },
    { near = { 114, 220, -661, 150 }, text = "Their gate key. Careless." },
    { near = { 1100, 420, -1740, 190 }, text = "The harbour's theirs. Whatever they took, it's down there." },
  },
  level_gullwing = {
    { start = true, text = "The corsairs' harbour. The sun's going down; so are they." },
    { box = { -560, -175, 60, 340 }, text = "That winch holds the gatehouse door." },
    { box = { 600, 1240, 425, 640 }, text = "Their flagship. The hold's empty: the plunder's somewhere else." },
    -- past the gate (its squad keeps it shut), in the cave mouth
    { box = { 1825, 1975, -1400, -1305 }, text = "Torches in the cliff. That's where they keep it." },
  },
  level_blackwater = {
    { start = true, text = "The corsairs' grotto. Mind the drop." },
    -- out of the torch tunnel onto the walkway: the galleon under the moon, the vault door behind its bars
    { box = { -1650, -1380, -920, -650 }, text = "A whole galleon, wedged in the rock. The vault must be past it." },
    -- the winch on the forecastle shot (game flag 104): the hull door opens
    { flag = 104, text = "The winch dropped the gangway." },
    -- through the purple key door and down into the vault
    { box = { -500, 200, -1450, -1000 }, text = "Their hoard... but the Stormglass's crate is empty." },
    -- the trade chart on the table by the sea door; then the world is done: its last gate is behind the player
    { near = { -465, -40, -1075, 170 }, text = "A trade chart: sold to the storm-builders of Mirefall." },
    { after = 5, delay = 4, complete = "driftwood", music = "driftwood_victory",
      text = "Driftwood Cay is free. Mirefall appears on the map." },
  },
  level_smugglers = {
    { start = true, text = "Smugglers' tunnels. Something's still down here." },
    -- through the way in from the tunnels: the flooded tavern, its crew among the tables
    { box = { 0, 150, 100, 300 }, text = "The crew never left." },
    -- the passage past the strongroom's window
    { box = { 900, 1150, 250, 400 }, text = "A strongroom behind glass. Glass breaks." },
    -- down into the rock: the landing stage, cargo stacked for the grotto
    { box = { 1200, 1400, -360, -250 }, text = "Cargo for the grotto. Someone's still loading it." },
    -- into the last passage (south of start point 1, so an arrival from the grotto doesn't trip it at once)
    { box = { 1200, 1400, -800, -740 }, text = "Torchlight ahead: the grotto." },
  },
  level_stiltwater = {
    -- on the landing jetty (start point 0 is on it; start point 1, back from the market, is not)
    { box = { -200, 200, 1600, 1900 }, text = "Mirefall. It hasn't stopped raining since the engine came." },
    -- the crossing in the reed beds: the flood gate's lights to the north
    { box = { -200, 200, 800, 1000 }, text = "The flood gate's shut. Its key must be out here somewhere." },
    -- the walk up to the hut plaza
    { box = { -1200, -1000, 400, 800 }, text = "The colonists are hiding in their huts." },
    -- inside the leaning chapel
    { box = { 640, 900, -780, -420 }, text = "The chapel's going under with the rest of the town." },
    -- onto the gate platform from the south
    { box = { -400, 600, -1500, -1400 }, text = "The town's flood gate. The lighthouse is beyond the town." },
  },
  level_bellmarket = {
    -- the gate arcade (start point 0 is in it; start points 1-3, from the cistern and the spire, are not)
    { box = { -600, 600, 1300, 1600 }, text = "Bellmarket. The water's in the streets now." },
    -- the tower's foot: the door and the pulley over it
    { box = { -1600, -1000, -600, -450 }, text = "The tower door hangs from that pulley." },
    -- into the causeway's forecourt (start point 1 is east of it, in the north lane)
    { box = { -400, 400, -1300, -850 },
      text = "Two locks. The colonists say one key's up the bell tower, and the other went down the cistern." },
    -- the bell chamber, by its door out onto the roofs (a sphere: the floors below share its x and z)
    { near = { -1150, 700, -920, 220 },
      text = "From up here you can see it: the engine on the lighthouse, pulling the clouds down." },
    -- through the inner gate (start point 3, back from the spire, is north of this strip)
    { box = { -150, 150, -1730, -1685 }, text = "The causeway's clear." },
  },
  level_undercistern = {
    -- the landing at the foot of the entry stair (start point 0, the only one, is on it)
    { box = { -1400, -1200, -1400, -1100 }, text = "The cistern. The whole town drank from here." },
    -- in front of the sluice gate: its valve is across the channel, behind bars
    { box = { -1000, -900, -1060, -900 }, text = "The sluice is held shut. Its valve's across the channel, behind the bars." },
    -- the valve shot (game flag 108)
    { flag = 108, text = "The sluice gate's open." },
    -- into the cell block from the sluice passage
    { box = { -360, -200, -1080, -880 }, text = "Colonists, locked in. The corsairs made it a jail." },
    -- out onto the channel walks
    { box = { 480, 680, -1080, -880 }, text = "Something's moving in the drains." },
    -- on the plinth in the great cistern, by the key (a sphere: the gallery's lookout is above)
    { near = { 200, -260, 820, 150 }, text = "The causeway key. Back up to the square." },
  },
  level_stormspire = {
    -- on the causeway, past the gatehouse (start point 0, the only one, is south of this strip)
    { box = { -150, 150, 1300, 1480 }, text = "The lighthouse. The engine's on top." },
    -- the north half-floor inside the tower, up the first ramp (a sphere: the floors above share its x and z)
    { near = { -280, 220, -650, 130 }, text = "The gallery door hangs from that pulley." },
    -- out on the gallery, past the first turn (a sphere: the islet is under it)
    { near = { 400, 460, -150, 160 }, text = "Don't look down." },
    -- up into the lamp room (a sphere: the keeper's floor is under it)
    { near = { 280, 1200, -870, 160 }, text = "The Stormglass, wired into their engine." },
    -- the lift door (door 3) opens: the engine's guards are dead. The world is done: its last gate is open
    { door = 3, set_flag = 127, fog = { 120, 110, 100, 988, 1021, 90 }, complete = "mirefall",
      music = "mirefall_victory", text = "The engine's dead. The storm is breaking." },
    { after = 5, delay = 4, text = "Their maker's mark: Cinderhold. Mirefall is free." },
  },
  level_slagflats = {
    -- on the landing ledge (start point 0 is on it; start point 1, back from the bellows, is in the foundry)
    { box = { -2450, -2050, 1250, 1650 }, text = "Cinderhold. The storm engines start here." },
    -- out of the canyon's mouth onto the flats: the volcano and its fire fill the north
    { box = { -1550, -1350, 150, 450 }, text = "Their summit forge: the Crown. That's the way up." },
    -- the near bank of the first bridge, the turret on its plinth across the lava
    { box = { -1160, -1080, 120, 480 }, text = "A turret on the far bank. Keep to the slag heaps." },
    -- into the ore yard under the signal gantry
    { box = { 1150, 1300, -550, -250 }, text = "The yard gate runs off that rail signal." },
    -- the foundry door (door 2), seen locked this visit, opens: its gunners are dead
    { door = 2, text = "The foundry doors." },
  },
  level_bellows = {
    -- in the loading dock by the way in (start point 0 is in it; start points 1 and 2, back from the Crown and the
    -- vents, are in the bellows chamber's passages)
    { box = { -2000, -1700, -1350, -1050 }, text = "The Bellows. They pour the engines' hearts here." },
    -- through the casting hall's west door, under the catwalk's lookouts
    { box = { -300, -150, -440, -240 }, text = "Snipers on the catwalks. Keep to the moulds." },
    -- on the gallery by the foreman's door (a sphere: the hall floor is under it)
    { near = { -120, 600, -910, 130 }, text = "The foreman's door hangs from the crane. Its release is across the hall." },
    -- the crane's release shot (game flag 111)
    { flag = 111, text = "The crane let go. The foreman's door is open." },
    -- into the bellows chamber through the tango door (nothing under the chamber)
    { box = { 300, 500, 40, 160 }, text = "The bellows. Every furnace in the mountain breathes through it." },
    -- the exit door (door 3) opens: the chamber's guards are dead
    { door = 3, text = "The Crown is up the mountain." },
  },
  level_crown = {
    -- on the roof door ledge (start points 0 and 1, from the Bellows and the vents, are both on it)
    { box = { 1000, 1500, 1400, 1700 }, text = "Caldera Crown. Everything they build, they build up there." },
    -- at the foot of the rim gate's cut, past the crown guards' fire
    { box = { 1000, 1300, -100, 0 }, text = "Last chance to rest." },
    -- the counterweight shot (game flag 113): the rim gate opens
    { flag = 113, text = "The counterweight's down. The rim gate is open." },
    -- the way into the Crown, out of the quiet room (wave 1 starts here)
    { box = { -800, -700, -1300, -1100 }, text = "The forge-masters. All of them." },
    -- the forge core's door (door 1) opens: the last wave is dead. The pack is done: Cinderhold's last gate is open.
    -- Flag 126 is "the Crown is out": later visits keep the calm fog and play no sting
    { door = 1, set_flag = 126, fog = { 45, 12, 8, 988, 1021, 90 }, complete = "cinderhold",
      music = "cinderhold_victory", text = "The Crown's fires are out." },
    { after = 5, delay = 4, text = "Mirefall stays dry; the cay stays free. Corsair Reach is quiet." },
  },
  level_vents = {
    -- in the vent hatch by the way in (start point 0 is in it; start point 1, down from the Crown, is in the lift
    -- room at the far end of the level)
    { box = { -160, 160, 900, 1200 }, text = "Coolant vents. At least it's cool." },
    -- out of the hatch's pipe into the first chamber: steam and hissing either way round
    { box = { -150, 150, 560, 760 }, text = "Something's moving in the steam. Keep to the vent stacks." },
    -- in the pump hall's west alcove, at the rockets chest
    { box = { -520, -400, -1300, -1140 }, text = "Their spare parts. Ours now." },
    { after = 3, delay = 4, text = "The service lift by the pumps goes up to the Crown's roof door." },
  },
}

-- Lightning in Mirefall's levels: every `every` seconds (a random wait between the two), the fog flashes to `flash`
-- over 3 ticks and fades back to the level's own fog over 20; sometimes a second flicker follows. With stop_flag, it
-- stops for good once that game flag is on (the storm engine dead).
local LIGHTNING = {
  level_stiltwater = { fog = { 60, 70, 85, 985, 1019 }, flash = { 190, 205, 235 }, every = { 20, 40 } },
  level_bellmarket = { fog = { 60, 70, 85, 985, 1019 }, flash = { 190, 205, 235 }, every = { 20, 40 } },
  -- the storm at its worst over the lighthouse; flag 127 (set by its door beat) is the engine dead: no more
  level_stormspire = { fog = { 55, 65, 80, 984, 1018 }, flash = { 200, 212, 240 }, every = { 10, 20 }, stop_flag = 127 },
  -- level_undercistern has none: it is underground, with no sky or opening for a flash to show through
}

local current, said, ids, when, locked = nil, {}, {}, {}, {}
local clock = 0
local storm, next_flash, flash_ticks, flicker = nil, 0, -1, false

local function id_of(name)
  if ids[name] == nil then ids[name] = jfg.level_id(name) or false end
  return ids[name]
end

local function beats_here(level)
  for name, list in pairs(BEATS) do
    if id_of(name) == level then return list end
  end
end

local function storm_here(level)
  for name, s in pairs(LIGHTNING) do
    if id_of(name) == level then return s end
  end
end

local function lightning(seconds)
  if not storm or (storm.stop_flag and jfg.flag(storm.stop_flag)) then return end
  local f = storm.fog
  if flash_ticks >= 0 then
    flash_ticks = flash_ticks + 1
    if flash_ticks == 3 then  -- the flash has peaked: fade back to the level's fog
      jfg.fog(f[1], f[2], f[3], f[4], f[5], 20)
    elseif flash_ticks > 24 then
      flash_ticks = -1
      if flicker then  -- a second, quicker flicker soon after
        flicker = false
        next_flash = seconds + 0.3
      else
        next_flash = seconds + math.random(storm.every[1], storm.every[2])
      end
    end
  elseif seconds >= next_flash then
    local c = storm.flash
    jfg.fog(c[1], c[2], c[3], f[4], f[5], 3)
    flash_ticks = 0
    if next_flash > 0 and math.random() < 0.35 then flicker = true end
  end
end

local function show(i, b, seconds)
  said[i], when[i] = true, clock
  jfg.message(b.text, seconds)
  if b.set_flag then jfg.set_flag(b.set_flag, true) end
  if b.fog then jfg.fog(b.fog[1], b.fog[2], b.fog[3], b.fog[4], b.fog[5], b.fog[6]) end
  local done = false
  if b.complete then
    done = select(3, jfg.planet(b.complete))  -- completed on an earlier visit: no sting again
    jfg.complete_planet(b.complete)
  end
  if b.music and not done then jfg.music(b.music) end
end

jfg.on("level", function(level)
  current, said, when, clock, locked = beats_here(level), {}, {}, 0, {}
  storm, flash_ticks, flicker = storm_here(level), -1, false
  if storm then next_flash = math.random(8, 16) end  -- the first soon after arrival
  if not current then return end
  for i, b in ipairs(current) do
    if b.start then show(i, b, 5) end
    if b.flag and jfg.flag(b.flag) then said[i] = true end  -- already done on an earlier visit
    if b.set_flag and jfg.flag(b.set_flag) then  -- done on an earlier visit: its fog stays, no message or sting
      said[i] = true
      if b.fog then jfg.fog(b.fog[1], b.fog[2], b.fog[3], b.fog[4], b.fog[5], 1) end
    end
  end
end)

jfg.on("tick", function(level, seconds)
  clock = type(seconds) == "number" and seconds or clock + 1 / 30
  lightning(clock)
  if not current then return end
  local x, y, z = jfg.player()
  if not x then return end
  for i, b in ipairs(current) do
    if not said[i] then
      local hit = false
      if b.box then
        hit = x >= b.box[1] and x <= b.box[2] and z >= b.box[3] and z <= b.box[4]
      elseif b.near then
        local dx, dy, dz = x - b.near[1], y - b.near[2], z - b.near[3]
        hit = dx * dx + dy * dy + dz * dz <= b.near[4] * b.near[4]
      elseif b.flag then
        hit = jfg.flag(b.flag)
      elseif b.door then  -- seen locked this visit, now open
        local l = jfg.door_locked(b.door)
        if l then locked[i] = true elseif l == false and locked[i] then hit = true end
      elseif b.after then
        hit = when[b.after] ~= nil and clock - when[b.after] >= (b.delay or 0)
      end
      if hit then show(i, b, 4) end
    end
  end
end)
