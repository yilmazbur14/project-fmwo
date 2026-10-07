-- Build an animated, layered .aseprite from per-layer horizontal strips (bottom to top).
--   Aseprite -b --script-param dir=<folder> --script-param layers=kaiju,fx --script-param n=<frames>
--               --script-param w=<frame w> --script-param h=<frame h> --script-param durs=<ms,ms,...>
--               --script-param out=<file.aseprite> --script kjr_layers_anim.lua
local dir = app.params["dir"]
local list = app.params["layers"]
local n = tonumber(app.params["n"])
local w = tonumber(app.params["w"])
local h = tonumber(app.params["h"])
local durs = app.params["durs"]
local out = app.params["out"]
if not (dir and list and n and w and h and durs and out) then error("missing params") end

local names = {}
for name in string.gmatch(list, "[^,]+") do table.insert(names, name) end
local ms = {}
for d in string.gmatch(durs, "[^,]+") do table.insert(ms, tonumber(d)) end

local spr = Sprite(w, h, ColorMode.RGB)
for i = 2, n do spr:newEmptyFrame() end
for i = 1, n do spr.frames[i].duration = (ms[i] or 100) / 1000.0 end
for li, name in ipairs(names) do
  local layer
  if li == 1 then layer = spr.layers[1] else layer = spr:newLayer() end
  layer.name = name
  local strip = Image{ fromFile = dir .. "/" .. name .. ".png" }
  if strip.width ~= w * n or strip.height ~= h then
    error(name .. " strip is " .. strip.width .. "x" .. strip.height)
  end
  for i = 1, n do
    local img = Image(w, h, ColorMode.RGB)
    img:drawImage(strip, Point(-(i - 1) * w, 0))
    spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  end
end
spr:saveAs(out)
