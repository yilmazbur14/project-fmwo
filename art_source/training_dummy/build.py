"""Builds the controls room's sparring dummy into Assets/Characters/TrainingDummy, each PNG with a
_3x companion and an .aseprite beside it that exports back pixel-identical, and checks the art
against the numbers the room drives it with.

    python build.py            write training_dummy / training_dummy_switch, then verify
    python build.py --check    rebuild and compare with the project files; writes nothing

Scripts/TrainingDummyArtLayout.gd is the contract and this reads it. The cell, the frame count and
every pose angle are asserted equal to design.py's copies, so a redraw cannot quietly drift from what
the room animates. The numbers this redraw MOVES - ANCHOR, SORT_POINT, the pivot, the shoulder, the
four boxes and the anchors hanging off them - are printed instead of asserted while the .gd still
holds the first pass's, because the sheet has to be buildable before a coder has applied them. Once
they are applied that block disappears and they are enforced like everything else.

It also measures the house standard the room sets rather than describing it. Every colour has to be
one of the nineteen in the shipped controls_bg.png, the keyline has to be as thin as the room's own
(share of black pixels sitting in a 2x2 block of black), the attack boxes have to agree with what the
drawing actually reaches, and nothing may fall outside its cell - which is not cosmetic: a pixel past
the cell edge is dropped, and a frame that reaches past it is cut in half on the sheet.

On the black-pixel share: it rises as a figure gets smaller, because the keyline stays one pixel wide
while the area it encloses shrinks. This body is about a third of danny.png's area, where pure
scaling would put it near 0.46; it comes in under 0.30. The size-free test is the 2x2 one.
"""
import ast
import os
import re
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from PIL import Image

import design as D

PROJ = os.path.normpath(os.path.join(HERE, '..', '..')).replace(os.sep, '/') + '/'
OUT = PROJ + 'Assets/Characters/TrainingDummy/'
LAYOUT = PROJ + 'Scripts/TrainingDummyArtLayout.gd'
ROOM_BG = PROJ + 'Assets/Environment/controls_bg.png'
ASEPRITE = 'C:/Program Files (x86)/Steam/steamapps/common/Aseprite/Aseprite.exe'
CHECK = '--check' in sys.argv
WORK = os.path.join(tempfile.gettempdir(), 'fmwo_training_dummy_work').replace(os.sep, '/') + '/'
os.makedirs(WORK, exist_ok=True)

DB32 = {
    (0, 0, 0), (34, 32, 52), (69, 40, 60), (102, 57, 49), (143, 86, 59), (223, 113, 38),
    (217, 160, 102), (238, 195, 154), (251, 242, 54), (153, 229, 80), (106, 190, 48),
    (55, 148, 110), (75, 105, 47), (82, 75, 36), (50, 60, 57), (63, 63, 116), (48, 96, 130),
    (91, 110, 225), (99, 155, 255), (95, 205, 228), (203, 219, 252), (255, 255, 255), (155, 173, 183),
    (132, 126, 135), (105, 106, 106), (89, 86, 82), (118, 66, 138), (172, 50, 50), (217, 87, 99),
    (215, 123, 186), (143, 151, 74), (138, 111, 48),
}
# The room's own props sit at 0.045 (controls_bg) to 0.094 (mason.png); Greyson, drawn to the
# character target rather than the room's, is 0.202. A prop in this room belongs at the low end.
MAX_FAT_KEYLINE = 0.12

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


# ---------------------------------------------------------------- reading the contract
def gd_source():
    with open(LAYOUT, encoding='utf-8') as f:
        return f.read()


def gd_const(src, name):
    """The right-hand side of `const NAME := ...`, as Python."""
    m = re.search(r'^const %s\s*:=\s*(.+)$' % name, src, re.M)
    assert m, ('no such const', name)
    text = m.group(1)
    text = re.sub(r'Vector2\(([^()]*)\)', r'(\1)', text)
    text = re.sub(r'Rect2\(([^()]*)\)', r'(\1)', text)
    return ast.literal_eval(text)


def gd_poses(src):
    body = src[src.index('const PLACEHOLDER_POSES'):]
    body = body[body.index('{'):body.index('\n}') + 1]
    poses = {}
    for line in body.splitlines():
        m = re.match(r'\s*(\d+):\s*\{lean = ([-\d.]+), arm = ([-\d.]+), tip = ([-\d.]+)\}', line)
        if m:
            poses[int(m.group(1))] = (float(m.group(2)), float(m.group(3)), float(m.group(4)))
    return poses


