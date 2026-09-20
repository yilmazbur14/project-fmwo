"""Builds the punch FX art into Assets/Effects, each PNG with an .aseprite beside it that exports back
pixel-identical, and checks the art against the geometry it has to show.

    python build.py            write punch_swoosh / punch_hit_star (.png + .aseprite), then verify
    python build.py --check    rebuild and compare with the project files; writes nothing

The swoosh's full-extension frame is the v2 punch hitbox drawn out (design.V2_BOXES): its far edge and
both sides are the box's, and no swoosh frame reaches outside it. PlayerScript.PUNCH_HITBOXES_V2 must
stay the same numbers as design.V2_BOXES: verify_defense.gd's punch_reach mode reads the shipped PNG
and fails if the art and the hitbox drift apart.
"""
import os
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image

import design as D
import punchfx_art as A

PROJ = os.path.normpath(os.path.join(HERE, '..', '..')).replace(os.sep, '/') + '/'
FX = PROJ + 'Assets/Effects/'
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
CHECK = '--check' in sys.argv
WORK = os.path.join(tempfile.gettempdir(), 'fmwo_punch_fx_work').replace(os.sep, '/') + '/'
os.makedirs(WORK, exist_ok=True)

DB32 = {
    (0, 0, 0), (34, 32, 52), (69, 40, 60), (102, 57, 49), (143, 86, 59), (223, 113, 38),
    (217, 160, 102), (238, 195, 154), (251, 242, 54), (153, 229, 80), (106, 190, 48),
    (55, 148, 110), (75, 105, 47), (82, 75, 36), (50, 60, 57), (63, 63, 116), (48, 96, 130),
    (91, 110, 225), (99, 155, 255), (95, 205, 228), (203, 219, 252), (255, 255, 255), (155, 173, 183),
    (132, 126, 135), (105, 106, 106), (89, 86, 82), (118, 66, 138), (172, 50, 50), (217, 87, 99),
    (215, 123, 186), (143, 151, 74), (138, 111, 48),
}

# Frame durations for the .aseprite previews only. In the game the swoosh follows the player's own
# punch columns and the star counts PunchFx.STAR_FRAME_TIMES.
SWOOSH_MS = [83, 100, 67]
STAR_MS = [50, 50, 60]

LUA = r'''
local spec = app.params["spec"]
local lines = {}
for line in io.lines(spec) do
  if #line > 0 then table.insert(lines, line) end
end
local function split(s, sep)
  local out = {}
  for piece in string.gmatch(s, "([^" .. sep .. "]+)") do table.insert(out, piece) end
  return out
end
local head = split(lines[1], "|")
local spr = Sprite(tonumber(head[2]), tonumber(head[3]), ColorMode.RGB)
spr.layers[1].name = head[4]
local frameCount = 0
for i = 2, #lines do
  local parts = split(lines[i], "|")
  if parts[1] == "TAG" then
    local tag = spr:newTag(tonumber(parts[3]), tonumber(parts[4]))
    tag.name = parts[2]
  else
    frameCount = frameCount + 1
    local frame
    if frameCount == 1 then frame = spr.frames[1] else frame = spr:newEmptyFrame() end
    frame.duration = tonumber(parts[1]) / 1000.0
    spr:newCel(spr.layers[1], frame, Image{ fromFile = parts[2] }, Point(0, 0))
  end
end
spr:saveAs(head[1])
spr:close()
'''


def pixels(img):
    """Every pixel, row by row (Pillow 12 renamed getdata)."""
    flat = getattr(img, 'get_flattened_data', None)
    return list(flat() if flat else img.getdata())


