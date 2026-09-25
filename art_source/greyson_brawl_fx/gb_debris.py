"""The roof coming in: brawl_debris (falling chunks with their dust trails), brawl_debris_shadow (the
spot on the floor it is going to hit) and brawl_debris_land (the hit).

brawl_debris.png   8 frames of 32x56, one strip.  frame = shape * 2 + spin.
  shape  0 a concrete block with a rebar stub, 1 a slab of the ceiling, 2 a steel beam stub,
         3 a clump of three small chunks
  spin   0 and 1 alternate at 0.06 s while it falls: two drawn orientations of the same piece, lit from
         the top left in both, so it tumbles without the engine ever rotating it (Matt's shards do the
         same).
  The chunk is the bottom 32 rows (up to 96 px across at 3x); its dust trail streams up the 24 above it,
  thinning in two alpha steps.
  THE PIVOT IS THE BOTTOM CENTRE (16, 56): the point that meets the floor. Centred sprite: offset (0,-28).
brawl_debris_shadow.png   1 frame of 36x12, solid black; the code grows and fades it (0.3 -> 1.0 scale,
  0.15 -> 0.5 alpha over the fall, as MattGlassFloor.drop_shard does). Pivot: centre (18, 6).
brawl_debris_land.png   6 frames of 80x48 at 0.05 s. THE PIVOT IS (40, 40): the landing point.
  f0 the smack: a flat burst along the floor and the first bits kicked up
  f1-3 dust rolling out both ways and billowing up, bits flying in arcs and dropping
  f4-5 thinning a step darker, then in the 176 and 96 alpha steps; the bits come to rest
"""
import math

import gb_pal as pal

W, H = 32, 56
TOP = 24                                    # the chunk's box starts here
SC = 32.0 / 24.0                            # the shapes are drawn in a 24 box, scaled to 32

# Faces as (polygon in the chunk's 24x24 box, key), drawn in order; then detail strokes.
# Keys: '2' lit top, '3' light side, '4' mid side, '5' shade side, 'c' crevice, steel S T U V, rust R Q.
SHAPES = {
    # a concrete block: seen from an edge (spin 0) and from a corner (spin 1)
    (0, 0): dict(faces=[
        ([(4.5, 8), (13, 3.5), (20.5, 8.5), (12, 13)], '3'),
        ([(4.5, 8), (12, 13), (11.5, 23.5), (4, 17.5)], '4'),
        ([(12, 13), (20.5, 8.5), (20, 17.5), (11.5, 23.5)], '5'),
    ], lines=[((12, 13), (11.8, 23), 'c'), ((14.5, 15), (18.5, 13), 'c')],
        rebar=[(15, 4), (16, 3), (17, 2), (17, 1)], lit=[((4.5, 8), (13, 3.5))]),
    (0, 1): dict(faces=[
        ([(6, 5.5), (16, 3), (21, 10), (11, 12.5)], '3'),
        ([(6, 5.5), (11, 12.5), (13, 23.5), (3.5, 15)], '4'),
        ([(11, 12.5), (21, 10), (19.5, 19), (13, 23.5)], '4'),
    ], lines=[((11, 12.5), (12.8, 23), 'c'), ((5.5, 12), (8.5, 17), 'c')],
        rebar=[(4, 6), (3, 5), (2, 5)], lit=[((6, 5.5), (16, 3))]),
    # a slab of the ceiling: flat and wide, then nearly edge-on as it turns
    (1, 0): dict(faces=[
        ([(1.5, 11), (14, 6.5), (22.5, 11.5), (10, 16)], '3'),
        ([(1.5, 11), (10, 16), (10, 20), (1.5, 15)], '4'),
        ([(10, 16), (22.5, 11.5), (22.5, 15.5), (10, 20)], '5'),
        ([(10, 20), (12, 23.5), (13.5, 19.5)], '5'),
    ], lines=[((6, 12.5), (13, 10), 'c'), ((13, 10), (15, 13.5), 'c')],
        rebar=[(21, 10), (22, 9), (23, 8)], lit=[((1.5, 11), (14, 6.5))]),
    (1, 1): dict(faces=[
        ([(8, 3), (14, 1.5), (16.5, 18), (10.5, 20)], '4'),
        ([(14, 1.5), (17, 3), (19, 19.5), (16.5, 18)], '5'),
        ([(10.5, 20), (16.5, 18), (19, 19.5), (12.5, 23.5)], '4'),
    ], lines=[((10, 8), (14.5, 7), 'c')],
        rebar=[(9, 2), (8, 1), (8, 0)], lit=[((8, 3), (14, 1.5)), ((8, 3), (10.5, 20))]),
    # a steel beam stub: along its length, then end-on showing the I
    (2, 0): dict(faces=[
        ([(1.5, 9), (17, 4.5), (22.5, 7), (7, 11.5)], 'T'),
        ([(7, 11.5), (22.5, 7), (22.5, 12), (7, 16.5)], 'U'),
        ([(1.5, 9), (7, 11.5), (7, 16.5), (1.5, 14)], 'V'),
        ([(7, 16.5), (22.5, 12), (22, 14.5), (11.5, 23.5), (7, 19)], 'V'),
    ], lines=[((2, 11.5), (6.5, 13.5), 'S')], rebar=[], lit=[((1.5, 9), (17, 4.5))]),
    (2, 1): dict(faces=[
        # the I, end-on: top flange, web, bottom flange
        ([(4, 4), (19, 4), (19, 8), (4, 8)], 'T'),
        ([(10, 8), (13.5, 8), (13.5, 16), (10, 16)], 'U'),
        ([(4, 16), (19, 16), (19, 20), (4, 20)], 'U'),
        ([(19, 4), (21.5, 6), (21.5, 22), (19, 20)], 'V'),
        ([(4, 20), (19, 20), (21.5, 22), (12.5, 23.5)], 'V'),
    ], lines=[((4, 4), (18.5, 4), 'S'), ((4.2, 16), (9.5, 16), 'S')],
        rebar=[], lit=[]),
    # a clump: three small chunks together
    (3, 0): dict(faces=[
        ([(2, 12), (7, 9), (11, 12), (6, 15)], '3'), ([(2, 12), (6, 15), (6, 19), (2, 16)], '4'),
        ([(6, 15), (11, 12), (11, 16), (6, 19)], '5'),
        ([(12, 7), (17, 4), (21.5, 7), (16.5, 10)], '3'), ([(12, 7), (16.5, 10), (16, 15), (12, 12)], '4'),
        ([(16.5, 10), (21.5, 7), (21, 12), (16, 15)], '5'),
        ([(7, 17), (12, 14.5), (16, 17.5), (11, 20)], '3'), ([(7, 17), (11, 20), (12, 23.5), (7, 21)], '4'),
        ([(11, 20), (16, 17.5), (15.5, 21), (12, 23.5)], '5'),
    ], lines=[], rebar=[], lit=[]),
    (3, 1): dict(faces=[
        ([(3, 7), (8, 5), (11, 8), (6, 10)], '3'), ([(3, 7), (6, 10), (6.5, 14), (3, 11)], '4'),
        ([(6, 10), (11, 8), (10.5, 12), (6.5, 14)], '5'),
        ([(13, 10), (18, 8.5), (21.5, 12), (16, 14)], '3'), ([(13, 10), (16, 14), (16, 18), (13, 14)], '4'),
        ([(16, 14), (21.5, 12), (21, 16), (16, 18)], '5'),
        ([(6, 16), (11, 14), (14, 17), (9.5, 19.5)], '3'), ([(6, 16), (9.5, 19.5), (12, 23.5), (6, 20)], '4'),
        ([(9.5, 19.5), (14, 17), (14, 20.5), (12, 23.5)], '5'),
    ], lines=[], rebar=[], lit=[]),
}


