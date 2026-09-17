"""Heads for beast Bixby: volumes + outlines, then hand stamps (faces.py), horns, headband, scorched ears.
Middle head local coords: col = (ox - 30) + lx, row = oy + ly, symmetric lx <-> 59 - lx (ox = continuous axis).
Side head local box 42x40 authored facing left: col = ox + lx (side +1) or ox + 41 - lx (side -1)."""
import math, random
import lib
from lib import *
from pal import PALC, RAMPC, BLACK
import faces


# ================================================================== middle head
def mid_pts(pts, ox, oy):
    b = ox - 30
    return [(b + x, oy + y) for x, y in pts]


def mid_sym_poly(half, ox, oy):
    """half: local pts on the left half, from the axis (x=30) at top to the axis at bottom"""
    full = half + [(60 - x, y) for x, y in reversed(half[1:-1])]
    return poly(mid_pts(full, ox, oy))


def middle_head_base(cv, ox, oy, jaw_drop=0):
    b = ox - 30
    skull = ell(ox, oy + 18, 19.5, 17)
    jowl = ell(ox, oy + 31, 18.5, 10.5)
    head = skull | jowl
    jd = jaw_drop
    jaw = mid_sym_poly([(30, 40), (19, 40), (19.5, 47 + jd), (23, 52.5 + jd), (30, 54 + jd)], ox, oy)
    cv.part(jaw, 'fur', ('sphere', ox - 3, oy + 43, 13, 12), TH_B)
    cv.part(head, 'tan', ('sphere', ox - 4, oy + 15, 24, 26, 0.1), TH_B)
    muz = ell(ox, oy + 34, 12.5, 8.5)
    cv.part(muz, 'fur', ('sphere', ox - 3, oy + 31, 14, 11), TH_B, outline=False)
    blaze = mid_sym_poly([(30, 1.5), (28, 1.5), (27.5, 12), (26.5, 20), (23, 27), (21, 30), (30, 30)], ox, oy)
    cv.recolor((blaze | muz) & erode(head, 1), 'fur', ('sphere', ox - 3, oy + 18, 14, 26, 0.2), TH_B)
    earL = poly(mid_pts([(15, 9), (9, 11), (4, 19), (1, 31), (0, 44), (2, 53), (7, 57), (11.5, 54), (13, 44), (12.5, 30), (14.5, 19)], ox, oy))
    earR = mirror(earL, int(round(2 * ox - 1)))
    cv.part(earL, 'ear', ('sphere', b + 4, oy + 26, 10, 32, 0.25), TH_B)
    cv.part(earR, 'ear', ('sphere', b + 52, oy + 26, 12, 32, 0.25), TH_B, bias=1)
    return dict(head=head, jaw=jaw, earL=earL, earR=earR)


def scorch(cv, mask, from_row, seed=1, embers=True, depth=5):
    """burnt-paper ear tip: charred ragged tip, glowing irregular burn line above it"""
    cols = {}
    for (x, y) in mask:
        cols.setdefault(x, []).append(y)
    bottom_of = {x: max(ys) for x, ys in cols.items()}
    # ragged silhouette: notch the bottom edge
    for x, yb in bottom_of.items():
        h = ((x * 7 + seed * 13) % 5)
        cut = 1 if h in (1, 3) else (2 if h == 2 else 0)
        for k in range(cut):
            cv.put(x, yb - k, None)
        bottom_of[x] = yb - cut
    cur = {q for q in mask if cv.get(*q) is not None}
    # re-outline bottom
    for q in edge(cur):
        cv.put(q[0], q[1], BLACK)
    inner = erode(cur, 1)
    for (x, y) in inner:
        yb = bottom_of.get(x, y)
        wob = ((x * 5 + seed * 3) % 3) - 1           # -1..1
        line = yb - depth + wob
        if y > line:
            cv.put(x, y, PALC['e'] if (x + y) % 4 else PALC['d'])
        elif y == line:
            cv.put(x, y, PALC['o'] if (x + seed) % 3 else PALC['O'])
        elif y == line - 1 and (x + seed) % 2 == 0:
            cv.put(x, y, PALC['F'])


