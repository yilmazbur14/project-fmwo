"""SKETCH ONLY (not part of the approval pass): a maze wall block rising out of the void floor, for
attack 1's walls. The plan's contract (jordan_puppet_master/PLAN.md section 7): void_wall, 32x36
texels (a 32x20 top face and a 16-row front), anchor (16, 35) on the front edge's centre at the
block's bottom edge; rise 0-3, stand 4, vanish 5-7; obsidian with rune-blue edges like his runes.

  rise 0-3   a rune seam burns open round the tile, the block pushes up through it, sparks
  stand 4    the block: polished obsidian top lit on its far edge by the rune light, a darker
             front with a glowing glyph
  vanish 5-7 the edges flare, the body dissolves in a checker, a dotted blue ghost of the edges
             is the last thing left (then the engine hides it)

A bare run writes nothing; `python jp_wall_sketch.py --write` writes into this folder only.
"""
import math
import os
import random
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
PUP = os.path.dirname(HERE)
sys.path.insert(0, PUP)
import jp_rig as R  # noqa: E402,F401
import jg_base as B  # noqa: E402
import jg_void as V  # noqa: E402
from jg_lord_pal import LORD  # noqa: E402
from PIL import Image, ImageDraw  # noqa: E402

W, H = 32, 36
ANCHOR = (16, 35)
TOP_H = 20
PAL = {k: LORD[k] for k in ('k', '1', '2', '3', '4', '5')}
PAL.update({'d': B.hx('17385A'), 'e': B.hx('2B6C99'), 'f': B.hx('66C6EC'), 'g': B.hx('D2F6FF')})
TIMES = [0.05, 0.05, 0.05, 0.08, 1.0, 0.06, 0.06, 0.08]


def block():
    """The standing block, {pixel: key}."""
    px = {}
    rnd = random.Random(7)
    for y in range(H):
        for x in range(W):
            edge = x in (0, W - 1) or y in (0, H - 1) or y == TOP_H
            if edge:
                px[(x, y)] = 'k'
                continue
            if y < TOP_H:
                # the top face: polished obsidian, a bevel lit blue on the far edge by the runes
                if y == 1:
                    k = 'f' if 2 <= x <= W - 3 else 'e'
                elif x == 1:
                    k = 'e' if y < TOP_H - 3 else '4'
                elif x == W - 2:
                    k = '2'
                elif y == TOP_H - 1:
                    k = '5'                       # the near edge catches the light
                else:
                    k = '3'
                    if (x + 2 * y) % 11 == 0 and 3 < x < W - 4:
                        k = '4'                   # polish streaks
                px[(x, y)] = k
            else:
                # the front face: darker, a crack or two, a rune glyph burning cold
                k = '2'
                if y == TOP_H + 1:
                    k = '4'
                elif y >= H - 3:
                    k = '1'
                elif x == 1:
                    k = '3'
                elif x == W - 2:
                    k = '1'
                px[(x, y)] = k
    # etched ring on the top face
    for a in range(0, 360, 9):
        x = int(round(15.5 + 8.5 * math.cos(math.radians(a))))
        y = int(round(9.5 + 5.0 * math.sin(math.radians(a))))
        if px.get((x, y)) in ('3', '4'):
            px[(x, y)] = '2'
    # cracks in the front
    for (x0, y0, x1, y1) in ((6, 22, 8, 32), (25, 22, 23, 30)):
        for q in B.line(x0, y0, x1, y1):
            if px.get(q) not in ('k', None):
                px[q] = '1'
    # the glyph: a stave with two arms, like the runes' own marks
    for q in B.line(15, 23, 15, 31) + B.line(16, 23, 16, 31):
        px[q] = 'f'
    for q in B.line(12, 25, 15, 27) + B.line(19, 25, 16, 27):
        px[q] = 'e'
    px[(15, 23)] = px[(16, 23)] = 'g'
    return px


def seam(heat):
    """The floor seam round the block's footprint (the 32x20 floor tile its bottom sits on)."""
    out = {}
    y0 = H - TOP_H          # 16: the tile's far edge in the frame
    for x in range(W):
        for y in (y0, H - 1):
            out[(x, y)] = 'g' if heat > 0.8 and 10 < x < 22 else 'f' if heat > 0.5 else 'e'
    for y in range(y0, H):
        for x in (0, W - 1):
            out[(x, y)] = 'f' if heat > 0.5 else 'e'
    return out