def _line(g, a, b, k, oy=0):
    n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
    for i in range(n + 1):
        t = i / float(n)
        pal.put(g, int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t) + oy, k)


def _chunk(g, shape, spin):
    s = SHAPES[(shape, spin)]
    for pts, k in s['faces']:
        pal.poly_fill(g, [(x * SC, y * SC + TOP) for (x, y) in pts], k)
    lit_key = {'3': '2', 'T': 'S'}
    for a, b in s['lit']:
        # the lit ridge along the top face's upper-left edge, one step lighter than the face
        a, b = (a[0] * SC, a[1] * SC), (b[0] * SC, b[1] * SC)
        n = int(max(abs(b[0] - a[0]), abs(b[1] - a[1])) * 2) + 1
        for i in range(n + 1):
            t = i / float(n)
            x, y = int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t) + TOP
            if 0 <= y < H and 0 <= x < W and g[y][x] in lit_key:
                g[y][x] = lit_key[g[y][x]]
    for a, b, k in s['lines']:
        _line(g, (a[0] * SC, a[1] * SC), (b[0] * SC, b[1] * SC), k, TOP)
    for i, (x, y) in enumerate(s['rebar']):
        # rebar keeps its one-texel thickness: scale the path, then draw it as a line
        if i:
            px, py = s['rebar'][i - 1]
            _line(g, (px * SC, py * SC), (x * SC, y * SC), 'R' if i < len(s['rebar']) - 1 else 'Q', TOP)


