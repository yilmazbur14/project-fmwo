"""nugget_target.png - ground telegraph, 4 frames of 48x26, marker centre at (24, 13).
The ring's outer size is constant (44x22 texels) so the danger zone never changes size;
the shadow grows as the nugget approaches, the ring heats up, and a crosshair of
breadcrumbs closes in on the centre."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from fxlib import *

FW, FH = 48, 26
CX, CY = 24.0, 13.0
RX, RY = 22.0, 11.0          # outer edge of the black outline
NM_WARM = hx('#C27C3E')


def in_ell(x, y, rx, ry, cx=CX, cy=CY):
    return ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0


def ellipse_mask(rx, ry):
    """symmetric about both axes (mirror the top-left quadrant)"""
    m = set()
    for y in range(FH):
        for x in range(FW):
            xx = x if x + 0.5 <= CX else int(2 * CX - 1 - x)
            yy = y if y + 0.5 <= CY else int(2 * CY - 1 - y)
            if in_ell(xx, yy, rx, ry):
                m.add((x, y))
    return m


# ring palette per frame: (top arc, sides, bottom arc)
RING = [
    (F_ORG, F_ORG, F_RED),
    (F_YEL, F_ORG, F_RED),
    (WHITE, F_YEL, F_ORG),
    (WHITE, F_YEL, F_ORG),
]
SHADOW = [(9.5, 4.6), (13.0, 6.4), (16.0, 8.0), (18.5, 9.2)]
CRUMB_R = [0.86, 0.76, 0.66, 0.58]     # crosshair crumbs close in on the centre

# irregular breadcrumb bits: h highlight, b base, m warm shade, d drop-shadow pixel
CRUMBS = {
    'L': [".hb.", "hbbm", ".bmd", "..d."],     # large
    'M': ["hb.", "bmd", ".d."],                # medium
    'S': ["b.", "d."],                         # small
}


def crumb(g, x, y, key, flip=False):
    spr = CRUMBS[key]
    for j, row in enumerate(spr):
        if flip:
            row = row[::-1]
        for i, ch in enumerate(row):
            if ch == '.':
                continue
            c = {'h': N_HI, 'b': N_BASE, 'm': NM_WARM, 'd': N_DARK}[ch]
            if flip and ch == 'h':
                c = N_BASE
            put(g, x + i, y + j, c)


def target_frame(f):
    g = canvas(FW, FH)
    outer = ellipse_mask(RX - 1.0, RY - 1.0)        # rim + interior (outline added outside)
    rim_in = ellipse_mask(RX - 3.6, RY - 2.2)       # inside of the rim band
    top, side, bot = RING[f]
    for (x, y) in outer - rim_in:
        yy = y + 0.5 - CY
        c = top if yy < -RY * 0.45 else (bot if yy > RY * 0.50 else side)
        put(g, x, y, c)
    # shadow grows toward the rim as the nugget falls
    srx, sry = SHADOW[f]
    for (x, y) in rim_in:                        # the whole danger zone is tinted from frame 0
        put(g, x, y, SH_1)
    s_outer = ellipse_mask(srx, sry) & rim_in
    s_core = ellipse_mask(srx * 0.55, sry * 0.60)
    for (x, y) in s_outer:
        put(g, x, y, SH_3 if (x, y) in s_core and f >= 2 else SH_2)
    if f == 3:
        # flash: a second, inner hot line just inside the rim
        inner_line = ellipse_mask(RX - 3.6, RY - 2.2) - ellipse_mask(RX - 5.0, RY - 3.0)
        for (x, y) in inner_line:
            yy = y + 0.5 - CY
            put(g, x, y, F_ORG if yy > RY * 0.2 else F_YEL)
    for p in outline_of(outer):
        put(g, p[0], p[1], K)
    # crumb crosshair ticks, closing in on the centre
    k = CRUMB_R[f]
    irx, iry = RX - 3.6, RY - 2.2
    for sgn in (-1, 1):
        flip = sgn > 0
        for dist, key in ((k, 'L'), (k - 0.20, 'M'), (k - 0.36, 'S')):
            w = len(CRUMBS[key][0])
            xc = CX + sgn * irx * dist
            crumb(g, int(round(xc - w / 2.0)), int(CY) - 1, key, flip)
        for dist, key in ((k, 'M'), (k - 0.30, 'S')):
            yc = CY + sgn * iry * dist
            crumb(g, int(CX) - 1, int(round(yc - 1.0)), key, flip)
    crumb(g, int(CX) - 2, int(CY) - 2, 'L')
    return g


def symmetric_report(g, name):
    bad = 0
    for y in range(FH):
        for x in range(FW):
            if (g[y][x][3] > 0) != (g[y][FW - 1 - x][3] > 0):
                bad += 1
    print(name, 'silhouette mirror mismatches:', bad)


if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'nugget_target_wip.png'
    frames = [target_frame(f) for f in range(4)]
    for i, fr in enumerate(frames):
        symmetric_report(fr, 'target%d' % i)
    sheet = strip(frames)
    check_alpha(sheet, 'target')
    edge_touch(sheet, FW, FH, 'target')
    save(out, sheet)
    ys = [y for y in range(FH) for x in range(FW) if frames[0][y][x][3]]
    xs = [x for y in range(FH) for x in range(FW) if frames[0][y][x][3]]
    print('wrote', out, 'bbox x %d-%d y %d-%d' % (min(xs), max(xs), min(ys), max(ys)),
          'outer size %dx%d' % (max(xs) - min(xs) + 1, max(ys) - min(ys) + 1))
