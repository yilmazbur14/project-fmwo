"""The juggle's effects, in the house convention of Matt's approved juggle (the "standard going
forward"): dust puffs are UNOUTLINED balls in the cool whites, lit from the upper left; motion
arcs are thin unoutlined curves in the whites; impact ticks are short black strokes; sweat drops
are the approved flex face's bead (gr_face.SWEAT), keyline and all. No new colours: the whites
'W' 'X' 'x' are his boots' and teeth's, the drop's blues his eyes'.

Every effect is placed clear of the body by at least one pixel, so the lint can tell air from
him (it keylines everything joined to the figure).
"""
import math
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gj_rig as R  # noqa: E402

K = R.K


def _free(cv, q, pad=1):
    """No body pixel within `pad` of q (effects never touch him)."""
    x, y = q
    for dy in range(-pad, pad + 1):
        for dx in range(-pad, pad + 1):
            if (x + dx, y + dy) in cv.px and (x + dx, y + dy) not in cv.fx:
                return False
    return 0 <= x < cv.w and 0 <= y < cv.h


def put(cv, q, k):
    if _free(cv, q):
        cv.px[q] = k
        cv.fx.add(q)


def puff(cv, c, r):
    """A dust ball of radius r centred c: lit upper left ('W'), body 'X', shaded lower right
    ('x')."""
    cx, cy = c
    pts = []
    for y in range(int(math.floor(cy - r)) - 1, int(math.ceil(cy + r)) + 2):
        for x in range(int(math.floor(cx - r)) - 1, int(math.ceil(cx + r)) + 2):
            u, v = (x - cx) / r, (y - cy) / r
            d = u * u + v * v
            if d <= 1.0:
                pts.append((x, y, u, v, d))
    ok = all(_free(cv, (x, y)) for (x, y, _, _, _) in pts)
    if not ok:
        return
    for (x, y, u, v, d) in pts:
        l = -(u * 0.62 + v * 0.62) + 0.35 * (1 - d)
        k = 'W' if l > 0.45 else ('X' if l > -0.35 else 'x')
        cv.px[(x, y)] = k
        cv.fx.add((x, y))


def arc(cv, c, r, a0, a1, lead='W', body='X', tail='x'):
    """A 1px motion arc round c at radius r from bearing a0 to a1 (degrees, screen): its leading
    end (a1) bright, its tail fading."""
    n = max(2, int(abs(a1 - a0) / 180.0 * math.pi * r * 1.6))
    seen = []
    for i in range(n + 1):
        t = i / float(n)
        a = math.radians(a0 + (a1 - a0) * t)
        q = (int(round(c[0] + r * math.cos(a))), int(round(c[1] + r * math.sin(a))))
        if not seen or seen[-1][0] != q:
            seen.append((q, t))
    for q, t in seen:
        put(cv, q, lead if t > 0.75 else (body if t > 0.3 else tail))


def outer_radius(cv, c, a0, a1):
    """How far his drawn pixels reach from c within the bearings a0..a1 (degrees)."""
    lo, hi = min(a0, a1), max(a0, a1)
    best = 0.0
    for (x, y) in cv.px:
        if (x, y) in cv.fx:
            continue
        a = math.degrees(math.atan2(y - c[1], x - c[0]))
        for w in (a - 360.0, a, a + 360.0):
            if lo - 4.0 <= w <= hi + 4.0:
                best = max(best, math.hypot(x - c[0], y - c[1]))
    return best


def swoosh(cv, c, a0, a1, gap=3.0, r_min=30.0):
    """A motion arc just outside him over the bearings a0 (its tail) to a1 (its lead)."""
    r = max(r_min, outer_radius(cv, c, a0, a1) + gap)
    arc(cv, c, r, a0, a1)
    return r


def soles(cv, row):
    """The runs of his pixels on one row: [(x0, x1), ...] left to right."""
    xs = sorted(x for (x, y) in cv.px if y == row and (x, y) not in cv.fx)
    runs, run = [], []
    for x in xs:
        if run and x != run[-1] + 1:
            runs.append((run[0], run[-1]))
            run = []
        run.append(x)
    if run:
        runs.append((run[0], run[-1]))
    return runs


def ticks(cv, c, r0, r1, bearings):
    """Short black impact strokes radiating from c between radii r0 and r1."""
    for b in bearings:
        a = math.radians(b)
        for i in range(int(r1 - r0) + 1):
            rr = r0 + i
            put(cv, (int(round(c[0] + rr * math.cos(a))), int(round(c[1] + rr * math.sin(a)))),
                'k')


def drop(cv, at):
    """The approved sweat bead (gr_face.SWEAT), its top-left at `at`."""
    bead = R.gr_face.SWEAT
    x0 = min(x for x, _ in bead)
    y0 = min(y for _, y in bead)
    pts = {(at[0] + x - x0, at[1] + y - y0): k for (x, y), k in bead.items()}
    if all(_free(cv, q) for q in pts):
        for q, k in pts.items():
            cv.px[q] = k
            cv.fx.add(q)
