"""Liam's throne palanquin, front view (3/4 top-down like the arena).
Frame 200x128.  liam_throne.png frame 0 = palanquin (dais, throne, front pole); frame 1 = rear pole only.
Z-order in the procession: shadow < frame 1 (rear pole) < rear carriers < frame 0 < Liam seated / Bixby < front carriers.
Key anchors (frame coords):
  SEAT       (64, 86)   Liam's seated sprite anchor (see liam_seated.py), throne centre x = 64
  BIXBY      (138, 104) bottom-centre of Bixby's 64x64 frame (his cushion)
  FRONT_POLE rows 120-123, REAR_POLE rows 106-109 (carriers grip rows 11-14 of their 32x32 frames)
"""
import math
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from lib import *
from pal import *
from throne_parts import *
import view

FW, FH = 200, 128
TX = 64
SEAT = (64, 86)
BIXBY = (138, 104)
FRONT_POLE = (120, 123)
REAR_POLE = (106, 109)
PLAT_X0, PLAT_X1 = 26, 166
TOP_Y0, TOP_Y1 = 94, 107
FACE_Y0, FACE_Y1 = 108, 119

# ------------------------------------------------------------------ mascot crest


def mascot(cv, cx, cy, r):
    """house mascot: white disc, blurple face with two white eyes and a toothy smile band, green online dot."""
    disc = ell(cx, cy, r, r)
    idx = shade_idx(disc, ('sphere', cx - 0.5, cy - 0.5, r + 1, r + 1, 0.35), [0.72, 0.42], cleanup=True)
    for p, i in idx.items():
        cv.put(*p, MASCOT_WHITE[i])
    cv.outline(disc)
    fw, fh = r * 1.25, r * 0.95
    fx0, fy0 = cx - fw / 2, cy - fh * 0.62
    face = poly([(fx0 + 1.5, fy0), (fx0 + fw - 1.5, fy0), (fx0 + fw, fy0 + 2), (fx0 + fw, fy0 + fh - 2),
                 (fx0 + fw - 2.5, fy0 + fh), (fx0 + 2.5, fy0 + fh), (fx0, fy0 + fh - 2), (fx0, fy0 + 2)])
    face |= ell(fx0 + 3.0, fy0 + 0.8, 3.0, 2.2) | ell(fx0 + fw - 3.0, fy0 + 0.8, 3.0, 2.2)
    face &= erode(disc, 2)
    for (x, y) in face:
        cv.put(x, y, BLURPLE[1])
    top = {(x, y) for (x, y) in face if (x, y - 1) not in face}
    for (x, y) in top:
        cv.put(x, y, BLURPLE[0])
        if (x, y + 1) in face and (x - 1, y) in face and (x + 1, y) in face and x < cx:
            cv.put(x, y + 1, BLURPLE[0])
    x0, y0, x1, y1 = bbox(face)
    band_y = y1 - max(2, round(r * 0.18))
    for (x, y) in face:
        if y >= band_y:
            cv.put(x, y, BLURPLE[2])
    for (x, y) in face:
        if y == y1 and (x in (x0 + 1, x1 - 1) or abs(x - (x0 + x1) / 2) <= 1):
            cv.put(x, y, WHITE)
    for (x, y) in face:
        if x == x1 and band_y > y > y0 + 1:
            cv.put(x, y, BLURPLE[2])
    ew = max(2, round(r * 0.17))
    eh = max(3, round(r * 0.3))
    ey = round(fy0 + fh * 0.32)
    for ex in (round(cx - fw * 0.22 - ew / 2), round(cx + fw * 0.22 - ew / 2)):
        cv.fill(rect(ex, ey, ex + ew - 1, ey + eh - 1), WHITE)
    dx, dy = cx + r * 0.66, cy + r * 0.66
    dr = max(2.2, r * 0.3)
    cv.fill(ell(dx, dy, dr + 1.6, dr + 1.6), BLACK)
    dot = ell(dx, dy, dr, dr)
    for p, i in shade_idx(dot, ('sphere', dx, dy, dr + 0.5, dr + 0.5), [0.8, 0.35]).items():
        cv.put(*p, ONLINE[i])


