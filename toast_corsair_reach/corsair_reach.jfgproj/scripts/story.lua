-- Corsair Reach: the story lines, shown once per visit to a level when the player reaches each spot.
-- Each beat: start (on arrival), box {x0, x1, z0, z1} (inside it), or near {x, y, z, r} (within r).

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
}

local current, said, ids = nil, {}, {}

local function beats_here(level)
  for name, list in pairs(BEATS) do
    if ids[name] == nil then ids[name] = jfg.level_id(name) or false end
    if ids[name] == level then return list end
  end
end

jfg.on("level", function(level)
  current, said = beats_here(level), {}
  if not current then return end
  for i, b in ipairs(current) do
    if b.start then said[i] = true; jfg.message(b.text, 5) end
  end
end)

jfg.on("tick", function()
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
      end
      if hit then said[i] = true; jfg.message(b.text, 4) end
    end
  end
end)
