"""Render the v2 bear hug: 15x256x192 strip, planted-sword layer, previews, gifs, checks."""
import os
from collections import Counter
import frames2
import bh2 as B
import pv2
from pngio import write_png, blank, paste, scale, crop, read_png
from gifio import write_gif

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(ROOT, 'out')
VIEWS = os.path.join(ROOT, 'views')
os.makedirs(OUT, exist_ok=True)
os.makedirs(VIEWS, exist_ok=True)
FW, FH = B.FW, B.FH
N = len(frames2.ORDER)
FL = pv2.FL

imgs, boxes = [], {}
for i, name in enumerate(frames2.ORDER):
    fr = frames2.F[name]()
    B.seal(fr)
    imgs.append(fr.rgba())
    if getattr(fr, 'box', None):
        boxes[name] = fr.box

strip = blank(FW * N, FH, (0, 0, 0, 0))
for i, im in enumerate(imgs):
    paste(strip, im, FW * i, 0)
write_png(os.path.join(OUT, 'eric_bearhug_v2.png'), FW * N, FH, strip)

sw = B.R.Frame()
B.planted_sword(sw)
sword_px = sw.rgba()
write_png(os.path.join(OUT, 'eric_bearhug_planted_sword_v2.png'), FW, FH, sword_px)

# ------------------------------------------------------------------ previews
pv2.strip(imgs, 3, os.path.join(VIEWS, 'strip_3x_all_v2.png'))
pv2.strip(imgs[:8], 2, os.path.join(VIEWS, 'strip_2x_a_v2.png'))
pv2.strip(imgs[8:], 2, os.path.join(VIEWS, 'strip_2x_b_v2.png'))
for name in ('grab', 'squeeze0'):
    pv2.zoom(imgs[frames2.ORDER.index(name)], 8, os.path.join(VIEWS, 'view8x_%s_v2.png' % name))

# ------------------------------------------------------------------ gifs (2x; the planted sword stays in the world during 3-12)
IDX = {n: i for i, n in enumerate(frames2.ORDER)}
WORLD_SWORD = {'lunge0', 'lunge1', 'whiff0', 'whiff1', 'grab', 'squeeze0', 'squeeze1', 'squeeze2', 'toss0', 'toss1'}


def gif_frame(name, s=2):
    im = imgs[IDX[name]]
    if name in WORLD_SWORD:
        base = [row[:] for row in sword_px]
        paste(base, im, 0, 0)
        im = base
    return scale(pv2.on_bg(im), s)


def make_gif(path, seq):
    fs = [gif_frame(n) for n, _ in seq]
    write_gif(path, [[[p[:3] for p in row] for row in f] for f in fs], [max(2, int(round(d * 100))) for _, d in seq])


charge = [('charge0', 0.16)] + [('charge1', 0.08), ('charge2', 0.08)] * 4
lunge = [('lunge0', 0.07), ('lunge1', 0.10)]
retrieve = [('retrieve0', 0.30), ('retrieve1', 0.40)]
land = charge + lunge + [('grab', 0.28)] + [('squeeze0', 0.10), ('squeeze1', 0.20), ('squeeze2', 0.12)] * 3 + \
    [('toss0', 0.20), ('toss1', 0.50)] + retrieve
whiff = charge + lunge + [('whiff0', 0.14), ('whiff1', 0.90)] + retrieve
make_gif(os.path.join(ROOT, 'gif_bearhug_v2_land.gif'), land)
make_gif(os.path.join(ROOT, 'gif_bearhug_v2_whiff.gif'), whiff)

# ------------------------------------------------------------------ checks
print('alpha values:', dict(Counter(p[3] for row in strip for p in row)))
print('colours:', len(set(p[:3] for row in strip for p in row if p[3])))
from lib import PALC
FX_OK = set(PALC[c] for c in 'WABCZgGhdfjmno') | {PALC['k']}
names = {v: k for k, v in PALC.items()}
for i, name in enumerate(frames2.ORDER):
    im = imgs[i]
    edge = sum(1 for y in range(FH) for x in (0, FW - 1) if im[y][x][3]) + sum(1 for x in range(FW) if im[0][x][3])
    xs = [x for y in range(FH) for x in range(FW) if im[y][x][3]]
    ys = [y for y in range(FH) for x in range(FW) if im[y][x][3]]
    gaps = iso = 0
    for y in range(FH):
        for x in range(FW):
            p = im[y][x]
            if not p[3]:
                continue
            if p not in FX_OK and any(0 <= xx < FW and 0 <= yy < FH and not im[yy][xx][3]
                                      for xx, yy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))):
                gaps += 1
            if not any(0 <= x + dx < FW and 0 <= y + dy < FH and im[y + dy][x + dx][3]
                       for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy):
                iso += 1
    print('%2d %-10s bbox=(%d,%d)-(%d,%d) edge px(left/right/top)=%d gaps=%d isolated=%d box=%s' % (
        i, name, min(xs), min(ys), max(xs), max(ys), edge, gaps, iso, boxes.get(name)))
_, _, base = read_png('C:/Users/theyi/OneDrive/Documents/new-game-project/Assets/Characters/Eric/eric_redesign_v2.png')
d = [(x, y) for y in range(FH) for x in range(FW) if imgs[14][y][x] != (base[y][x] if base[y][x][3] else (0, 0, 0, 0))]
print('retrieve1 vs eric_redesign_v2.png: %d px differ, bbox %s' % (
    len(d), (min(x for x, _ in d), min(y for _, y in d), max(x for x, _ in d), max(y for _, y in d)) if d else None))
print('timings land %.2f whiff %.2f' % (sum(t for _, t in land), sum(t for _, t in whiff)))
