"""APPROVAL PASS (2026-09-29): Josh's card-gates, card hands and poses for his OWN ladder fight.
NOTHING here ships: `python jh_build.py --write` writes into art_source/josh_hands/approval/ only, behind
a guard that refuses any write outside this folder, the scratchpad and the temp folder, any write under
Assets/, and any process but Aseprite. A bare run prints this and writes nothing.

  approval/                 take A ("gilded deck"): every sheet (.png + .aseprite), the GIFs, the mocks,
                            the contact sheet and contract.json (every number the code needs)
  approval/takeB/           take B ("wine deck"): the six hand clips with his wine card backs

Ship names follow the build plan's contract (scratchpad josh_hands/PLAN.md, "Art contract"):
  Hands/josh_hand_<form|hover|windup|drop|impact|shatter>.png, josh_hand_mark.png,
  josh_hand_impact_fx.png (optional), Portals/josh_portal_<open|loop|close|feed>_<back|glow>.png,
  josh_summon.png, josh_command.png.
"""
import json
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jh_lib as H            # noqa: E402
from PIL import Image         # noqa: E402

OUT = H.APPROVAL

LUA = r'''
local src = app.params["src"]
local out = app.params["out"]
local n = tonumber(app.params["n"])
local fw = tonumber(app.params["fw"])
local durs = {}
for d in string.gmatch(app.params["durs"], "[^,]+") do table.insert(durs, tonumber(d)) end
local strip = Image{ fromFile = src }
local fh = strip.height
local spr = Sprite(fw, fh, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = app.params["layer"]
for i = 1, n do
  if i > 1 then spr:newEmptyFrame() end
  local img = Image(fw, fh, ColorMode.RGB)
  img:drawImage(strip, Point(-(i - 1) * fw, 0))
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = durs[((i - 1) % #durs) + 1]
end
local tag = spr:newTag(1, n)
tag.name = app.params["tag"]
spr:saveAs(out)
'''


def write_sprite(tmp, dest_dir, name, im, n, fw, durs, tag, layer):
    """name.png and name.aseprite (n frames of fw, with durations and a tag) into dest_dir, after the
    .aseprite is checked to re-export pixel-identical to the .png."""
    from imgdiff import pixel_diff
    assert im.width == n * fw, (name, im.size, n, fw)
    tpng = os.path.join(tmp, name + '.png')
    tase = os.path.join(tmp, name + '.aseprite')
    im.save(tpng)
    lua = os.path.join(tmp, 'mk.lua')
    if not os.path.exists(lua):
        with open(lua, 'w') as f:
            f.write(LUA)
    subprocess.run([H.ASEPRITE, '-b', '--script-param', 'src=' + tpng, '--script-param', 'out=' + tase,
                    '--script-param', 'n=%d' % n, '--script-param', 'fw=%d' % fw,
                    '--script-param', 'durs=' + ','.join('%.3f' % t for t in durs),
                    '--script-param', 'layer=' + layer, '--script-param', 'tag=' + tag, '--script', lua],
                   check=True, capture_output=True)
    back = os.path.join(tmp, name + '_rt.png')
    subprocess.run([H.ASEPRITE, '-b', tase, '--sheet', back, '--sheet-type', 'horizontal'], check=True,
                   capture_output=True)
    d = pixel_diff(Image.open(tpng), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    for src, ext in ((tpng, '.png'), (tase, '.aseprite')):
        with open(src, 'rb') as f:
            data = f.read()
        with open(os.path.join(dest_dir, name + ext), 'wb') as f:
            f.write(data)
    return os.path.join(dest_dir, name + '.png')


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    H.install_guard()
    import jh_sheets as SH
    tmp = tempfile.mkdtemp(prefix='jh_build_')
    for d in (OUT, os.path.join(OUT, 'takeB')):
        if not os.path.isdir(d):
            os.mkdir(d)
    written = []
    for spec in SH.all_sheets():
        dest = OUT if spec['take'] == 'A' else os.path.join(OUT, 'takeB')
        p = write_sprite(tmp, dest, spec['name'], spec['image'], spec['frames'], spec['fw'], spec['times'],
                         spec['tag'], spec['layer'])
        written.append(os.path.relpath(p, OUT).replace('\\', '/'))
        print('wrote', written[-1], spec['image'].size)
    import jh_previews as PV
    for path in PV.build_all(OUT):
        written.append(os.path.relpath(path, OUT).replace('\\', '/'))
        print('wrote', written[-1])
    contract = SH.contract()
    contract['files'] = written
    with open(os.path.join(OUT, 'contract.json'), 'w') as f:
        json.dump(contract, f, indent=1)
    print('wrote contract.json')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