def crown(cv, cx, y0):
    grid = """
..k.....k.....k..
.kOk...kOk...kOk.
.kyk..kOyok..kyk.
.kyyk.kyyok.kyok.
.kyyykyyyyokyyok.
.kyOyyyGyyyyyoyk.
.kyyyyyyyyyyyyok.
.koookkBkkkookkok
.kkkkkkkkkkkkkkk.
"""
    cm = {'k': BLACK, 'O': GOLD[0], 'y': GOLD[1], 'o': GOLD[3], 'G': ONLINE[1], 'B': BLURPLE[1]}
    rows = grid.strip('\n').split('\n')
    cv.stamp(grid, cx - len(rows[0]) // 2, y0, cm)


def crest(cv, cx, cy):
    R_OUT, R_IN = 16, 12
    ring = ell(cx, cy, R_OUT, R_OUT)
    for side in (-1, 1):
        wing = poly([(cx + side * 12, cy - 9), (cx + side * 23, cy - 13), (cx + side * 21, cy - 6), (cx + side * 25, cy - 2),
                     (cx + side * 20, cy + 1), (cx + side * 22, cy + 7), (cx + side * 13, cy + 6)])
        cv.part(wing, GOLD, ('dist', 3, 0.3), TH_METAL)
        for t in (0.35, 0.65):
            gx = cx + side * (13 + 9 * t)
            for yy in range(int(cy - 8 + 4 * t), int(cy + 4 - 2 * t)):
                if cv.get(int(gx), yy) not in (None, BLACK):
                    cv.put(int(gx), yy, GOLD[3])
    cv.part(ring, GOLD, ('sphere', cx - 0.5, cy - 0.5, R_OUT + 2, R_OUT + 2, 0.2), TH_METAL)
    cv.fill(ell(cx, cy, R_IN + 1.6, R_IN + 1.6) - ell(cx, cy, R_IN + 0.6, R_IN + 0.6), GOLD[4])
    for a in range(0, 360, 45):
        sx = cx + math.cos(math.radians(a)) * (R_OUT - 2.2)
        sy = cy + math.sin(math.radians(a)) * (R_OUT - 2.2)
        cv.put(int(sx), int(sy), GOLD[0] if a in (180, 225, 270) else GOLD[2])
    mascot(cv, cx, cy, R_IN + 0.5)
    crown(cv, cx, int(cy - R_OUT - 6))

# ------------------------------------------------------------------ the throne


def throne(cv):
    cx = TX
    outer = poly([(cx - 26, 44), (cx - 24, 36), (cx - 16, 31), (cx, 29), (cx + 16, 31), (cx + 24, 36), (cx + 26, 44),
                  (cx + 26, 96), (cx - 26, 96)])
    cv.part(outer, GOLD, ('dist', 3.5, 0.25), TH_METAL)
    inner = erode(outer, 4)
    ring_in = dilate(inner, 1) - inner
    cv.fill(ring_in, GOLD[4])
    tufted_panel(cv, inner, cx, 60, 22, 32)
    cv.fill(edge(dilate(inner, 1)) & ring_in, BLACK)
    for yy in range(50, 94, 10):
        for xx in (cx - 24, cx + 24):
            cv.put(xx, yy, GOLD[0])
    cv.part(rect(cx - 27, 34, cx - 25, 42), GOLD, ('cyl', (cx - 27.5, 0), (cx - 27.5, 1), 1.8), TH_METAL)
    cv.part(rect(cx + 25, 34, cx + 27, 42), GOLD, ('cyl', (cx + 24.5, 0), (cx + 24.5, 1), 1.8), TH_METAL)
    gold_ball(cv, cx - 25.5, 32, 3.4)
    gold_ball(cv, cx + 26.5, 32, 3.4)
    crest(cv, cx, 22)
    for side in (-1, 1):
        ax = cx + side * 31
        post = rect(ax - 4, 72, ax + 4, 101)
        cv.part(post, GOLD, ('cyl', (ax - 4.5, 0), (ax - 4.5, 1), 4.8, 0.15), TH_METAL)
        for yy in (82, 90, 97):
            for xx in range(ax - 3, ax + 4):
                if cv.get(xx, yy) not in (None, BLACK):
                    cv.put(xx, yy, GOLD[3])
        pad = capsule((ax - 5, 68), (ax + 5, 68), 4.2)
        cv.part(pad, VELVET, ('sphere', ax - 1.5, 66, 8, 5.5, 0.3), [9.0, 0.86, 0.6, 0.3, 0.1])
        vol = ell(ax, 76, 4.6, 4.6)
        cv.part(vol, GOLD, ('sphere', ax - 1, 75, 5.5, 5.5), TH_METAL)
        for (px, py) in ((ax, 76), (ax + 1, 76), (ax + 1, 77), (ax, 77), (ax - 1, 77), (ax - 1, 76), (ax - 1, 75), (ax, 74), (ax + 1, 74), (ax + 2, 75)):
            cv.put(px, py, GOLD[4])
        cv.put(ax, 76, GOLD[0])
    cush = poly([(cx - 22, 84), (cx + 22, 84), (cx + 24, 88), (cx + 23, 95), (cx - 23, 95), (cx - 24, 88)])
    cv.part(cush, VELVET, ('sphere', cx - 6, 86, 30, 8, 0.4), [9.0, 0.86, 0.62, 0.34, 0.1])
    for xx in range(cx - 22, cx + 23):
        if cv.get(xx, 94) not in (None, BLACK):
            cv.put(xx, 94, GOLD[2] if xx % 3 else GOLD[1])
    apron = poly([(cx - 26, 96), (cx + 26, 96), (cx + 25, 102), (cx + 8, 104), (cx, 106), (cx - 8, 104), (cx - 25, 102)])
    cv.part(apron, GOLD, ('dist', 3, 0.3), TH_METAL)
    gem = ell(cx, 100.5, 3, 2.6)
    cv.part(gem, BLURPLE, ('sphere', cx - 1, 99.5, 3.5, 3.5), [0.85, 0.5, 0.2])
    cv.put(cx - 1, 99, WHITE)
    for xx in (cx - 18, cx - 12, cx + 12, cx + 18):
        cv.put(xx, 99, GOLD[3])
        cv.put(xx + 1, 100, GOLD[3])
    for fx in (cx - 22, cx + 22):
        foot = ell(fx, 105, 4.5, 3)
        cv.part(foot, GOLD, ('sphere', fx - 1, 104, 5, 4), TH_METAL)
        for t in (-2, 0, 2):
            cv.put(fx + t, 107, BLACK)


def dais(cv):
    x0, x1 = PLAT_X0, PLAT_X1
    top = rect(x0, TOP_Y0, x1, TOP_Y1)
    for (x, y) in top:
        t = (x - x0) / (x1 - x0)
        cv.put(x, y, VELVET[2] if t < 0.55 else VELVET[3])
    for x in range(x0, x1 + 1):
        cv.put(x, TOP_Y0 + 1, VELVET[1] if x < (x0 + x1) // 2 else VELVET[2])
    border = rect(x0 + 3, TOP_Y0 + 3, x1 - 3, TOP_Y1 - 1) - rect(x0 + 4, TOP_Y0 + 4, x1 - 4, TOP_Y1 - 2)
    cv.fill(border, GOLD[2])
    cv.outline(top)
    face = rect(x0, FACE_Y0 + 3, x1, FACE_Y1)
    cv.part(face, WOOD, ('flat', -0.1, 0.2), [9.0, 0.95, 0.75, 0.4])
    for x in range(x0, x1 + 1):
        cv.put(x, FACE_Y1 - 1, WOOD[3])
    cv.outline(rect(x0 - 1, FACE_Y0 - 1, x1 + 1, FACE_Y1))
    period = 16
    for x in range(x0 + 1, x1):
        ph = ((x - x0) % period) / period
        depth = int(round(3 + 3.2 * math.sin(math.pi * ph)))
        for y in range(FACE_Y0 + 3, FACE_Y0 + 3 + depth):
            shade = VELVET[2] if ph < 0.45 else VELVET[3]
            if y == FACE_Y0 + 3:
                shade = VELVET[1] if ph < 0.6 else VELVET[2]
            cv.put(x, y, shade)
        cv.put(x, FACE_Y0 + 3 + depth, BLACK)
    gold_bar_h(cv, x0 - 1, x1 + 1, FACE_Y0 - 1, FACE_Y0 + 2)
    for x in range(x0 + period, x1, period):
        tassel(cv, x, FACE_Y0 + 3)
    for bx in (x0 + 1, x1 - 4):
        cv.fill(rect(bx, FACE_Y1 - 4, bx + 3, FACE_Y1 - 1), GOLD[2])
        cv.put(bx + 1, FACE_Y1 - 3, GOLD[0])
    label = '@LIAM'
    tw = text_w(label)
    px0 = TX - tw // 2 - 4
    px1 = px0 + tw + 7
    plate = rect(px0, FACE_Y0 + 3, px1, FACE_Y0 + 11) - {(px0, FACE_Y0 + 3), (px1, FACE_Y0 + 3), (px0, FACE_Y0 + 11), (px1, FACE_Y0 + 11)}
    cv.part(plate, GOLD, ('flat', -0.3, -0.4), [9.0, 0.9, 0.5])
    plate_text(cv, label, px0 + 4, FACE_Y0 + 6, BLURPLE[3])


def bixby_cushion(cv):
    cx, cy = BIXBY[0], 100
    cush = ell(cx, cy, 27, 6.5)
    cv.part(cush, VELVET, ('sphere', cx - 8, cy - 4, 34, 10, 0.2), [9.0, 0.88, 0.62, 0.34, 0.1])
    for (x, y) in edge(erode(cush, 1)):
        if y > cy:
            cv.put(x, y, GOLD[2] if x % 2 else GOLD[1])
    for tx in (cx - 26, cx + 26):
        tassel(cv, tx, cy - 1)


def streamers(cv):
    """wide role-colour ribbons tied to the top finials, fluttering outward with a curl"""
    def flat_ribbon(pts, rp, w=2.0):
        m = tube(pts, (w, w * 0.8))
        idx = {}
        path = catmull(pts, 8)
        for (x, y) in m:
            k = min(range(len(path)), key=lambda i: (path[i][0] - x) ** 2 + (path[i][1] - y) ** 2)
            idx[(x, y)] = 0 if (k // 10) % 2 == 0 else 1
        for p, i in idx.items():
            cv.put(*p, rp[i])
        cv.outline(m)
    flat_ribbon([(TX - 26, 33), (TX - 36, 38), (TX - 40, 48), (TX - 46, 55), (TX - 44, 64)], ROLE_PINK)
    flat_ribbon([(TX + 27, 33), (TX + 37, 38), (TX + 41, 48), (TX + 47, 55), (TX + 45, 64)], ROLE_CYAN)


def build():
    f0 = Canvas(FW, FH)
    pennant(f0, PLAT_X0 + 2, 66, TOP_Y0 + 2, -1)
    pennant(f0, PLAT_X1 - 2, 50, TOP_Y0 + 2, 1)
    dais(f0)
    bixby_cushion(f0)
    streamers(f0)
    throne(f0)
    pole(f0, FRONT_POLE[0], 22, 164)
    f1 = Canvas(FW, FH)
    pole(f1, REAR_POLE[0], 14, 190)
    return f0, f1


if __name__ == '__main__':
    f0, f1 = build()
    both = Canvas(FW, FH)
    both.blit(f1)
    both.blit(f0)
    print(view.zoom(both, 5, 'throne_5x.png'))
