"""Effects drawn into the beast's frames: dust, speed lines, sweat, impact stars, roar rays, dizzy
stars, debris, ground flashes. Each returns a callable fx(cv, P) for a pose's 'fx' list, stamped after
the body. Solid things (dust, drops, stars, pebbles) are keylined; light (rays, glows) is not.
"""
import math

from pal import ellipse, fill, poly
from shapes import edge, poly_line, recolor

GROUND = 151


def _stamp(part, outline=True):
    def f(cv, P):
        cv.stamp(part, outline=outline)
    return f


def _put(pixels):
    def f(cv, P):
        for q, k in pixels.items():
            if 0 <= q[0] < cv.w and 0 <= q[1] < cv.h:
                cv.px[q] = k
    return f


def dust(x, size=2, ground=GROUND, drift=1):
    """A dust puff sitting on the ground at x, rolling outward (drift = +1 right, -1 left)."""
    r = {1: [(0, 0, 2.2), (3 * drift, 1, 1.8)],
         2: [(0, 0, 3.2), (4 * drift, 1, 2.8), (-3 * drift, 1, 2.4), (1 * drift, -3, 2.4)],
         3: [(0, 0, 4.2), (6 * drift, 1, 3.6), (-5 * drift, 1, 3.2), (2 * drift, -4, 3.4),
             (9 * drift, -1, 2.6)]}[size]
    pts = set()
    for dx, dy, rr in r:
        pts |= ellipse(x + dx, ground - rr + dy, rr, rr * 0.9)
    part = fill(pts, 'x')
    recolor(part, edge(part, 0, -1, 1), 'w')
    recolor(part, edge(part, 0, 1, 1), 'y')
    recolor(part, edge(part, drift, 0, 1), 'y')
    return _stamp(part)


def speed_lines(lines):
    """Horizontal streaks: (x0, x1, y). Bone white, fading to grey at the tail (x0)."""
    px = {}
    for x0, x1, y in lines:
        n = max(1, x1 - x0)
        for x in range(x0, x1 + 1):
            px[(x, y)] = 'y' if (x - x0) < n * 0.4 else 'w'
    return _put(px)


def sweat(x, y, tilt=0):
    """A drop flung off a head: steel-white, keylined."""
    rows = ['.W.', 'WWU', 'WUU', '.U.'] if tilt >= 0 else ['.W.', 'UWW', 'UUW', '.U.']
    part = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                part[(x + c, y + r)] = ch
    return _stamp(part)


def star4(x, y, r=3, core='Y', ray='P'):
    """A four-point spark, keylined."""
    part = {(x, y): core}
    for i in range(1, r + 1):
        k = ray if i < r else ray
        for dx, dy in ((i, 0), (-i, 0), (0, i), (0, -i)):
            part[(x + dx, y + dy)] = k
    for dx, dy in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        part[(x + dx, y + dy)] = ray
    return _stamp(part)


def star5(x, y, key='O'):
    """A little gold star for the daze, keylined (5x5 body)."""
    rows = ['..O..', '.OOO.', 'OOOOO', '.OOO.', '.O.O.']
    part = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch != '.':
                part[(x + c - 2, y + r - 2)] = key if (r, c) != (1, 2) else 'Y'
    part[(x, y)] = 'Y'
    part[(x + 1, y + 1)] = 'G'
    return _stamp(part)


def rays(cx, cy, n=10, r0=26, r1=34, phase=0.0, keys='PY'):
    """Roar rays: short dashes radiating from a point, no keyline."""
    px = {}
    for i in range(n):
        a = phase + 2 * math.pi * i / n
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.8)
        p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.8)
        seg = poly_line([p0, p1])
        for j, q in enumerate(seg):
            px[q] = keys[0] if j < len(seg) / 2 else keys[1]
    return _put(px)


def pebbles(points):
    """Debris: little charcoal chunks (x, y, size 1 or 2), keylined."""
    part = {}
    for x, y, s in points:
        if s >= 2:
            part.update({(x, y): 'd', (x + 1, y): 'c', (x, y + 1): 'c', (x + 1, y + 1): 'b'})
        else:
            part[(x, y)] = 'd'
    return _stamp(part)


def ground_flash(x, ground=GROUND, w=13, h=7):
    """The flash where a slam lands: a fan of light up off the floor, white-hot at the root."""
    px = {}
    for i in range(9):
        a = math.pi * (0.06 + 0.88 * i / 8)
        L = h + (4 if i % 2 else 0)
        seg = poly_line([(x, ground), (x + math.cos(a) * w * (0.75 if i % 2 else 1), ground - math.sin(a) * L)])
        for j, q in enumerate(seg):
            t = j / max(1, len(seg) - 1)
            px[q] = 'Y' if t < 0.35 else 'P' if t < 0.7 else 'p'
            if t < 0.5:
                px[(q[0] + 1, q[1])] = 'Y' if t < 0.25 else 'P'
    for dx in range(-5, 6):
        px[(x + dx, ground)] = 'Y' if abs(dx) < 3 else 'P'
        px[(x + dx, ground - 1)] = 'Y' if abs(dx) < 2 else 'P'
    return _put(px)


def ground_cracks(x, ground=GROUND, spread=16):
    """Black cracks split along the floor from a slam."""
    part = {}
    for sgn in (1, -1):
        pts = [(x, ground), (x + sgn * spread * 0.4, ground + 1), (x + sgn * spread * 0.7, ground),
               (x + sgn * spread, ground + 2)]
        for q in poly_line(pts):
            part[q] = 'k'
    return _put(part)


def motion_arc(cx, cy, rx, ry, a0, a1, key='w'):
    """A partial ellipse of pale motion, for the spin."""
    px = {}
    steps = int(abs(a1 - a0) * max(rx, ry) / 1.5) + 2
    for i in range(steps + 1):
        a = a0 + (a1 - a0) * i / steps
        px[(int(round(cx + math.cos(a) * rx)), int(round(cy + math.sin(a) * ry)))] = key
    return _put(px)
