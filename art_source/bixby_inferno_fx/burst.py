"""bixby_inferno_burst.png: the breath leaving his three mouths and merging into the cone's start.

Frame 64x64 texels, 7 frames: ignite 0-1 (played once), burn 2-4 (loop), die 5-6 (played once).

Three streams pour in: the middle mouth's straight down from the top edge at (32, 0), the side mouths' in
from the left and right edges at (0, 16) and (63, 16), sweeping inward and then down. They meet in a
white-hot ball at MERGE (32, 30), and gush out below it in a fan of lobes pointing down and outward: the
start of the cone, which the flood and the edge strips carry on across the ring. No keyline, like the rest
of Bixby's fire: a dark-blood rim, then the throat ramp inward to a white core.

PIVOT: MERGE (32, 30), where the three streams' centrelines meet and the fan starts; a centred Sprite2D
puts it on its node with offset (0, +2). The perch art's mouth flames should run into the three entry
points (the side ones level, so side mouths wider apart than the frame just lengthen them). The code
anchors the burst on the cone's apex, (960, 145): that fits if the perch mouths sit about level with the
rope, since the middle stream then reaches 90 px up and the side ones enter 42 px up, 96 px either side.
If the perch mouths hang lower, put MERGE about 20 px under the middle mouth instead; the cone's edges can
still start at the apex, behind his body.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from firelib import rings, put, close_holes, periodic_noise  # noqa: E402

W, H = 64, 64
MERGE = (32, 30)
ENTRY = {'mid': (32, 0), 'left': (0, 16), 'right': (63, 16)}
# Each stream's bend: the side ones run level from the edge, then turn down into the ball.
BEND = {'mid': (32, 15), 'left': (22, 15), 'right': (41, 15)}


def blank():
    return [['.'] * W for _ in range(H)]


def disc(cx, cy, r):
    out = set()
    for y in range(int(cy - r) - 1, int(cy + r) + 2):
        for x in range(int(cx - r) - 1, int(cx + r) + 2):
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r:
                out.add((x, y))
    return out


def bezier(p0, p1, p2, t):
    a = (1 - t) * (1 - t)
    b = 2 * (1 - t) * t
    c = t * t
    return (a * p0[0] + b * p1[0] + c * p2[0], a * p0[1] + b * p1[1] + c * p2[1])


def stroke(p0, p1, p2, r0, r1, wobble=0.0, phase=0.0, steps=40, taper=1.0):
    """A tapered curved band from p0 (radius r0) to p2 (radius r1), bent toward p1, its edge rippling.
    taper < 1 keeps it wide for longer and pinches it only near the end (a flame lobe)."""
    out = set()
    for i in range(steps + 1):
        t = i / steps
        x, y = bezier(p0, p1, p2, t)
        r = r1 + (r0 - r1) * (1.0 - t) ** taper
        r *= 1.0 + wobble * math.sin(2 * math.pi * (2.2 * t + phase))
        out |= disc(x, y, max(0.6, r))
    return out


def tongue(root, angle_deg, length, width, curl=0.0, phase=0.0):
    """A flame tongue from root, pointing at angle_deg (0 = straight down, + = toward screen right)."""
    a = math.radians(angle_deg)
    d = (math.sin(a), math.cos(a))
    n = (d[1], -d[0])
    tip = (root[0] + d[0] * length + n[0] * curl, root[1] + d[1] * length + n[1] * curl)
    mid = (root[0] + d[0] * length * 0.5 + n[0] * curl * 0.2, root[1] + d[1] * length * 0.5)
    return stroke(root, mid, tip, width / 2.0, 0.35, wobble=0.12, phase=phase, taper=0.55)


# The gush's heat: hottest at the merge, cooling outward, with flow streaks radiating from it and the
# streams' centrelines running hot. Interior texels (past the rim bands) are coloured from it.
STREAK = periodic_noise(W, H, [(5, 3, 1.0), (7, -4, 0.7), (3, 6, 0.5)], seed=78)


def stream_centres():
    """Points along the three streams' centrelines (the same curves gush() strokes)."""
    pts = []
    mx, my = MERGE
    for key in ('mid', 'left', 'right'):
        end = (mx, my) if key == 'mid' else (mx + (-3 if key == 'left' else 3), my + 1)
        for i in range(41):
            pts.append(bezier(ENTRY[key], BEND[key], end, i / 40.0))
    return pts


CENTRES = stream_centres()


def heat(x, y, f, reach):
    mx, my = MERGE
    dx, dy = x - mx, (y - my - 2) * 1.05
    r = math.hypot(dx, dy)
    theta = math.atan2(dx, dy)
    h = 1.0 - r / reach
    h += 0.13 * math.sin(9.0 * theta + 1.7 * f) + 0.12 * (STREAK[y][x] - 0.5)
    if y < my + 2:                    # in the streams: hot along their centrelines
        d = min(math.hypot(x + 0.5 - px, y + 0.5 - py) for px, py in CENTRES)
        h = max(h, 0.95 - d * 0.2)
    return h


def paint(g, shape, rims=('r', 'N', 'p'), inner=(('W', 0.84), ('Y', 0.55), ('P', 0.28), ('p', -9.0)), f=0,
          reach=30.0, cool=None):
    """Rim bands by erosion ring (outermost first), then the interior from the heat field."""
    depth = rings(shape)
    for (x, y), d in depth.items():
        if cool:
            d = max(0, d - cool(x, y))
        if d < len(rims):
            k = rims[d]
        else:
            h = heat(x, y, f, reach)
            k = next(key for key, th in inner if h >= th)
        put(g, x, y, k)