def check_contract():
    """What must be true no matter what, and what is still waiting on the layout being updated.

    The cell, the frame count and the pose angles are hard asserts: they are what the room drives the
    sheet with and a mismatch means the wrong art. The numbers the redraw moves - ANCHOR, SORT_POINT,
    the four boxes and the anchors hanging off them - are reported instead, with the values to apply,
    because the sheet has to be buildable before a coder has touched the .gd.
    """
    src = gd_source()
    frame = gd_const(src, 'FRAME_SIZE')
    assert frame == (D.FRAME, D.FRAME), ('FRAME_SIZE', frame)
    assert gd_const(src, 'SHEET_FRAMES') == D.SHEET_FRAMES
    assert gd_const(src, 'SWITCH_FRAME_SIZE') == (D.SWITCH_W, D.SWITCH_H), 'SWITCH_FRAME_SIZE'
    names = sorted(set(sum([list(a['frames']) for a in gd_anims(src)], [])))
    assert names == list(range(D.SHEET_FRAMES)), ('the anims use frames %s' % names)

    # angles are size-free, so these have to match today
    poses = gd_poses(src)
    assert sorted(poses) == sorted(D.POSES), 'PLACEHOLDER_POSES frame numbers'
    for i, (lean, arm, tip) in poses.items():
        mine = D.POSES[i]
        assert (arm, tip) == (mine[1], mine[2]), ('pose %d arm/tip' % i, (arm, tip), mine[1:])
        assert lean == mine[0], ('pose %d lean' % i, lean, mine[0])

    # Layout.frame_texel is `point - FRAME_SIZE / 2 + SPRITE_OFFSET` and SPRITE_OFFSET is
    # `FRAME_SIZE / 2 - ANCHOR + SORT_POINT`, so origin = frame - ANCHOR + SORT_POINT.
    want = dict(D.PROPOSAL)
    origin = (want['ANCHOR'][0] - want['SORT_POINT'][0], want['ANCHOR'][1] - want['SORT_POINT'][1])
    assert origin == D.FRAME_ORIGIN, ('the proposal disagrees with the drawing', origin, D.FRAME_ORIGIN)
    assert want['ANCHOR'][0] == D.FRAME / 2, 'the dummy must be centred across its cell'
    assert want['ANCHOR'][1] - origin[1] == D.ANCHOR_Y
    for name, mine in (('HURT_BOX', D.HURT_BOX), ('BODY_BOX', D.BODY_BOX)):
        x, y, w, h = want[name]
        assert (x - origin[0], y - origin[1], w, h) == mine, ('the proposal disagrees on ' + name)
    for name, mine in (('PLACEHOLDER_PIVOT', D.PIVOT), ('PLACEHOLDER_SHOULDER', D.SHOULDER)):
        assert want[name] == tuple(int(v) for v in mine), ('the proposal disagrees on ' + name)

    pending = []
    for name, value in want.items():
        try:
            live = gd_const(src, name)
        except AssertionError:
            live = None
        if live != value:
            pending.append((name, live, value))
    lean_scale = D.LEAN_SCALE != 1.0
    return src, pending, lean_scale


# ---------------------------------------------------------------- writing the contract back out
def gd_number(value):
    """A number written so that reading it back gives this exact float.

    The printed block is the contract between this file and whoever applies it, so a value that
    cannot be transcribed faithfully is a defect in the contract, not a display nicety. The first
    version rounded to two places: a lean of 0.325 was published as 0.33, applied literally, and
    moved a pixel. --check happened to catch that one, but a value that rounded to within the
    checks' tolerance would have shipped a silent drift instead.

    Python's repr is the shortest decimal that round-trips a double and GDScript parses doubles the
    same way, so repr is usually the answer; an exponent form is not something to paste into a .gd,
    so those fall back to plain decimals at whatever precision it takes.
    """
    if isinstance(value, int) or (isinstance(value, float) and value.is_integer()
                                  and abs(value) < 1e15 and repr(value).endswith('.0')):
        return repr(value) if isinstance(value, float) else str(value)
    text = repr(float(value))
    if 'e' in text or 'E' in text:
        for digits in range(1, 18):
            text = '%.*f' % (digits, value)
            if float(text) == float(value):
                break
    assert re.fullmatch(r'-?\d+(\.\d+)?', text), ('not a number to paste into a .gd', value, text)
    assert float(text) == float(value), ('cannot write this number down faithfully', value, text)
    return text


def gd_value(value):
    if isinstance(value, tuple):
        kind = {2: 'Vector2', 4: 'Rect2'}[len(value)]
        return '%s(%s)' % (kind, ', '.join(gd_number(v) for v in value))
    return gd_number(value)