def frame(i):
    px = {}
    if i <= 3:
        sink = (27, 18, 9, 3)[i]
        for (x, y), k in seam(1.0 - 0.2 * i).items():
            px[(x, y)] = k
        for (x, y), k in block().items():
            y2 = y + sink
            if y2 < H:
                px[(x, y2)] = k
        # sparks off the rising edge
        rnd = random.Random(20 + i)
        for _ in range(5 - i):
            x = rnd.randrange(2, W - 2)
            y = max(0, sink - 2 - rnd.randrange(0, 6))
            px[(x, y)] = 'g' if rnd.random() < 0.5 else 'f'
        return px
    b = block()
    if i == 4:
        return b
    if i == 5:
        # the edges flare: every keyline texel on the silhouette turns to rune light
        out = dict(b)
        for (x, y), k in b.items():
            if k == 'k' and (x in (0, W - 1) or y in (0, H - 1)):
                out[(x, y)] = 'f'
            elif k in ('e', 'f'):
                out[(x, y)] = 'g'
        return out
    if i == 6:
        # the body dissolves in a checker; the edges hold
        out = {}
        for (x, y), k in b.items():
            onedge = x in (0, W - 1) or y in (0, H - 1) or y == TOP_H
            if onedge:
                out[(x, y)] = 'e'
            elif (x + y) % 2 == 0:
                out[(x, y)] = k
        return out
    # 7: a dotted ghost of the edges
    out = {}
    for (x, y), k in b.items():
        onedge = x in (0, W - 1) or y in (0, H - 1) or y == TOP_H
        if onedge and (x + y) % 2 == 0:
            out[(x, y)] = 'd'
    return out


def strip():
    im = Image.new('RGBA', (W * 8, H), (0, 0, 0, 0))
    for i in range(8):
        im.alpha_composite(B.image(frame(i), W, H, PAL), (i * W, 0))
    return im


def preview():
    """A short L of wall blocks rippling up out of the void (0.05 s apart), holding, then going
    invisible, at 3x on the void (the plan's 96x60 px blocks)."""
    blocks = [(0, 0), (1, 0), (2, 0), (2, 1), (2, 2), (3, 2), (4, 2)]      # (col, row) on the 32x20 grid
    frames, durs = [], []
    fs = [strip().crop((i * W, 0, (i + 1) * W, H)) for i in range(8)]
    base = V.backdrop().crop((220, 180, 400, 290))
    order = sorted(range(len(blocks)), key=lambda k: -blocks[k][1])        # far rows first (painter's order)
    tick = 0.05
    total = 0.05 * len(blocks) + 0.35 + 1.0 + 0.3 + 0.4
    t = 0.0
    while t < total:
        img = base.copy()
        for k in order:
            c, r = blocks[k]
            t0 = 0.05 * k
            u = t - t0
            if u < 0:
                continue
            if u < 0.35:
                fi = min(3, int(u / 0.0875))
            elif t < 0.05 * len(blocks) + 0.35 + 1.0:
                fi = 4
            else:
                v = t - (0.05 * len(blocks) + 0.35 + 1.0)
                fi = 5 + min(2, int(v / 0.1)) if v < 0.3 else None
            if fi is None:
                continue
            x = 20 + c * 32
            y = 70 - r * 20
            img.alpha_composite(fs[fi], (x - ANCHOR[0] + 16, y - ANCHOR[1] + 20))
        frames.append(img.resize((img.width * 3, img.height * 3), Image.NEAREST))
        durs.append(int(tick * 1000))
        t += tick
    return frames, durs


def main(argv):
    if not argv or argv[0] != '--write':
        print(__doc__)
        return 2
    out = HERE
    root = os.path.realpath(os.path.join(B.ROOT, 'Assets'))
    if os.path.realpath(out).startswith(root):
        raise SystemExit('refusing to write under Assets')
    im = strip()
    png = os.path.join(out, 'void_wall_sketch.png')
    im.save(png)
    ase = os.path.join(out, 'void_wall_sketch.aseprite')
    subprocess.run([B.ASEPRITE, '-b', png, '--save-as', ase], check=True, capture_output=True)
    frames, durs = preview()
    pal = frames[len(frames) // 2].convert('RGB').quantize(colors=128, method=Image.MEDIANCUT)
    q = [f.convert('RGB').quantize(palette=pal, dither=Image.NONE) for f in frames]
    gif = os.path.join(out, 'void_wall_sketch_rise.gif')
    q[0].save(gif, save_all=True, append_images=q[1:], duration=durs, loop=0, disposal=1)
    big = Image.new('RGBA', (im.width, im.height), (8, 6, 16, 255))
    big.alpha_composite(im)
    big = big.resize((im.width * 8, im.height * 8), Image.NEAREST)
    d = ImageDraw.Draw(big)
    for i, lab in enumerate(('rise 0', 'rise 1', 'rise 2', 'rise 3', 'stand', 'flare', 'dissolve', 'ghost')):
        d.text((i * W * 8 + 4, 4), lab, fill=(230, 230, 240, 255))
    big.save(os.path.join(out, 'void_wall_sketch_8x.png'))
    print('wrote void_wall_sketch.png + .aseprite, void_wall_sketch_8x.png, void_wall_sketch_rise.gif (%d frames)'
          % len(frames))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