def middle_headband(cv, ox, oy, head_mask):
    band = mid_sym_poly([(30, 9.5), (22, 10), (14, 11), (14, 15.5), (22, 14.5), (30, 14)], ox, oy) & head_mask
    cv.part(band, 'tails', ('cyl', (ox - 20, oy + 12), (ox + 20, oy + 12), 3.2), TH_B4, bias=0)
    cv.outline(band)
    plate = poly(mid_pts([(21, 8), (39, 8), (40, 9), (40, 16), (39, 17), (21, 17), (20, 16), (20, 9)], ox, oy))
    cv.part(plate, 'band', ('sphere', ox - 6, oy + 9, 22, 10, 0.3), TH_B4)
    # plate details: top highlight line + rivets + bottom shade (Liam's plate is plain)
    b = ox - 30
    for lx in range(23, 37):
        cv.put(b + lx, oy + 9, PALC['h'])
    for lx, ly in ((22, 10), (38, 10), (22, 15), (38, 15)):
        cv.put(b + lx, oy + ly, PALC['l'])
    for lx in range(22, 39):
        if cv.get(b + lx, oy + 16) != BLACK:
            cv.put(b + lx, oy + 16, PALC['j'])
    return band | plate


def ribbon(cv, path, width, seed=0):
    """flat cloth ribbon along a smoothed path; light/dark bands suggest twisting; notched end"""
    sp = catmull(path, 10)
    L = len(sp)
    m = set()
    shade = {}
    for i in range(L - 1):
        (x0, y0), (x1, y1) = sp[i], sp[i + 1]
        dx, dy = x1 - x0, y1 - y0
        n = math.hypot(dx, dy) or 1
        nx, ny = -dy / n, dx / n
        w = width * (1.0 - 0.25 * i / L)
        for k in range(-6, 7):
            t = k / 6 * w
            q = (int(math.floor(x0 + nx * t)), int(math.floor(y0 + ny * t)))
            m.add(q)
            shade[q] = 0 if k <= -3 else (1 if k <= 3 else 2)
    # notch the end
    ex, ey = sp[-1]
    (px, py) = sp[-3]
    for q in list(m):
        if math.hypot(q[0] + 0.5 - ex, q[1] + 0.5 - ey) < width * 0.9 and ((q[0] + 0.5 - px) * (ex - px) + (q[1] + 0.5 - py) * (ey - py)) > 0:
            d = abs((q[0] + 0.5 - ex) * (ey - py) - (q[1] + 0.5 - ey) * (ex - px)) / (math.hypot(ex - px, ey - py) or 1)
            if d < 0.7:
                m.discard(q)
    rp = RAMPC['tails']
    for q in m:
        cv.put(q[0], q[1], rp[shade.get(q, 1)])
    cv.outline(m)
    return m


