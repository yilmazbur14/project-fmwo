"""v2 in-sprite effects (shared). All functions take a rig2.Frame."""
import math
import rig2 as R
from lib import PALC

WHITE = PALC['W']


def smear_arc(fr, c, r_out, width0, width1, a0, a1, ground=190):
    """crescent motion smear from angle a0 to a1 (degrees, screen coords, y down; a1 may be < a0).
    Width grows from width0 to width1 along the sweep. Never drawn below `ground`."""
    cx, cy = c
    span = a1 - a0
    wmax = max(width0, width1)
    for y in range(min(fr.H, ground + 1)):
        for x in range(fr.W):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            r = math.hypot(dx, dy)
            if r > r_out + 0.5 or r < r_out - wmax - 1:
                continue
            a = math.degrees(math.atan2(dy, dx))
            t = None
            for k in (-720, -360, 0, 360, 720):
                tt = (a + k - a0) / span
                if 0 <= tt <= 1:
                    t = tt
                    break
            if t is None:
                continue
            w = width0 + (width1 - width0) * t
            inner = r_out - w
            if inner <= r <= r_out:
                q = (r - inner) / max(1e-6, w)
                if q > 0.7:
                    fr.setc(x, y, WHITE)
                elif q > 0.35:
                    fr.set(x, y, 'A')
                elif t > 0.35:
                    fr.set(x, y, 'B')


def ray(fr, p0, p1, w0, ch='W'):
    x0, y0 = p0
    x1, y1 = p1
    L = math.hypot(x1 - x0, y1 - y0)
    n = int(L * 2) + 1
    for i in range(n + 1):
        t = i / n
        w = w0 * (1 - t)
        cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
        for ox in range(int(-w - 1), int(w + 2)):
            for oy in range(int(-w - 1), int(w + 2)):
                if ox * ox + oy * oy <= w * w + 0.25:
                    fr.set(int(math.floor(cx + ox)), int(math.floor(cy + oy)), ch)


def sparkle(fr, x, y, size=2):
    fr.set(x, y, 'W')
    for k in range(1, size + 1):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            fr.set(x + dx, y + dy, 'W' if k < size else 'B')


def glint(fr, x, y):
    fr.set(x, y, 'W')
    for k in (1, 2, 3):
        for dx, dy in ((k, 0), (-k, 0), (0, k), (0, -k)):
            fr.set(x + dx, y + dy, 'W' if k < 3 else 'A')
    for dx, dy in ((1, 1), (-1, -1), (1, -1), (-1, 1)):
        fr.set(x + dx, y + dy, 'A')


def ellipse_fill(fr, cx, cy, rx, ry, ch, ground=191):
    for y in range(int(cy - ry - 1), min(ground, int(cy + ry + 1)) + 1):
        for x in range(int(cx - rx - 1), int(cx + rx + 2)):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1:
                fr.set(x, y, ch)


PUFF = """
...kkkk...
.kkWWWAkk.
kWWWWWAABk
kWWWAAABBk
kAAABBBCCk
.kkBCCCkk.
...kkkk...
"""
PUFF_S = """
.kkk.
kWWAk
kABCk
.kkk.
"""
ROCK = """
.kk.
kKLk
kLMk
.kk.
"""
CLOD = """
.kk.
knok
.kk.
"""
DROP = """
.d.
dfd
fjf
.f.
"""


def puff(fr, x, y, small=False):
    fr.stamp(PUFF_S if small else PUFF, x, y)


def rock(fr, x, y):
    fr.stamp(ROCK, x, y)


def clod(fr, x, y):
    fr.stamp(CLOD, x, y)


def sweat(fr, x, y):
    fr.stamp(DROP, x, y)


def crack(fr, pts, ch='k'):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            fr.set(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), ch)


def strain_marks(fr, x, y, flip=False):
    s = -1 if flip else 1
    for dx, dy in ((0, -3), (s * 3, -2), (s * 4, 1)):
        fr.set(x + dx, y + dy, 'W')
        fr.set(x + dx + s * (1 if dx else 0), y + dy - (1 if dy < 0 else 0), 'W')


def shock_arcs(fr, cx, arcs, ground=190):
    """white shock arcs racing along the ground from cx: arcs = [(r0, reach, lift), ...]"""
    for r0, reach, lift in arcs:
        for x in range(fr.W):
            d = abs(x - cx)
            if r0 <= d <= reach:
                t = (d - r0) / max(1, reach - r0)
                y = ground - int(round(lift * (1 - t) * t * 2.2))
                fr.set(x, y, 'W')
                if t < 0.55:
                    fr.set(x, y + 1, 'A')
