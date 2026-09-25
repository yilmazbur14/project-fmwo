-- Replace ONE frame's cel in an existing .aseprite, leaving every other frame, the layer, the frame
-- durations and the tags exactly as they are. Used by ladder.py for rank_icons.aseprite.
--   Aseprite -b --script-param in=<old.aseprite> --script-param cell=<cell.png>
--               --script-param frame=<1-based frame> --script-param out=<new.aseprite>
--               --script ladder_splice.lua
local spr = app.open(app.params["in"])
if not spr then error("cannot open " .. tostring(app.params["in"])) end
local n = tonumber(app.params["frame"])
if #spr.layers ~= 1 then error("expected one layer, found " .. #spr.layers) end
local layer = spr.layers[1]
local frame = spr.frames[n]
if not frame then error("no frame " .. n) end
local img = Image{ fromFile = app.params["cell"] }
local cel = layer:cel(frame)
if cel then
  cel.image = img
  cel.position = Point(0, 0)
else
  spr:newCel(layer, frame, img, Point(0, 0))
end
spr:saveAs(app.params["out"])