def pose_line(index):
    lean, arm, tip = D.POSES[index]
    return '{lean = %s, arm = %s, tip = %s}' % (
        gd_number(D.scaled_lean(lean)), gd_number(arm), gd_number(tip))


def check_printer():
    """Feed the printer's own output back through the reader. What it publishes has to parse to the
    numbers the sheet was drawn with, or applying the block introduces the drift it exists to
    prevent."""
    for name, value in D.PROPOSAL.items():
        text = gd_value(value)
        assert gd_const('const %s := %s\n' % (name, text), name) == value, \
            ('the printer does not round-trip', name, text)
    lines = ['const PLACEHOLDER_POSES := {']
    lines += ['\t%d: %s,' % (i, pose_line(i)) for i in sorted(D.POSES)]
    lines.append('}')
    back = gd_poses('\n'.join(lines))
    want = {i: (D.scaled_lean(lean), arm, tip) for i, (lean, arm, tip) in D.POSES.items()}
    assert back == want, ('the pose printer does not round-trip', back, want)


def report_pending(pending, lean_scale):
    if not pending and not lean_scale:
        print('  contract: the cell, the poses and every box in TrainingDummyArtLayout.gd match')
        return
    print('  LAYOUT NOT YET UPDATED - the sheet is drawn to the redraw, the .gd still has the first')
    print('  pass. Apply these to Scripts/TrainingDummyArtLayout.gd verbatim - the numbers are')
    print('  written to round-trip exactly, so transcribe them as printed:')
    for name, live, value in pending:
        print('    %-22s %-26s  (was %s)' % (name, gd_value(value), gd_value(live) if live else live))
    if lean_scale:
        print('    PLACEHOLDER_POSES      every `lean` x %s, as below, then set '
              'design.LEAN_SCALE to 1.0' % gd_number(D.LEAN_SCALE))
        for i in sorted(D.POSES):
            print('      %2d: %s,' % (i, pose_line(i)))


def gd_anims(src):
    body = src[src.index('const ANIMS'):]
    body = body[:body.index('\n}') + 1]
    out = []
    for m in re.finditer(r'&"(\w+)":\s*\{frames = \[([\d, ]+)\], times = \[([\d., ]+)\]', body):
        frames = [int(v) for v in m.group(2).split(',')]
        times = [float(v) for v in m.group(3).split(',')]
        out.append(dict(name=m.group(1), frames=frames, times=times))
    return out


# ---------------------------------------------------------------- drawing
def img_of(grid, w, h):
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = im.load()
    for y in range(h):
        for x in range(w):
            ch = grid[y][x]
            if ch != ' ':
                px[x, y] = D.PAL[ch] + (255,)
    return im


def dummy_frames():
    return [img_of(D.frame_grid(i), D.FRAME, D.FRAME) for i in range(D.SHEET_FRAMES)]


def switch_frames():
    return [img_of(D.post_grid(sp), D.SWITCH_W, D.SWITCH_H) for sp in (False, True)]


def strip(frames):
    w, h = frames[0].size
    sheet = Image.new('RGBA', (w * len(frames), h), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * w, 0))
    return sheet


def pixels(img):
    return list(img.get_flattened_data())


# ---------------------------------------------------------------- checks
def room_palette():
    bg = Image.open(ROOM_BG).convert('RGBA')
    return {p[:3] for p in pixels(bg) if p[3] == 255}


def check_pixels(name, img, room):
    bad_alpha = {p[3] for p in pixels(img) if p[3] not in (0, 255)}
    assert not bad_alpha, (name, 'partial alpha', bad_alpha)
    used = {p[:3] for p in pixels(img) if p[3] == 255}
    assert used <= DB32, (name, 'off-palette', used - DB32)
    assert used <= room, (name, 'not a colour the locker room is drawn with', used - room)


def fat_keyline(img):
    """The share of black pixels sitting in a 2x2 block of black: how thick the keyline runs."""
    w, h = img.size
    px = img.load()

    def blk(x, y):
        if not (0 <= x < w and 0 <= y < h):
            return False
        q = px[x, y]
        return q[3] == 255 and q[:3] == (0, 0, 0)

    n = fat = 0
    for y in range(h):
        for x in range(w):
            if blk(x, y):
                n += 1
                if any(blk(x + dx, y) and blk(x, y + dy) and blk(x + dx, y + dy)
                       for dx in (-1, 1) for dy in (-1, 1)):
                    fat += 1
    return n, fat / max(n, 1)