def _trail(g, shape, spin):
    """dust shed as it falls: puffs streaming up from the top of the chunk, thinning"""
    top = min(y for y in range(TOP, H) for x in range(W) if g[y][x] != '.')
    wob = 1.0 if spin else -1.0
    cx = W / 2.0
    puffs = [(cx + 0.5 * wob, top - 4.0, 3.8, 0, 0), (cx - 0.8 * wob, top - 10, 3.2, 1, 1),
             (cx + 1.0 * wob, top - 15.5, 2.6, 1, 1), (cx - 0.5 * wob, top - 20, 2.1, 1, 2),
             (cx + 0.8 * wob, top - 23.2, 1.4, 2, 2)]
    if shape == 2:
        puffs = puffs[:3]                           # steel sheds less
    trail = pal.blank(W, H)
    for (x, y, r, fade, thin) in puffs:
        pal.puff(trail, x, y, r, fade, thin)
    for y in range(H):
        for x in range(W):
            if g[y][x] == '.' and trail[y][x] != '.':
                g[y][x] = trail[y][x]


def debris_frame(shape, spin):
    g = pal.blank(W, H)
    _chunk(g, shape, spin)
    _trail(g, shape, spin)
    return pal.rows(g)


def debris_frames():
    return [debris_frame(s, p) for s in range(4) for p in range(2)]


# --------------------------------------------------------------- shadow

SW, SH = 36, 12


def shadow_frames():
    g = pal.blank(SW, SH)
    for y in range(SH):
        for x in range(SW):
            dx = (x + 0.5 - SW / 2.0) / (SW / 2.0)
            dy = (y + 0.5 - SH / 2.0) / (SH / 2.0)
            if dx * dx + dy * dy <= 1.0:
                g[y][x] = 'k'
    return [pal.rows(g)]


# ------------------------------------------------------------------ land

LW, LH = 80, 48
PX, PY = 40.0, 40.0

# dust per frame: (x offset, y offset, radius), mirrored left/right with a little asymmetry
PUFFS = [
    [(0, -1, 5.5), (7, 0, 4.0), (13, 0.5, 2.8)],
    [(4, -2, 6.5), (13, -0.5, 5.0), (21, 0.5, 3.8), (0, -5, 5.0)],
    [(7, -4, 7.5), (18, -2, 6.5), (28, -0.5, 5.0), (35, 0.5, 3.2), (1, -9, 5.5)],
    [(9, -7, 8.0), (22, -4.5, 7.5), (32, -2, 6.0), (39, -0.5, 3.8), (2, -12, 6.0)],
    [(11, -9, 7.0), (25, -7, 6.5), (35, -4, 5.0), (3, -15, 5.0)],
    [(13, -11, 5.5), (27, -9, 5.0), (37, -6, 3.5), (4, -17, 3.5)],
]
FADE = [0, 0, 0, 0, 1, 1]
THIN = [0, 0, 0, 0, 1, 2]
# bits kicked out: (vx, vy) per bit in texels per frame, with gravity; frames 0..5
BITS = [(-3.2, -3.0, '3'), (2.8, -3.6, '4'), (-5.5, -1.8, '5'), (5.0, -2.2, '3'), (-1.2, -4.4, '2'),
        (1.6, -4.0, '5'), (-7.0, -1.0, '4'), (7.2, -1.2, '3')]


def land_frame(f):
    g = pal.blank(LW, LH)
    if f == 0:
        # the smack: a wide low sheet of dust at the point of impact, bright on top
        for y in range(int(PY) - 3, int(PY) + 2):
            for x in range(LW):
                dx = abs(x + 0.5 - PX)
                half = 22 - 4.5 * abs(y + 0.5 - (PY - 1))
                if dx <= half:
                    g[y][x] = '1' if y < PY - 2 else ('2' if y < PY else '4')
    for (ox, oy, r) in PUFFS[f]:
        for sx, jit in ((1, 0.0), (-1, 0.7)):
            pal.puff(g, PX + sx * (ox + jit), PY + oy + (0.5 if sx < 0 else 0.0), r, FADE[f], THIN[f])
    # the bits: chunks thrown up out of the dust in arcs, over it, coming down to rest by f4
    for i, (vx, vy, k) in enumerate(BITS):
        t = f + 0.8
        x = PX + vx * t * 1.1
        y = PY - 3 + vy * 1.5 * t + 0.95 * t * t
        rest = PY + 1 + (i % 3)
        y = min(y, rest)
        big = i % 3 != 2
        _bit(g, int(x), int(y), big)
    return pal.rows(g)


def _bit(g, x, y, big):
    """a thrown chunk: a lit top edge over a mid body and a shaded underside"""
    if big:
        for dx, dy, k in ((0, 0, '2'), (1, 0, '3'), (2, 0, '3'), (0, 1, '4'), (1, 1, '4'), (2, 1, '5'),
                          (1, 2, '5'), (2, 2, 'c')):
            pal.put(g, x + dx, y + dy, k)
    else:
        for dx, dy, k in ((0, 0, '3'), (1, 0, '4'), (0, 1, '5'), (1, 1, 'c')):
            pal.put(g, x + dx, y + dy, k)


def land_frames():
    return [land_frame(f) for f in range(6)]
