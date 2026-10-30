-- Corsair Reach: the story lines, shown once per visit to a level when the player reaches each spot.
-- Each beat: start (on arrival), box {x0, x1, z0, z1} (inside it), near {x, y, z, r} (within r), flag n (when that
-- game flag turns on during the visit: a switch shot; already on at arrival, the beat is skipped), or after n (delay
-- seconds after beat n was shown). A beat may also complete a planet (complete = id) and play a track (music = name).

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
}

local current, said, ids, when = nil, {}, {}, {}
local clock = 0

local function beats_here(level)
  for name, list in pairs(BEATS) do
    if ids[name] == nil then ids[name] = jfg.level_id(name) or false end
    if ids[name] == level then return list end
  end
end

local function show(i, b, seconds)
  said[i], when[i] = true, clock
  jfg.message(b.text, seconds)
  local done = false
  if b.complete then
    done = select(3, jfg.planet(b.complete))  -- completed on an earlier visit: no sting again
    jfg.complete_planet(b.complete)
  end
  if b.music and not done then jfg.music(b.music) end
end

jfg.on("level", function(level)
  current, said, when, clock = beats_here(level), {}, {}, 0
  if not current then return end
  for i, b in ipairs(current) do
    if b.start then show(i, b, 5) end
    if b.flag and jfg.flag(b.flag) then said[i] = true end  -- already done on an earlier visit
  end
end)

jfg.on("tick", function(level, seconds)
  if not current then return end
  clock = type(seconds) == "number" and seconds or clock + 1 / 30
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
      elseif b.after then
        hit = when[b.after] ~= nil and clock - when[b.after] >= (b.delay or 0)
      end
      if hit then show(i, b, 4) end
    end
  end
end)