def check_cells(name, frames, floor_row=None):
    for i, f in enumerate(frames):
        box = f.getbbox()
        assert box, (name, i, 'empty frame')
        assert box[0] >= 0 and box[1] >= 0 and box[2] <= f.width and box[3] <= f.height, (name, i, box)
        # every drawn pixel is fenced by the keyline, so nothing may sit on the cell edge either
        assert box[0] >= 0 and box[2] <= f.width and box[3] <= f.height, (name, i, 'on the edge', box)
        if floor_row is not None:
            assert box[3] <= floor_row + 1, (name, i, 'drawn below the floor', box)


def check_anchor(frames):
    """The base stands on ANCHOR in every frame, because it is bolted down and never moves. Its body
    ends one row above the floor and its keyline lands on it."""
    floor = D.ANCHOR_Y + D.FRAME_ORIGIN[1]
    for i, f in enumerate(frames):
        px = f.load()
        bottom = max(y for y in range(f.height) for x in range(f.width) if px[x, y][3] == 255)
        assert bottom == floor, (i, 'the base does not stand on ANCHOR', bottom, floor)


def check_hurtbox(frames):
    """The idle frame's barrel is exactly as wide as HURT_BOX, which is what makes a punch that
    connects look like it connected."""
    x, y, w, h = D.HURT_BOX
    left = x + D.FRAME_ORIGIN[0]
    # the widest row of the leather itself: measured from the barrel's own profile rather than from
    # a sampled row of the sheet, because on the sheet the arm crosses most of them
    widest = max(D.BARREL_HW)
    assert widest * 2 == w, ('the barrel is not HURT_BOX wide', widest * 2, w)
    # and the sheet agrees, on a row the arm is clear of
    row = D.BARREL_HW.index(widest) + D.BARREL_TOP + D.FRAME_ORIGIN[1]
    px = frames[0].load()
    lit = [cx for cx in range(D.FRAME) if px[cx, row][3] == 255 and px[cx, row][:3] != (0, 0, 0)]
    assert lit and min(lit) == left and max(lit) == left + w - 1, \
        ('the drawn barrel does not fill HURT_BOX', min(lit), max(lit), left, left + w - 1)


def drawn_reach(index):
    """How far the drawing itself gets from the origin along the way it faces, in texels."""
    pose = D.Pose(index)
    best = -99.0
    for py in range(D.FRAME):
        for px in range(D.FRAME):
            p = D.to_origin(px, py)
            if D.in_arm(pose.unarm(p)) or D.in_barrel(pose.unfigure(p)):
                best = max(best, p[0])
    return best


def check_reach():
    """The attack boxes and the drawing have to agree, which is half the point of the redraw: at the
    first pass's size the boxes reached a dozen texels past anything a 64-wide cell could draw. The
    swing is the padded arm, measured on the strike frames; the lunge is the whole body thrown
    forward, so LUNGE_PUSH counts toward it."""
    out = []
    for name, box, frames, push in (
            ('swing', D.PROPOSAL['SWING_BOX'], (6, 7), 0.0),
            ('lunge', D.PROPOSAL['LUNGE_BOX'], (11, 12), D.PROPOSAL['LUNGE_PUSH'])):
        reach = (box[0] + box[2]) * 3.0
        drawn = max(drawn_reach(i) + push for i in frames) * 3.0
        assert abs(drawn - reach) <= 12.0, \
            ('the %s box and the %s drawing are more than four texels apart' % (name, name),
             drawn, reach)
        out.append((name, drawn, reach))
    return out


# ---------------------------------------------------------------- writing
def emit(img, path):
    if CHECK:
        disk = Image.open(path).convert('RGBA')
        assert disk.size == img.size and pixels(disk) == pixels(img), ('differs from project', path)
        return
    img.save(path)


def emit_3x(img, path):
    emit(img.resize((img.width * 3, img.height * 3), Image.NEAREST), path)


def build_ase(out_path, frames, durations_ms, layer, tags):
    key = os.path.splitext(os.path.basename(out_path))[0]
    target = WORK + key + '_check.aseprite' if CHECK else out_path
    w, h = frames[0].size
    lines = ['%s|%d|%d|%s' % (target, w, h, layer)]
    for i, (img, ms) in enumerate(zip(frames, durations_ms)):
        fp = WORK + '%s_f%02d.png' % (key, i)
        img.save(fp)
        lines.append('%d|%s' % (ms, fp))
    for tag_name, a, b in tags:
        lines.append('TAG|%s|%d|%d' % (tag_name, a, b))
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
    return target


