"""The rubble the roof leaves: a kit to wall the fighters in with. The architect sets the box; these are
the pieces it is built from, all standing on the floor and y-sorted by their base like the fighters.

brawl_rubble_mound.png   10 frames of 64x48, one strip, static. Lit from the top left, so NEVER flipped:
  a mirrored heap would be lit from the wrong side. Variety comes from the ten, not from flipping.
  0-1  big heaps with a steel beam jutting out: accents, one in four or five
  2-4  big heaps, no beam, up to 38 texels high (114 px): the bulk of the fill and the wall behind Greyson
  5-7  medium heaps, up to 28 texels high: the side walls, and the gaps between the big ones
  8-9  low ridges, up to 16 texels high: the wall IN FRONT of the player. Nothing taller than a ridge
       may stand between the camera and the player, or it covers him (it is y-sorted in front of him).
  THE PIVOT IS THE BOTTOM CENTRE (32, 46): the middle of the heap's footprint on the floor. Centred
  sprite: offset (0, -22). Heaps overlap: set them about 44 texels (132 px) apart along a wall.
brawl_rubble_bits.png    8 frames of 16x12: loose chunks to scatter along the foot of a wall so its
  edge is not a straight line. Pivot bottom centre (8, 11); centred offset (0, -5).

A heap is built like a real one: a dark fill (the crevices) laid first, then faceted chunks, back to
front, lit from the top left, so what shows between them is depth. A beam or two and some rebar come out
of the big ones. The dark only ever shows as crevices and as the contact with the floor, never as an
outline round the silhouette: the chunks at the rim are what the silhouette is made of.
"""
import math
import random

import gb_pal as pal

MW, MH = 64, 48
BASE = 46                                     # the footprint row (pivot y)

KINDS = [
    # (height, half-width, seed, beams)
    (40, 31, 11, 1), (37, 30, 23, 1),                      # 0-1 big, a beam jutting out
    (38, 31, 101, 0), (34, 30, 113, 0), (36, 29, 127, 0),  # 2-4 big, no beam: the bulk of the fill
    (28, 26, 41, 1), (26, 24, 53, 0), (24, 27, 67, 0),     # 5-7 medium
    (16, 30, 71, 0), (13, 29, 83, 0),                      # 8-9 low ridges
]


def envelope(kind):
    h, half, seed, _ = KINDS[kind]
    rnd = random.Random(seed)
    bumps = [(rnd.uniform(-0.6, 0.6), rnd.uniform(0.08, 0.18), rnd.uniform(-0.12, 0.12)) for _ in range(3)]

    def top(x):
        u = (x + 0.5 - MW / 2.0) / half
        if abs(u) >= 1.0:
            return None
        base = (1.0 - abs(u) ** 1.7)
        for (c, w, a) in bumps:
            base += a * math.exp(-((u - c) / w) ** 2)
        return BASE - max(0.0, base) * h
    return top


def _boulder(g, cx, cy, s, rnd, keys=('3', '4', '5', '2')):
    """a faceted chunk: a lit top face, a mid left face and a shaded right face; (cx, cy) is its
    bottom point, s its size"""
    top_k, left_k, right_k, ridge_k = keys
    tilt = rnd.uniform(-0.35, 0.35)
    w = s * rnd.uniform(0.9, 1.25)
    hh = s * rnd.uniform(0.55, 0.8)
    tw = s * rnd.uniform(0.35, 0.5)
    # the box: bottom point (cx, cy); left and right bottom corners; top face above them
    lb = (cx - w * 0.55, cy - hh * (0.35 + tilt * 0.2))
    rb = (cx + w * 0.45, cy - hh * (0.45 - tilt * 0.2))
    lt = (lb[0] + 0.3, lb[1] - hh * 0.7)
    rt = (rb[0] - 0.3, rb[1] - hh * 0.7)
    mt = (cx + tilt * 2, cy - hh * 0.7)
    back = (cx + (tilt - 0.1) * 3, lt[1] - tw)
    pal.poly_fill(g, [lb, (cx, cy), mt, lt], left_k)
    pal.poly_fill(g, [(cx, cy), rb, rt, mt], right_k)
    pal.poly_fill(g, [lt, mt, rt, back], top_k)
    # the lit ridge: the top face's front-left edge
    n = int(max(abs(mt[0] - lt[0]), abs(mt[1] - lt[1])) * 2) + 1
    for i in range(n + 1):
        t = i / float(n)
        x, y = int(lt[0] + (mt[0] - lt[0]) * t), int(lt[1] + (mt[1] - lt[1]) * t)
        if 0 <= y < len(g) and 0 <= x < len(g[0]) and g[y][x] == top_k:
            g[y][x] = ridge_k
    return lt, rt, back


def _beam(g, x0, y0, x1, y1, thick=3):
    """a steel beam: its top in #9DA1C0 with a #D5D9EC highlight, its side #3F3F52, underside #2A2A38"""
    n = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
    for i in range(n + 1):
        t = i / float(n)
        x = x0 + (x1 - x0) * t
        y = y0 + (y1 - y0) * t
        for d in range(thick + 2):
            k = 'S' if d == 0 else ('T' if d == 1 else ('U' if d < thick + 1 else 'V'))
            pal.put(g, int(x), int(y) + d, k)
    # the cut end: the I seen end-on, a lighter cap
    ex, ey = int(x1), int(y1)
    for d in range(thick + 2):
        pal.put(g, ex, ey + d, 'S' if d in (0, thick + 1) else 'T')