def cloth_tail(cv, pts, r0, r1):
    """solid ribbon tail: clean tube, lit upper edge, shaded lower edge, V-notched end"""
    m = tube(pts, [r0 + (r1 - r0) * i / (len(pts) - 1) for i in range(len(pts))])
    sp = catmull(pts, 10)
    ex, ey = sp[-1]
    px_, py_ = sp[-4]
    dx, dy = ex - px_, ey - py_
    n = math.hypot(dx, dy) or 1
    dx, dy = dx / n, dy / n
    # V notch: remove pixels near the end that lie close to the centre line
    for q in list(m):
        qx, qy = q[0] + 0.5 - ex, q[1] + 0.5 - ey
        along = qx * dx + qy * dy
        across = abs(-qx * dy + qy * dx)
        if along > -2.2 and across < 1.0 + (along + 2.2) * 0.45:
            m.discard(q)
    rp = RAMPC['tails']
    for (x, y) in m:
        # distance to the smoothed path, signed by side (upper side lighter)
        best = None
        for i in range(0, len(sp) - 1, 2):
            (ax, ay), (bx, by) = sp[i], sp[min(i + 2, len(sp) - 1)]
            vx, vy = bx - ax, by - ay
            L2 = vx * vx + vy * vy or 1
            t = max(0, min(1, ((x + 0.5 - ax) * vx + (y + 0.5 - ay) * vy) / L2))
            cx, cy = ax + vx * t, ay + vy * t
            d2 = (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2
            if best is None or d2 < best[0]:
                best = (d2, cx, cy, vx, vy)
        _, cx, cy, vx, vy = best
        side = (x + 0.5 - cx) * (-vy) + (y + 0.5 - cy) * vx      # >0 : below the path
        cv.put(x, y, rp[0] if side < -0.6 else (rp[1] if side < 0.9 else rp[2]))
    cv.outline(m)
    return m


def headband_tails(cv, ox, oy, P):
    b = ox - 30
    knot = (b + 45.5, oy + 13)
    paths = P.get('tails', [
        [(0, -1), (8, -6), (18, -11), (29, -12), (40, -18), (50, -18)],
        [(0, 1.5), (9, -1), (19, -6), (30, -5), (41, -10), (51, -8)],
    ])
    masks = []
    for k, path in enumerate(paths):
        pts = [(knot[0] + x, knot[1] + y) for x, y in path]
        masks.append(cloth_tail(cv, pts, 2.3, 1.7))
    return masks


GLASSES = """
kk.................
.kk................
..kkkkkkkk.kkkkkkkk
..kWWWWCWkkkWWWWWCk
..kWWWWjWk.kWWWWWWk
..kWWWjWWk.kWWWWWWk
..kWWjWWCk.kCWWWWWk
..kkkkkkkk.kkkkkkkk
"""


def glasses_on_horn(cv, x0, y0, flip=False):
    """Liam's glasses, one lens cracked, hanging by a temple arm from a horn tip"""
    rows = GLASSES.strip(chr(10)).split(chr(10))
    wdt = len(rows[0])
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch != '.':
                cv.put(x0 + (wdt - 1 - dx if flip else dx), y0 + dy, PALC[ch])


def middle_horns(cv, ox, oy, P=None):
    path = [(19, 9), (13, 3), (9.5, -5), (9.5, -12), (13, -17.5)]
    radii = [4.6, 4.1, 3.2, 2.0, 0.6]
    hl = tube(mid_pts(path, ox, oy), radii)
    hr = mirror(hl, int(round(2 * ox - 1)))
    for h in (hl, hr):
        cv.part(h, 'dark', ('dist', 3.4), TH_GLOSS)
    # ridge rings (obsidian segments) along each horn
    for h, sgn in ((hl, 1), (hr, -1)):
        for (lx, ly) in ((12, 1), (10, -4), (10, -9)):
            x = ox - 30 + lx if sgn > 0 else ox + 29 - lx
            for dx in range(-3, 4):
                q = (int(x + dx), int(oy + ly + (dx * 0.35 if sgn > 0 else -dx * 0.35)))
                if q in erode(h, 1):
                    cv.put(q[0], q[1], PALC['Z'])
    return hl, hr


def middle_head(cv, ox, oy, P=None):
    P = P or {}
    jd = P.get('mh_jaw', 0)
    base = middle_head_base(cv, ox, oy, jd)
    faces.middle_face(cv, ox, oy, jd)
    scorch(cv, base['earL'], oy + 47, seed=3)
    scorch(cv, base['earR'], oy + 47, seed=5)
    middle_headband(cv, ox, oy, base['head'])
    return base


# ================================================================== side heads
def side_pts(pts, ox, oy, side):
    if side > 0:
        return [(ox + x, oy + y) for x, y in pts]
    return [(ox + 42 - x, oy + y) for x, y in pts]


def side_head_base(cv, ox, oy, side, jaw_drop=0):
    T = lambda pts: side_pts(pts, ox, oy, side)
    cx = lambda lx: T([(lx, 0)])[0][0]
    ear = poly(T([(29.5, 8), (36.5, 9), (41.5, 17), (43.5, 29), (43, 41), (39.5, 48), (33.5, 47), (30.5, 38), (29, 22)]))
    cv.part(ear, 'ear', ('sphere', cx(35) - 3, oy + 22, 11, 30, 0.25), TH_B, bias=(0 if side > 0 else 1))
    skull = poly(T([(17, 5), (24, 3), (31, 5), (36, 10), (38, 17), (37, 25), (34, 31), (28, 34), (21, 33), (15, 28), (9, 23), (8, 16), (11, 9)]))
    cv.part(skull, 'tan', ('sphere', cx(21), oy + 13, 20, 20, 0.12), TH_B)
    jd = jaw_drop
    jaw = poly(T([(5, 31), (15, 32.5), (24, 29.5), (28, 28.5), (29, 33 + jd), (25, 37 + jd), (15, 39 + jd), (7, 37 + jd)]))
    cv.part(jaw, 'fur', ('sphere', cx(14), oy + 31, 14, 9), TH_B)
    muz = poly(T([(22, 16), (15, 16.5), (8, 16.5), (3, 18), (0.5, 21), (1.5, 25), (5, 27.5), (14, 27.5), (22, 26), (26, 21.5)]))
    cv.part(muz, 'fur', ('sphere', cx(10), oy + 18, 16, 11), TH_B)
    mouth = poly(T([(3.5, 26.5), (14, 27), (23, 25.5), (27, 27.5), (25, 30.5), (15, 33.5), (6, 32.5), (3.5, 29.5)]))
    cv.paint(mouth, PALC['M'])
    cv.outline(mouth)
    blaze = poly(T([(22, 3.5), (26, 3.5), (25, 10), (24, 14.5), (22.5, 17.5), (18, 17.5), (21, 12)]))
    cv.recolor(blaze & erode(skull, 1), 'fur', ('sphere', cx(20), oy + 8, 12, 16, 0.2), TH_B)
    nose = poly(T([(0, 18.5), (3.5, 16.5), (7.5, 17.5), (8, 21.5), (4.5, 23.5), (0, 23)]))
    cv.paint(nose, BLACK)
    return dict(ear=ear, skull=skull, jaw=jaw, muz=muz, mouth=mouth)


def side_horns(cv, ox, oy, side, style):
    T = lambda pts: side_pts(pts, ox, oy, side)
    masks = []
    if style == 'spikes':
        specs = [([(19, 7), (17, 0), (18.5, -7), (22.5, -13.5)], [4.1, 3.2, 2.0, 0.6]),
                 ([(28.5, 6), (30, -2), (32.5, -10), (36, -19)], [3.9, 3.0, 1.9, 0.6])]
    else:  # bull horns sweeping out then up
        specs = [([(18, 7), (12, 4), (7.5, -1.5), (7.5, -8.5)], [4.3, 3.4, 2.2, 0.6]),
                 ([(29, 6), (35, 3), (39, -2.5), (38.5, -9.5)], [4.3, 3.4, 2.2, 0.6])]
    for path, radii in specs:
        m = tube(T(path), radii)
        masks.append(m)
    for m in masks:
        cv.part(m, 'dark', ('dist', 2.6), [0.93, 0.62, 0.30, 0.02])
    return masks


def side_head(cv, ox, oy, side, style, jaw_drop=0):
    base = side_head_base(cv, ox, oy, side, jaw_drop)
    faces.side_face(cv, ox, oy, side, jaw_drop)
    scorch(cv, base['ear'], oy + 38, seed=7 if side > 0 else 11)
    horns = side_horns(cv, ox, oy, side, style)
    base['horns'] = horns
    return base
