-- Build the layered .aseprite for Jordan's room from the five layer PNGs.
--   Aseprite -b --script-param dir=<folder with the layer PNGs>
--               --script-param layers=room_floor,room_walls,...   (bottom to top)
--               --script-param out=<file.aseprite>
--               --script jr_layers.lua
local dir = app.params["dir"]
local list = app.params["layers"]
local out = app.params["out"]
if not dir or not list or not out then error("need dir, layers and out") end

local names = {}
for name in string.gmatch(list, "[^,]+") do table.insert(names, name) end

local first = Image{ fromFile = dir .. "/" .. names[1] .. ".png" }
local spr = Sprite(first.width, first.height, ColorMode.RGB)
for i, name in ipairs(names) do
  local layer
  if i == 1 then layer = spr.layers[1] else layer = spr:newLayer() end
  layer.name = name
  local img = Image{ fromFile = dir .. "/" .. name .. ".png" }
  if img.width ~= spr.width or img.height ~= spr.height then
    error(name .. " is " .. img.width .. "x" .. img.height)
  end
  spr:newCel(layer, spr.frames[1], img, Point(0, 0))
end
spr:saveAs(out)
