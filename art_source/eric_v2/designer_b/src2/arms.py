"""Posable arms in 128-space, built from the same materials as the approved sprite:
chainmail upper arm ('chain' ramp + ring texture), white plate vambrace, spherical elbow cop,
dark-iron gauntlet stamps."""
import math
import lib
from lib import PALC, BLACK, _DARKER, _LIGHTER, TH_METAL, TH_SOFT, hexc, RAMPS
from weapons import FIST_V, FIST_D
from sword import edge


def capsule(p0, p1, r0, r1=None):
    if r1 is None:
        r1 = r0
    W, H = lib.W, lib.H
    m = [[False] * W for _ in range(H)]
    (x0, y0), (x1, y1) = p0, p1
    dx, dy = x1 - x0, y1 - y0
    L2 = dx * dx + dy * dy or 1e-6
    for y in range(max(0, int(min(y0, y1) - max(r0, r1) - 2)), min(H, int(max(y0, y1) + max(r0, r1) + 3))):
        for x in range(max(0, int(min(x0, x1) - max(r0, r1) - 2)), min(W, int(max(x0, x1) + max(r0, r1) + 3))):
            px, py = x + 0.5, y + 0.5
            t = max(0.0, min(1.0, ((px - x0) * dx + (py - y0) * dy) / L2))
            cx, cy = x0 + dx * t, y0 + dy * t
            r = r0 + (r1 - r0) * t
            if (px - cx) ** 2 + (py - cy) ** 2 <= r * r:
                m[y][x] = True
    return m


def upper_arm(cv, S, E, r=5.0):
    m = capsule(S, E, r, r * 0.92)
    cv.part(m, 'chain', ('cyl', S, E, r + 0.5), th=TH_SOFT)
    inner = [[m[y][x] and not e for x, e in enumerate(row)] for y, row in enumerate(edge(m))]
    for y in range(lib.H):
        for x in range(lib.W):
            if inner[y][x]:
                c = cv.px[y][x]
                if (y % 2 == 0 and x % 2 == 0) or (y % 2 == 1 and x % 2 == 1):
                    cv.px[y][x] = _DARKER.get(c, c)
                elif y % 2 == 0 and x % 4 == 1:
                    cv.px[y][x] = _LIGHTER.get(c, c)
    return m


def vambrace(cv, E, Hn, r0=5.6, r1=4.6):
    m = capsule(E, Hn, r0, r1)
    cv.part(m, 'plate', ('cyl', E, Hn, r0 + 1.0), th=TH_METAL)
    return m


def elbow(cv, E, rx=5.0, ry=4.8):
    m = lib.ell(E[0], E[1], rx, ry)
    cv.part(m, 'plate', ('sphere', E[0] - 1, E[1] - 1.5, rx + 0.7, ry + 0.9), th=TH_METAL)
    return m


def shoulder_cap(cv, c, rx=6.5, ry=5.5):
    m = lib.ell(c[0], c[1], rx, ry)
    cv.part(m, 'plate', ('sphere', c[0] - 1.5, c[1] - 2, rx + 1, ry + 1), th=TH_METAL)
    return m


# ------------------------------------------------------------------ hand stamps (anchor = centre)
FIST_H = '\n'.join(''.join(r) for r in zip(*FIST_V.strip('\n').split('\n')))

OPEN_UP = """
.kk.kk.kk.kk....
kIJkIJkJKkKLk...
kIJkIJkJKkKLk...
kIJkIJkJKkKLk...
kIJkIJkJKkKLk.k.
kIJkJJkJKkKLkkJk
kIJJJJJKKKKLkIKk
kIJJJJKKKKLLkJLk
kIJJJKKKKKLLKLMk
kJJJKKKKKLLLMMk.
.kJKKKKKLLLMMk..
..kKKKLLLMMNk...
..kkkkkkkkkkk...
"""

OPEN_FWD = """
..kkkkkkkkk..
.kIIIIIIIJJk.
kIIIIIIIJJJKk
kIJJJJJJKKKLk
kkkkkkkkkkkkk
kIJkIJkJKkKLk
kIJkIJkJKkKLk
kIJkJKkKKkLMk
kJKkJKkKLkLMk
.kk.kk.kk.kk.
"""

FIST_SIDE = """
..kkkkkkk..
.kIIIIIJJk.
kIIIIIJJJKk
kJkkkkkkkKk
kJkKKKLLkLk
kKkLLLLMkLk
kKkLLMMMkMk
kLkMMMMNkMk
.kkkkkkkkk.
"""

STAMPS = {'V': FIST_V, 'H': FIST_H, 'D': FIST_D, 'open_up': OPEN_UP, 'open_fwd': OPEN_FWD, 'side': FIST_SIDE}


def _rows(name):
    return STAMPS[name].strip('\n').split('\n')


def stamp_mask(name, cx, cy, flip=False):
    rows = _rows(name)
    h, w = len(rows), max(len(r) for r in rows)
    x0, y0 = int(round(cx - w / 2)), int(round(cy - h / 2))
    m = [[False] * lib.W for _ in range(lib.H)]
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                X = x0 + (w - 1 - c if flip else c)
                if 0 <= X < lib.W and 0 <= y0 + r < lib.H:
                    m[y0 + r][X] = True
    return m, x0, y0


def cast_shadow(cv, mask, dx, dy):
    tgt = set()
    for y in range(lib.H):
        for x in range(lib.W):
            if mask[y][x]:
                xx, yy = x + dx, y + dy
                if 0 <= xx < lib.W and 0 <= yy < lib.H and not mask[yy][xx]:
                    tgt.add((xx, yy))
    for x, y in tgt:
        c = cv.px[y][x]
        if c is not None and c != BLACK:
            cv.px[y][x] = _DARKER.get(c, c)


def hand(cv, name, c, flip=False, shadow=True):
    m, x0, y0 = stamp_mask(name, c[0], c[1], flip)
    if shadow:
        cast_shadow(cv, m, 1, 2)
    cv.stamp(STAMPS[name], x0, y0, flip=flip)
    return m


def solve_elbow(S, Hn, l1, l2, bend=1):
    """2-bone IK: elbow position for shoulder S, hand Hn, lengths l1, l2; bend = +1/-1 picks the side."""
    dx, dy = Hn[0] - S[0], Hn[1] - S[1]
    d = math.hypot(dx, dy)
    d = max(1e-3, min(d, l1 + l2 - 1e-3))
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    h = math.sqrt(max(0.0, l1 * l1 - a * a))
    ux, uy = dx / math.hypot(dx, dy), dy / math.hypot(dx, dy)
    mx, my = S[0] + ux * a, S[1] + uy * a
    return (mx - uy * h * bend, my + ux * h * bend)