def mound_frame(kind):
    g = pal.blank(MW, MH)
    top = envelope(kind)
    h, half, seed, beams = KINDS[kind]
    rnd = random.Random(seed * 7 + 1)
    # 1. the dark between the chunks, inset from the rim so it never outlines the heap
    for x in range(MW):
        t = top(x)
        if t is None:
            continue
        for y in range(int(math.ceil(t + 2.0)), BASE):
            if abs(x + 0.5 - MW / 2.0) < half - 2:
                g[y][x] = 'c'
    # 2. chunks, back (high) to front (low), filling the envelope
    placed = []
    rows_y = list(range(int(BASE - h) + 6, BASE + 1, 5))
    for ry in rows_y:
        step = rnd.uniform(6.5, 9.0)
        x = MW / 2.0 - half + rnd.uniform(0.0, step * 0.6)
        while x < MW / 2.0 + half:
            t = top(int(x))
            if t is not None and ry >= t + 4:
                depth = (ry - (BASE - h)) / float(h)          # 0 at the top of the heap, 1 at its foot
                s = rnd.uniform(5.5, 8.5) + depth * rnd.uniform(2.0, 5.5)
                placed.append((ry + rnd.uniform(-1.5, 1.5), x + rnd.uniform(-1.5, 1.5), s))
            x += step + rnd.uniform(-1.0, 2.0)
    # the rim: chunks whose tops sit on the envelope, so the silhouette is chunks, not a curve
    xr = MW / 2.0 - half + 2
    while xr < MW / 2.0 + half - 2:
        t = top(int(xr))
        if t is not None:
            s = rnd.uniform(6.0, 9.0)
            placed.append((t + s * 0.65, xr, s))
        xr += rnd.uniform(5.0, 7.5)
    placed.sort()
    beam_at = sorted(rnd.sample(range(len(placed)), min(beams, len(placed)))) if beams else []
    for i, (cy, cx, s) in enumerate(placed):
        if cy > BASE:
            cy = BASE
        # the heap is lit as one mass, from the top left: chunks up its left shoulder step lighter,
        # chunks down its right flank and along its foot step darker
        lx = (cx - MW / 2.0) / half
        ly = (cy - (BASE - h)) / float(h)
        light = -0.65 * lx - 0.55 * (ly - 0.45) + rnd.uniform(-0.18, 0.18)
        if light > 0.32:
            keys = ('2', '3', '4', '1')
        elif light < -0.30:
            keys = ('4', '5', 'c', '3')
        else:
            keys = ('3', '4', '5', '2')
        _boulder(g, cx, cy, s, rnd, keys)
        if i in beam_at:
            # a beam jutting up and out of the heap from this depth
            side = 1 if cx < MW / 2.0 else -1
            ln = rnd.uniform(12, 18)
            _beam(g, cx - side * 4, cy - s * 0.6, cx + side * ln, cy - s * 0.6 - ln * 0.45)
    # 3. rebar out of the top of the big ones
    if kind <= 4:
        for i in range(2 if kind >= 2 else 3):
            x = int(MW / 2.0 + rnd.uniform(-half * 0.5, half * 0.5))
            t = top(x)
            if t is None:
                continue
            y = int(t) + 2
            lean = rnd.choice((-1, 1))
            for j in range(rnd.randint(4, 7)):
                pal.put(g, x + (lean if j > 2 else 0) + (lean if j > 4 else 0), y - j, 'R' if j < 3 else 'Q')
    # 4. the foot: the heap sits on the floor with a dark contact under its front chunks
    for x in range(MW):
        for y in range(BASE - 1, -1, -1):
            if g[y][x] != '.':
                if y >= BASE - 2 and g[y][x] in '345':
                    g[y][x] = 'c' if g[y][x] == '5' else '5'
                break
    # nothing may be drawn below the footprint row
    for y in range(BASE + 1, MH):
        for x in range(MW):
            g[y][x] = '.'
    return pal.rows(g)


def mound_frames():
    return [mound_frame(k) for k in range(len(KINDS))]


# ------------------------------------------------------------------- bits

BW, BH = 16, 12


def bits_frame(i):
    g = pal.blank(BW, BH)
    rnd = random.Random(900 + i)
    n = 1 + i % 3
    for j in range(n):
        s = rnd.uniform(3.5, 6.5) if n > 1 else rnd.uniform(6.0, 8.5)
        cx = BW / 2.0 + (j - (n - 1) / 2.0) * 4.5 + rnd.uniform(-1, 1)
        _boulder(g, cx, BH - 1 - rnd.uniform(0, 1.5 if j else 0), s, rnd)
    if i in (3, 6):
        _beam(g, 3, 5, 12, 3, thick=2)
    return pal.rows(g)


def bits_frames():
    return [bits_frame(i) for i in range(8)]
