-- Replace ONE named layer's cel in frame 1 of an existing .aseprite, leaving every other layer, its
-- order, opacity and blend mode exactly as they are. Used by menu.py for main_menu_bg.aseprite, whose
-- eight layers (sky .. player) are the pipeline's own; only 'members' changes.
--   Aseprite -b --script-param in=<old.aseprite> --script-param layer=<name>
--               --script-param cel=<full-canvas png> --script-param out=<new.aseprite>
--               --script layer_splice.lua
local spr = app.open(app.params["in"])
if not spr then error("cannot open " .. tostring(app.params["in"])) end
local want = app.params["layer"]
local target = nil
for _, l in ipairs(spr.layers) do
  if l.name == want then
    if target then error("two layers named " .. want) end
    target = l
  end
end
if not target then error("no layer named " .. want) end
if #spr.frames ~= 1 then error("expected one frame, found " .. #spr.frames) end
local img = Image{ fromFile = app.params["cel"] }
if img.width ~= spr.width or img.height ~= spr.height then
  error("cel is " .. img.width .. "x" .. img.height .. ", sprite is " .. spr.width .. "x" .. spr.height)
end
local cel = target:cel(spr.frames[1])
if cel then
  cel.image = img
  cel.position = Point(0, 0)
else
  spr:newCel(target, spr.frames[1], img, Point(0, 0))
end
spr:saveAs(app.params["out"])
