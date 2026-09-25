-- Build a multi-frame .aseprite from a horizontal strip PNG, in crowd_v2.aseprite's layout: one
-- layer named "Flattened", one frame per cell, frame durations and tags as given. build_ship.py
-- drives it; the strip must be a single row of fw x fh frames.
--   Aseprite -b --script-param strip=<strip.png> --script-param fw=640 --script-param fh=40
--               --script-param durations=350,350,350,150,150,200,200
--               --script-param tags=idle:1-3,cheer:4-5,boo:6-7
--               --script-param out=<file.aseprite> --script crowd_sheet.lua
local p = app.params
local strip = Image{ fromFile = p["strip"] }
if not strip then error("cannot read " .. tostring(p["strip"])) end
local fw, fh = tonumber(p["fw"]), tonumber(p["fh"])
local n = strip.width // fw
if n * fw ~= strip.width or strip.height ~= fh then
  error("strip is " .. strip.width .. "x" .. strip.height .. ", not a row of " .. fw .. "x" .. fh .. " frames")
end
local durs = {}
for d in string.gmatch(p["durations"], "[^,]+") do durs[#durs + 1] = tonumber(d) end
if #durs ~= n then error("expected " .. n .. " durations, got " .. #durs) end

local spr = Sprite(fw, fh, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = "Flattened"
for i = 1, n do
  local frame = (i == 1) and spr.frames[1] or spr:newEmptyFrame()
  local img = Image(fw, fh, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0))
  local cel = layer:cel(frame)
  if cel then
    cel.image = img
    cel.position = Point(0, 0)
  else
    spr:newCel(layer, frame, img, Point(0, 0))
  end
  frame.duration = durs[i] / 1000
end
for spec in string.gmatch(p["tags"], "[^,]+") do
  local name, a, b = string.match(spec, "([^:]+):(%d+)-(%d+)")
  local tag = spr:newTag(tonumber(a), tonumber(b))
  tag.name = name
end
spr:saveAs(p["out"])