def cells(sheet, w, h):
    """Row-major cells of a grid sheet."""
    return [sheet.crop((x * w, y * h, x * w + w, y * h + h))
            for y in range(sheet.height // h) for x in range(sheet.width // w)]


def check_pixels(name, img):
    bad_alpha = {p[3] for p in pixels(img) if p[3] not in (0, 255)}
    assert not bad_alpha, (name, 'partial alpha', bad_alpha)
    colours = {p[:3] for p in pixels(img) if p[3] == 255}
    assert colours <= DB32, (name, 'off-palette', colours - DB32)


def check_swoosh(sheet):
    half = A.SWOOSH_CELL // 2
    for facing in range(4):
        x, y, w, h = D.V2_BOXES[facing]
        box = (x + half, y + half, x + w + half, y + h + half)
        for frame in range(len(D.SWOOSH)):
            cell = sheet.crop((frame * A.SWOOSH_CELL, facing * A.SWOOSH_CELL,
                               (frame + 1) * A.SWOOSH_CELL, (facing + 1) * A.SWOOSH_CELL))
            used = cell.getbbox()
            assert used, (facing, frame, 'empty')
            inside = box[0] <= used[0] and box[1] <= used[1] and used[2] <= box[2] and used[3] <= box[3]
            assert inside, ('swoosh outside its reach box', D.FACINGS[facing], frame, used, box)
        # Full extension: the far edge and both sides are the box's own.
        cell = sheet.crop((A.SWOOSH_CELL, facing * A.SWOOSH_CELL, 2 * A.SWOOSH_CELL, (facing + 1) * A.SWOOSH_CELL))
        used = cell.getbbox()
        if facing == 3:
            same = used[2] == box[2] and used[1] == box[1] and used[3] == box[3]
        elif facing == 2:
            same = used[0] == box[0] and used[1] == box[1] and used[3] == box[3]
        elif facing == 1:
            same = used[1] == box[1] and used[0] == box[0] and used[2] == box[2]
        else:
            same = used[3] == box[3] and used[0] == box[0] and used[2] == box[2]
        assert same, ('full-extension swoosh does not span its box', D.FACINGS[facing], used, box)
    # The left punch is the right one mirrored, as the player's sheet draws it.
    for frame in range(len(D.SWOOSH)):
        left = sheet.crop((frame * 48, 2 * 48, frame * 48 + 48, 3 * 48))
        right = sheet.crop((frame * 48, 3 * 48, frame * 48 + 48, 4 * 48)).transpose(Image.FLIP_LEFT_RIGHT)
        # A 48-texel cell mirrors about its centre line; the player's 32-texel frames share that centre.
        assert pixels(left) == pixels(right), ('left is not right mirrored', frame)


def check_star(sheet):
    for i, cell in enumerate(cells(sheet, A.STAR_CELL, A.STAR_CELL)):
        assert cell.getbbox(), ('empty star frame', i)
        for flipped in (cell.transpose(Image.FLIP_LEFT_RIGHT), cell.transpose(Image.FLIP_TOP_BOTTOM),
                        cell.transpose(Image.TRANSPOSE)):
            assert pixels(flipped) == pixels(cell), ('star frame not symmetric', i)


def build_ase(out_path, frames, w, h, layer, durations, tags):
    key = os.path.splitext(os.path.basename(out_path))[0]
    target = WORK + key + '_check.aseprite' if CHECK else out_path
    lines = ['%s|%d|%d|%s' % (target, w, h, layer)]
    for i, (img, ms) in enumerate(zip(frames, durations)):
        fp = WORK + '%s_f%02d.png' % (key, i)
        img.save(fp)
        lines.append('%d|%s' % (ms, fp))
    for name, a, b in tags:
        lines.append('TAG|%s|%d|%d' % (name, a, b))
    spec = WORK + key + '_spec.txt'
    with open(spec, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    lua = WORK + 'make_ase.lua'
    with open(lua, 'w') as f:
        f.write(LUA)
    if os.path.exists(target) and CHECK:
        os.remove(target)
    r = subprocess.run([ASEPRITE, '-b', '--script-param', 'spec=' + spec, '--script', lua],
                       capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert os.path.exists(target), (target, r.stdout, r.stderr)


def round_trip(ase_path, sheet, columns):
    """Aseprite's own export of the .aseprite must be the PNG, pixel for pixel."""
    back = WORK + os.path.basename(ase_path) + '_roundtrip.png'
    if os.path.exists(back):
        os.remove(back)
    subprocess.run([ASEPRITE, '-b', ase_path, '--sheet', back, '--sheet-type', 'rows',
                    '--sheet-columns', str(columns)], capture_output=True, text=True, stdin=subprocess.DEVNULL)
    rt = Image.open(back).convert('RGBA')
    assert rt.size == sheet.size, ('round trip size', ase_path, rt.size, sheet.size)
    assert pixels(rt) == pixels(sheet), ('round trip pixels differ', ase_path)


def emit(sheet, path):
    if CHECK:
        disk = Image.open(path).convert('RGBA')
        assert disk.size == sheet.size and pixels(disk) == pixels(sheet), ('differs from project', path)
        return
    sheet.save(path)


def main():
    swoosh = A.swoosh_sheet()
    check_pixels('punch_swoosh', swoosh)
    check_swoosh(swoosh)
    star = A.star_sheet()
    check_pixels('punch_hit_star', star)
    check_star(star)

    emit(swoosh, FX + 'punch_swoosh.png')
    emit(star, FX + 'punch_hit_star.png')

    swoosh_frames = cells(swoosh, A.SWOOSH_CELL, A.SWOOSH_CELL)
    tags = [('swoosh_' + name, 1 + 3 * i, 3 + 3 * i) for i, name in enumerate(D.FACINGS)]
    build_ase(FX + 'punch_swoosh.aseprite', swoosh_frames, A.SWOOSH_CELL, A.SWOOSH_CELL, 'punch_swoosh',
              SWOOSH_MS * 4, tags)
    star_frames = cells(star, A.STAR_CELL, A.STAR_CELL)
    build_ase(FX + 'punch_hit_star.aseprite', star_frames, A.STAR_CELL, A.STAR_CELL, 'punch_hit_star',
              STAR_MS * 2, [('hit', 1, 3), ('charged', 4, 6)])

    for name, sheet, columns in (('punch_swoosh', swoosh, 3), ('punch_hit_star', star, 3)):
        round_trip(WORK + name + '_check.aseprite' if CHECK else FX + name + '.aseprite', sheet, columns)
        if CHECK:
            round_trip(FX + name + '.aseprite', sheet, columns)
    print('%s punch_swoosh %dx%d, punch_hit_star %dx%d: palette, reach boxes, symmetry and .aseprite round trips OK'
          % ('checked' if CHECK else 'wrote', swoosh.width, swoosh.height, star.width, star.height))


if __name__ == '__main__':
    main()