# The fan below the merge: wide lobes, then smaller tongues between them for a ragged front.
# (angle from straight down, + toward screen right; length; root width)
FAN = [(-58, 21, 12), (-30, 27, 14), (0, 31, 15), (30, 27, 14), (58, 21, 12),
       (-44, 16, 6), (-15, 20, 7), (15, 20, 7), (44, 16, 6)]
FLICK = [(1.0, 0.0), (1.12, 0.5), (0.9, -0.4)]


def gush(scale=1.0, width=1.0, f=0, streams=1.0, stream_w=1.0, ball=1.0):
    """The whole burst's silhouette: streams, merge ball, fan."""
    mx, my = MERGE
    s = set()
    if streams > 0:
        lx, ly = ENTRY['left']
        rx, ry = ENTRY['right']
        ph = 0.33 * f
        s |= stroke(ENTRY['mid'], BEND['mid'], (mx, my), 4.5 * stream_w, 7.5 * stream_w, wobble=0.16, phase=ph, steps=30)
        s |= stroke((lx, ly), BEND['left'], (mx - 3, my + 1), 3.8 * stream_w, 6.0 * stream_w, wobble=0.18, phase=ph + 0.3)
        s |= stroke((rx, ry), BEND['right'], (mx + 3, my + 1), 3.8 * stream_w, 6.0 * stream_w, wobble=0.18, phase=ph + 0.6)
    if ball > 0:
        s |= {(x, y) for (x, y) in disc(mx, my + 2, 10.5 * ball)}
    for j, (ang, ln, w) in enumerate(FAN):
        k, dang = FLICK[(f + j) % 3]
        L = ln * scale * k
        if L < 2:
            continue
        s |= tongue((mx + ang / 12.0, my + 5), ang * (0.85 + 0.15 * width) + dang * 6, L, w * width,
                    curl=(1.5 if j % 2 else -1.5) * k, phase=0.2 * f + 0.13 * j)
    s = {(x, y) for (x, y) in s if 0 <= x < W and 0 <= y < H}
    return close_holes(close_holes(s))


def hotter_near_merge(x, y):
    """Texels far from the merge are one or two rings cooler: the gush cools as it spreads."""
    mx, my = MERGE
    d = math.hypot(x - mx, (y - my) * 1.1)
    return 0 if d < 18 else 1


def sparks(g, f, n, seed, keys='PY'):
    rnd = random.Random(seed + f)
    for j in range(n):
        x, y = rnd.randint(2, W - 3), rnd.randint(2, H - 3)
        if g[y][x] == '.':
            put(g, x, y, keys[j % len(keys)])


def ignite_frame(t):
    g = blank()
    if t == 0:
        # the streams leave the mouths: short, thin, white-hot; nothing has met yet
        mx, my = MERGE
        s = set()
        s |= stroke(ENTRY['mid'], (mx, 5), (mx, 11), 3.0, 4.0, steps=16)
        s |= stroke(ENTRY['left'], (6, 16), (12, 16), 2.5, 3.5, steps=16)
        s |= stroke(ENTRY['right'], (57, 16), (51, 16), 2.5, 3.5, steps=16)
        paint(g, close_holes(s), rims=('N', 'P'), inner=(('W', 0.5), ('Y', -9.0)))
        sparks(g, 0, 4, 500)
        return g
    # they meet: a flash-bright ball, the fan only starting
    paint(g, gush(scale=0.4, width=1.2, f=0, ball=1.15), rims=('N', 'P'), inner=(('W', 0.55), ('Y', -9.0)))
    sparks(g, 1, 8, 500)
    return g


def burn_frame(t):
    g = blank()
    paint(g, gush(scale=1.0, f=t), f=t)
    sparks(g, t, 7, 600)
    return g


def die_frame(t):
    g = blank()
    if t == 0:
        paint(g, gush(scale=0.7, width=0.8, f=1, stream_w=0.6, ball=0.7), rims=('r', 'n', 'N'),
              inner=(('P', 0.75), ('p', 0.45), ('N', -9.0)), f=1, reach=24.0)
        sparks(g, 0, 5, 700, keys='pN')
        return g
    # t 1: the streams are gone; a guttering knot of flame where they met, embers and smoke
    mx, my = MERGE
    s = disc(mx, my + 4, 5.5)
    for ang, ln in ((-35, 8), (0, 10), (35, 8)):
        s |= tongue((mx, my + 6), ang, ln, 5)
    paint(g, close_holes(s), rims=('r', 'n'), inner=(('p', 0.7), ('N', -9.0)), reach=14.0)
    for (x, y, r) in ((22, 14, 3), (42, 11, 2), (33, 6, 2)):
        body = disc(x, y, r)
        dep = rings(body)
        for (px, py), d in dep.items():
            put(g, px, py, 'z' if d == 0 else ('x' if (px - x) + (py - y) < -1 else 'y'))
    sparks(g, 1, 6, 700, keys='nN')
    return g


def frames():
    return [ignite_frame(0), ignite_frame(1)] + [burn_frame(t) for t in range(3)] + [die_frame(0), die_frame(1)]
