"""Jordan's main-menu tower silhouette: the raw derivation his masks_clean.txt entry is hand-cleaned from
(the way art_source/main_menu/masks_josh.py did Josh's today).

The source is the approved 2026-09-23 redesign, Assets/Characters/Jordan/jordan_redesign.png frame 0
(96x96, feet on row 95, body centred on x48), sampled the way masks2.py / masks3.py did it: 4x4
supersamples per tower pixel, a pixel is solid at 34% coverage, bottom-anchored so the ground line
(his feet on tier 10, y47) is exact.

THE SCALE. His previous entry's scale, recovered by fitting rather than guessed (fit_old()): the
old jordan.png sampled at 1.0-2.6 and scored against the old cleaned [jordan] mask; 1.6 won (IoU
0.873; the next best, 1.5, scored 0.791). But the redesign is 87px from quiff to sole where the old
sprite was 61, and at 1.6 it comes out 54 rows tall: standing on tier 10 (feet on y47, the top of
the frame at y0) its top 6 rows - the whole quiff - would be off the screen. So the factor is the
one closest to 1.6 that keeps him whole with the same clear sky over his head the tiers below give
their members: FACTOR below, chosen and justified in menu.py.

    python menu_mask.py            # prints the fit and the raw mask
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dkit                                                      # noqa: E402
from PIL import Image                                            # noqa: E402

OLD_SPRITE = os.path.join(dkit.ASSETS, 'Characters', 'Jordan', 'jordan.png')
MASKS = os.path.join(dkit.ART, 'main_menu', 'masks_clean.txt')
FRAME_W = 96
THRESHOLD = 0.34
SS = 4
ANCHOR_X = 48          # the sprite's anchor column (jordan.py: the body centres on x48)


def load_masks(path=MASKS):
    """bg.load_masks, without importing bg (whose `from lib import *` would clash with the rig's lib)."""
    ms, cur = {}, None
    for line in open(path):
        line = line.rstrip()
        if line.startswith('['):
            cur = line[1:-1]
            ms[cur] = []
        elif line.strip() and cur:
            ms[cur].append(line)
    return ms


def alpha_of(im, frame=0, fw=None):
    fw = fw or im.width
    return [[im.getpixel((frame * fw + x, y))[3] for x in range(fw)] for y in range(im.height)]


def raw_mask(alpha, factor):
    """masks_josh.raw_mask on an alpha grid: returns (rows, x0) - x0 is the sprite column the mask's
    column 0 starts at, so a sprite column maps to mask column floor((x - x0) / factor)."""
    h, fw = len(alpha), len(alpha[0])
    xs = [x for y in range(h) for x in range(fw) if alpha[y][x]]
    ys = [y for y in range(h) for x in range(fw) if alpha[y][x]]
    x0, y0, x1, y1 = min(xs), min(ys), max(xs) + 1, max(ys) + 1
    tw, th = int(round((x1 - x0) / factor)), int(round((y1 - y0) / factor))
    rows = []
    for ty in range(th):
        r = ''
        for tx in range(tw):
            hit = 0
            for sy in range(SS):
                for sx in range(SS):
                    X = int(x0 + (tx + (sx + 0.5) / SS) * factor)
                    Y = int(y1 - (th - ty) * factor + ((sy + 0.5) / SS) * factor)
                    if 0 <= X < fw and 0 <= Y < h and alpha[Y][X]:
                        hit += 1
            r += '#' if hit / (SS * SS) >= THRESHOLD else '.'
        rows.append(r)
    return rows, x0


def iou(a, b, span=12):
    """Best IoU over horizontal offsets, both masks standing on their last row."""
    ha, hb = len(a), len(b)
    A = {(x, y - ha) for y in range(ha) for x in range(len(a[0])) if a[y][x] != '.'}
    best = (0.0, 0)
    for dx in range(-span, span + 1):
        B = {(x + dx, y - hb) for y in range(hb) for x in range(len(b[0])) if b[y][x] != '.'}
        u = len(A | B)
        s = len(A & B) / u if u else 0.0
        if s > best[0]:
            best = (s, dx)
    return best


def fit_old():
    """The old jordan.png against the old cleaned mask, at 1.0..2.6: [(iou, factor, w, h)]."""
    old = Image.open(OLD_SPRITE).convert('RGBA')
    alpha = alpha_of(old)
    target = load_masks(os.path.join(dkit.PREVIEWS, 'before', 'masks_clean_old.txt')
                        if os.path.exists(os.path.join(dkit.PREVIEWS, 'before', 'masks_clean_old.txt'))
                        else MASKS)['jordan']
    out = []
    for f10 in range(10, 27):
        m, _ = raw_mask(alpha, f10 / 10.0)
        out.append((iou(m, target)[0], f10 / 10.0, len(m[0]), len(m)))
    return sorted(out, reverse=True)


SPRITE_V2 = os.path.join(dkit.ASSETS, 'Characters', 'Jordan', 'jordan_redesign_v2.png')


def new_mask(factor, sprite=None):
    """(rows, anchor column) for frame 0 of `sprite` (default: the first redesign). The v2 derivation
    passes SPRITE_V2 (the approved 2026-09-24 v2, whose body also centres on x48)."""
    im = Image.open(sprite or dkit.SPRITE).convert('RGBA')
    rows, x0 = raw_mask(alpha_of(im, 0, FRAME_W), factor)
    return rows, int((ANCHOR_X - x0) // factor)


if __name__ == '__main__':
    for s, f, w, h in fit_old()[:4]:
        print('old fit: factor %.1f -> %dx%d  IoU %.3f' % (f, w, h, s))
    for f in (1.6, 1.8, 1.9, 2.0, 2.1):
        m, a = new_mask(f)
        print('new frame 0 at %.2f: %dx%d, anchor column %d, top row on tier 10: y%d'
              % (f, len(m[0]), len(m), a, 47 - len(m) + 1))
    f = float(sys.argv[1]) if len(sys.argv) > 1 else 2.0
    m, a = new_mask(f)
    print('\nraw at %.2f (%dx%d, anchor %d):' % (f, len(m[0]), len(m), a))
    print('\n'.join(m))
