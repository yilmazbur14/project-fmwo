"""Write the maze wall block's approval pass (Jordan's final phase, attack 1).

A bare run writes nothing:

    python vw_export.py                      # print this and exit
    python vw_export.py --check              # build and audit both takes; write nothing
    python vw_export.py --approval           # write the approval files into art_source/void_wall/approval/
    python vw_export.py --approval --out DIR # the same, into DIR (a scratch folder, for tests)

It never writes under Assets/: every target's real path (8.3 names and links resolved) is checked
first, and the ship step, after the user's approval, is not in this script. It never runs Godot
and never writes an .import file.

Two takes of one design:
    void_wall      take A, the contract: 32x36 (a 32x20 top face over a 16-row front), anchor (16,35)
    void_wall_low  take B, the same block with a 10-row front face: 32x30, anchor (16,29)
Each take: <name>.png (8 frames, a horizontal strip), <name>.aseprite (the 8 frames with their
suggested durations and rise / stand / vanish tags, built by the Aseprite CLI from a Lua script,
then re-exported and compared pixel for pixel with the PNG), <name>.gif (the block at 6x),
<name>_maze.gif (the maze rising at game scale), <name>_mock.png and <name>_mock_god.png
(1920x1080). Plus void_wall_frames_8x.png, every frame of both takes. Nothing is written unless
the audit passes.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import vw_block as V  # noqa: E402
import vw_present as P  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = P.ROOT
ART = os.path.join(ROOT, 'art_source')
if ART not in sys.path:
    sys.path.append(ART)
from imgdiff import pixel_diff  # noqa: E402

OUT = os.path.join(HERE, 'approval')
ASEPRITE = os.environ.get('ASEPRITE', r'C:\Program Files (x86)\Steam\steamapps\common\Aseprite\Aseprite.exe')
TAKES = (('void_wall', 16, 'Take A (the contract): 32x36, a 16-row front face'),
         ('void_wall_low', 10, 'Take B (lower): 32x30, a 10-row front face'))


def _real(p):
    return os.path.normcase(os.path.realpath(p))


def _under(path, root):
    p, r = _real(path), _real(root)
    return p == r or p.startswith(r + os.sep)


def guard(out_dir):
    if _under(out_dir, os.path.join(ROOT, 'Assets')):
        raise SystemExit('refusing: %s is inside Assets' % out_dir)


# ------------------------------------------------------------------ audit

def stats(im):
    px = list(im.getdata()) if not hasattr(im, 'get_flattened_data') else list(im.get_flattened_data())
    op = [c for c in px if c[3] > 0]
    return {'opaque': len(op), 'colours': len(set(op)), 'semi': sum(1 for c in px if 0 < c[3] < 255),
            'black': sum(1 for c in op if c[:3] == (0, 0, 0)) / max(1, len(op))}


def audit_take(name, fh):
    """Numbers per frame, and the failures that stop a write."""
    frames = V.frames(fh)
    w, h = V.size(fh)
    ax, ay = V.anchor(fh)
    lines, bad = [], []
    pal = set(V.PAL.values())
    for i, px in enumerate(frames):
        im = P.image(px, fh)
        st = stats(im)
        flat = im.get_flattened_data() if hasattr(im, 'get_flattened_data') else im.getdata()
        extra = set(c for c in flat if c[3] > 0) - pal
        lines.append('  f%d  opaque %4d  colours %2d  black %4.1f%%  semi %d' % (
            i, st['opaque'], st['colours'], 100 * st['black'], st['semi']))
        if st['semi']:
            bad.append('%s f%d: %d semi-alpha px' % (name, i, st['semi']))
        if extra:
            bad.append('%s f%d: colours outside the palette %s' % (name, i, sorted(extra)[:4]))
        if any(not (0 <= x < w and 0 <= y < h) for (x, y) in px):
            bad.append('%s f%d: pixels outside the %dx%d frame' % (name, i, w, h))
    # the solid frames (3: lock, 4: standing): a full opaque block, keyline all round
    for i in (3, 4):
        px = frames[i]
        holes = [(x, y) for x in range(w) for y in range(h) if (x, y) not in px]
        border = [(x, y) for x in range(w) for y in range(h) if x in (0, w - 1) or y in (0, h - 1)]
        not_black = [p for p in border if px.get(p) != 'k']
        if holes:
            bad.append('%s f%d: %d transparent px inside the block' % (name, i, len(holes)))
        if not_black:
            bad.append('%s f%d: %d border px not keyline' % (name, i, len(not_black)))
        if px.get((ax, ay)) != 'k':
            bad.append('%s f%d: the anchor texel is not on the keyline row' % (name, i))
    # rise frames: nothing above the block's top, the floor line lit, the lowest texel on the last row
    for i, hgt in zip((0, 1, 2), V.frames_heights(fh)):
        px = frames[i]
        top = fh - hgt
        above = [p for p in px if p[1] < top]
        if above:
            bad.append('%s f%d: %d px above the rising block' % (name, i, len(above)))
        if max(y for (x, y) in px) != h - 1:
            bad.append('%s f%d: lowest texel not on the last row' % (name, i))
    return frames, lines, bad


def tiling(fh):
    """Blocks edge to edge, side by side and in rows (3 x 3, drawn back to front at 1x): the union
    must have no gap, side seams must be exactly the two keylines, and a block in front must hide
    all of the front face of the block behind it."""
    w, h = V.size(fh)
    px = V.stand(fh)
    cols, rows = 3, 3
    W_, H_ = w * cols, V.TOP * (rows - 1) + h
    canvas = {}
    owner = {}
    for r in range(rows - 1, -1, -1):          # r = rows-1 is the back row, drawn first
        for c in range(cols):
            ox, oy = c * w, (rows - 1 - r) * V.TOP
            for (x, y), k in px.items():
                canvas[(ox + x, oy + y)] = k
                owner[(ox + x, oy + y)] = (c, r, y)
    bad = []
    gaps = [(x, y) for x in range(W_) for y in range(H_) if (x, y) not in canvas]
    if gaps:
        bad.append('tiling: %d gaps, first %s' % (len(gaps), gaps[0]))
    for c in range(1, cols):
        for y in range(H_):
            if canvas.get((c * w - 1, y)) != 'k' or canvas.get((c * w, y)) != 'k':
                bad.append('tiling: side seam at x=%d is not two keylines (row %d)' % (c * w, y))
                break
    shown = [p for p, (c, r, y) in owner.items() if r > 0 and y >= V.TOP]
    if shown:
        bad.append('tiling: %d px of a back block\'s front face show through the block in front' % len(shown))
    # the back row's lit lip sits directly on the front row's keyline
    lip_on_key = all(canvas.get((x, V.TOP - 1)) in 'fg' and canvas.get((x, V.TOP)) == 'k' for x in range(1, w - 1))
    if not lip_on_key:
        bad.append('tiling: the back block\'s lip is not directly above the front block\'s keyline')
    return bad


# ------------------------------------------------------------------ .aseprite

LUA = r'''
local p = app.params
local n, w, h = tonumber(p.n), tonumber(p.w), tonumber(p.h)
local spr = Sprite(w, h, ColorMode.RGB)
local layer = spr.layers[1]
layer.name = "block"
for i = 2, n do spr:newEmptyFrame() end
for i = 1, n do
  local img = Image{ fromFile = p.dir .. "/f" .. (i - 1) .. ".png" }
  spr:newCel(layer, spr.frames[i], img, Point(0, 0))
  spr.frames[i].duration = tonumber(p["d" .. (i - 1)])
end
local t = spr:newTag(1, 4); t.name = "rise"
t = spr:newTag(5, 5); t.name = "stand"
t = spr:newTag(6, 8); t.name = "vanish"
local cols = {}
for c in string.gmatch(p.pal, "[^,]+") do table.insert(cols, c) end
local pal = Palette(#cols + 1)
pal:setColor(0, Color{ r = 0, g = 0, b = 0, a = 0 })
for i, c in ipairs(cols) do
  pal:setColor(i, Color{ r = tonumber(c:sub(1, 2), 16), g = tonumber(c:sub(3, 4), 16), b = tonumber(c:sub(5, 6), 16), a = 255 })
end
spr:setPalette(pal)
spr:saveAs(p.out)
'''


def aseprite(*args):
    r = subprocess.run([ASEPRITE, '-b'] + list(args), capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit('aseprite failed: %s %s' % (r.stdout, r.stderr))
    return r


def build_aseprite(tmp, name, frames, fh):
    """The .aseprite and its round trip; returns (ase path, strip png path)."""
    fdir = os.path.join(tmp, name + '_frames')
    os.makedirs(fdir)
    for i, px in enumerate(frames):
        P.image(px, fh).save(os.path.join(fdir, 'f%d.png' % i))
    lua = os.path.join(tmp, 'build.lua')
    with open(lua, 'w', encoding='utf-8') as f:
        f.write(LUA)
    ase = os.path.join(tmp, name + '.aseprite')
    w, h = V.size(fh)
    pal = ','.join('%02X%02X%02X' % V.PAL[k][:3] for k in 'k12345defg')
    args = []
    for k, v in (('n', V.N), ('w', w), ('h', h), ('dir', fdir.replace('\\', '/')), ('out', ase.replace('\\', '/')),
                 ('pal', pal)):
        args += ['--script-param', '%s=%s' % (k, v)]
    for i, t in enumerate(P.TIMES):
        args += ['--script-param', 'd%d=%s' % (i, t)]
    aseprite(*(args + ['--script', lua]))
    png = os.path.join(tmp, name + '.png')
    P.strip(frames, fh).save(png)
    back = os.path.join(tmp, name + '_rt.png')
    data = os.path.join(tmp, name + '_rt.json')
    aseprite(ase, '--sheet', back, '--sheet-type', 'horizontal', '--data', data, '--format', 'json-array',
             '--list-tags')
    d = pixel_diff(Image.open(png), Image.open(back))
    if d:
        raise SystemExit('%s: the .aseprite does not round-trip: %s' % (name, d))
    with open(data, encoding='utf-8') as f:
        meta = json.load(f)
    durs = [fr['duration'] for fr in meta['frames']]
    want = [int(round(t * 1000)) for t in P.TIMES]
    if durs != want:
        raise SystemExit('%s: frame durations %s, expected %s' % (name, durs, want))
    tags = [(t['name'], t['from'], t['to']) for t in meta['meta']['frameTags']]
    if tags != [('rise', 0, 3), ('stand', 4, 4), ('vanish', 5, 7)]:
        raise SystemExit('%s: tags %s' % (name, tags))
    return ase, png, durs, tags


# ------------------------------------------------------------------ main

def check():
    ok = True
    report = []
    for name, fh, title in TAKES:
        frames, lines, bad = audit_take(name, fh)
        report.append('%s  %dx%d  anchor %s  frames %d' % (name, V.size(fh)[0], V.size(fh)[1], V.anchor(fh), len(frames)))
        report += lines
        bad += tiling(fh)
        for b in bad:
            report.append('  FAIL ' + b)
        ok = ok and not bad
    return ok, report


def write(out_dir):
    guard(out_dir)
    os.makedirs(out_dir, exist_ok=True)
    tmp = tempfile.mkdtemp(prefix='voidwall_')
    written = []
    try:
        takes = []
        for name, fh, title in TAKES:
            frames = V.frames(fh)
            takes.append((title, frames, fh))
            ase, png, durs_ms, tags = build_aseprite(tmp, name, frames, fh)
            print('%s.aseprite: round trip identical; durations %s ms; tags %s' % (name, durs_ms, tags))
            staged = {name + '.png': png, name + '.aseprite': ase}
            ims, durs = P.block_gif_frames(frames, fh)
            g = os.path.join(tmp, name + '.gif')
            P.save_gif(g, ims, durs)
            staged[name + '.gif'] = g
            ims, durs = P.maze_gif_frames(frames, fh)
            g = os.path.join(tmp, name + '_maze.gif')
            P.save_gif(g, ims, durs)
            staged[name + '_maze.gif'] = g
            block = P.image(frames[V.STAND], fh)
            for god, suffix in ((False, '_mock.png'), (True, '_mock_god.png')):
                m = P.mock(block, god=god, caption=title + ('  |  in context: the god and his runes behind' if god else '')
                           + '  |  standing frame, every wall of PLAN section 3')
                path = os.path.join(tmp, name + suffix)
                m.save(path)
                staged[name + suffix] = path
            for dst, src in staged.items():
                target = os.path.join(out_dir, dst)
                guard(target)
                shutil.copyfile(src, target)
                written.append(target)
        sheet = os.path.join(out_dir, 'void_wall_frames_8x.png')
        guard(sheet)
        P.contact(takes).save(sheet)
        written.append(sheet)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return written


def main(argv):
    if not argv or argv[0] not in ('--check', '--approval'):
        print(__doc__)
        return 2
    ok, report = check()
    print('\n'.join(report))
    if not ok:
        print('audit FAILED: nothing written')
        return 1
    if argv[0] == '--approval':
        out = OUT
        if '--out' in argv:
            out = argv[argv.index('--out') + 1]
        for p in write(out):
            print('wrote', p)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