def round_trip(ase_path, sheet, columns):
    back = WORK + os.path.basename(ase_path) + '_roundtrip.png'
    if os.path.exists(back):
        os.remove(back)
    subprocess.run([ASEPRITE, '-b', ase_path, '--sheet', back, '--sheet-type', 'rows',
                    '--sheet-columns', str(columns)], capture_output=True, text=True,
                   stdin=subprocess.DEVNULL)
    rt = Image.open(back).convert('RGBA')
    assert rt.size == sheet.size, ('round trip size', ase_path, rt.size, sheet.size)
    assert pixels(rt) == pixels(sheet), ('round trip pixels differ', ase_path)


def dummy_durations(src):
    """A frame's .aseprite duration is the time the room's own animation table gives it. Frames the
    table shows once keep that time; the sheet is a strip, so this is only for scrubbing in
    Aseprite."""
    out = [100] * D.SHEET_FRAMES
    for anim in gd_anims(src):
        for i, frame in enumerate(anim['frames']):
            out[frame] = int(round(anim['times'][min(i, len(anim['times']) - 1)] * 1000))
    return out


def dummy_tags(src):
    """One tag per animation, but only where its frames are a contiguous run - which, in this
    sheet's order, is all of them."""
    tags = []
    for anim in gd_anims(src):
        frames = anim['frames']
        if frames == list(range(frames[0], frames[-1] + 1)):
            tags.append((anim['name'], frames[0] + 1, frames[-1] + 1))
    return tags


def main():
    check_printer()
    src, pending, lean_scale = check_contract()
    room = room_palette()
    if not CHECK:
        os.makedirs(OUT, exist_ok=True)

    frames = dummy_frames()
    sheet = strip(frames)
    check_pixels('training_dummy', sheet, room)
    check_cells('training_dummy', frames, floor_row=D.ANCHOR_Y + D.FRAME_ORIGIN[1])
    check_anchor(frames)
    check_hurtbox(frames)
    reaches = check_reach()
    black, fat = fat_keyline(sheet)
    assert fat <= MAX_FAT_KEYLINE, ('keyline too thick for this room', fat)

    posts = switch_frames()
    post_sheet = strip(posts)
    check_pixels('training_dummy_switch', post_sheet, room)
    check_cells('training_dummy_switch', posts)

    emit(sheet, OUT + 'training_dummy.png')
    emit_3x(sheet, OUT + 'training_dummy_3x.png')
    emit(post_sheet, OUT + 'training_dummy_switch.png')
    emit_3x(post_sheet, OUT + 'training_dummy_switch_3x.png')

    ase = build_ase(OUT + 'training_dummy.aseprite', frames, dummy_durations(src),
                    'training_dummy', dummy_tags(src))
    post_ase = build_ase(OUT + 'training_dummy_switch.aseprite', posts, [500, 500],
                         'training_dummy_switch', [('bag', 1, 1), ('spar', 2, 2)])
    round_trip(ase, sheet, D.SHEET_FRAMES)
    round_trip(post_ase, post_sheet, D.SWITCH_FRAMES)
    if CHECK:
        round_trip(OUT + 'training_dummy.aseprite', sheet, D.SHEET_FRAMES)
        round_trip(OUT + 'training_dummy_switch.aseprite', post_sheet, D.SWITCH_FRAMES)

    opaque = sum(1 for p in pixels(sheet) if p[3] == 255)
    colours = len({p[:3] for p in pixels(sheet) if p[3] == 255})
    print('%s training_dummy %dx%d (%d frames), training_dummy_switch %dx%d'
          % ('checked' if CHECK else 'wrote', sheet.width, sheet.height, D.SHEET_FRAMES,
             post_sheet.width, post_sheet.height))
    print('  body %d texels tall, %d px on screen at SCALE 3' % (D.ANCHOR_Y + 26, (D.ANCHOR_Y + 26) * 3))
    print('  house standard: %d colours, all of them among the %d in controls_bg.png; '
          'black %.4f of opaque; keyline in a 2x2 block %.3f (the room runs 0.045-0.094)'
          % (colours, len(room), black / opaque, fat))
    for name, drawn, reach in reaches:
        print('  %-5s box reaches %.0f px, the drawing reaches %.0f px' % (name, reach, drawn))
    print('  every frame inside its cell, the base on ANCHOR, the barrel HURT_BOX wide, '
          '.aseprite round trips exact, the layout printer round trips exact')
    report_pending(pending, lean_scale)


if __name__ == '__main__':
    main()
