-- Read every layer of an .aseprite back out as a full-canvas PNG (for the round-trip check).
--   Aseprite -b --script-param in=<file.aseprite> --script-param dir=<folder> --script jr_unpack.lua
local spr = app.open(app.params["in"])
if not spr then error("cannot open " .. tostring(app.params["in"])) end
local dir = app.params["dir"]
for _, layer in ipairs(spr.layers) do
  local img = Image(spr.width, spr.height, spr.colorMode)
  local cel = layer:cel(spr.frames[1])
  if cel then img:drawImage(cel.image, cel.position) end
  img:saveAs(dir .. "/" .. layer.name .. ".png")
end
