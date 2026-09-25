"""danny_quake_ring.png: Danny's quake ring, drawn for the green canvas, in the layout of bixby_quake_ring.png so
BixbyQuakeRingScript's mechanic runs it unchanged (only the sheet's path differs): 4 frames of 40x32 across,
7 rows down, one row per band of the ring's screen tangent (BixbyCombinedArtLayout.RING_ROW_TANGENTS: under
7, 20.3, 35.8, 54.2, 69.7, 83 degrees, and the rest), each row drawn at its band's middle angle (0, 13.7, 28,
45, 62, 76.4 and 90 degrees), rising to the right. Rows 1-5 flip where the ring falls to the right, as Bixby's.
EVERY FRAME'S PIVOT IS ITS CENTRE (20, 16): on the ring's centre line at floor level. Neighbouring segments
play frames one apart, so the dust runs round the ring.
Bixby's art is hellfire through broken earth; Danny's is the canvas itself: a ridge of mat lifted by the wave
(its lit crest n, its shaded back m), torn along a crack (K k), with his cool dust (W Q P g) kicked up off
the crest and chips of mat (n m k K) hopping. The patch across the ring is the hurt band's width seen on the
floor, flattened by 0.36: about 4 texels either side where the ring runs across the screen, 12 where it runs
up it. No keyline, opaque.
"""
import math
import random

import dfx_pal as pal
import dfx_floor as fl

W, H = 40, 32
PX, PY = 20.0, 16.0
FRAME_SIZE = (W, H)
ROWS = 7
FRAMES = 4
NOTE = ('4 frames x 7 rows of 40x32 (the bixby_quake_ring layout): a row per ring tangent 0/13.7/28/45/62/76.4/90 '
        'deg rising right; every pivot = centre (20,16)')
ANGLES = [0.0, 13.7, 28.0, 45.0, 62.0, 76.4, 90.0]
FLATTEN = 0.36
HURT_HALF = 12.0               # BixbyCombinedArtLayout.RING_HURT_HALF_WIDTH, 36 px = 12 texels on the floor
HALF_LEN = 15.0                # half the segment's length along the ring: neighbours are 16 texels apart


def across_half(theta):
    """The hurt band's half-width on screen, perpendicular to the ring, where its tangent is theta."""
    if theta <= 0.0:
        phi = math.pi / 2
    else:
        phi = math.atan(FLATTEN / math.tan(math.radians(theta)))
    return HURT_HALF * FLATTEN / math.sqrt(math.sin(phi) ** 2 + (FLATTEN * math.cos(phi)) ** 2)


def frame(row, f):
    g = pal.blank(W, H)
    th = math.radians(ANGLES[row])
    tx, ty = math.cos(th), -math.sin(th)                  # along the ring, rising to the right
    nx, ny = -ty, tx                                       # across it, toward the outside (down-right)
    w = across_half(ANGLES[row])
    rnd = random.Random(row * 7 + 1)
    wob = [rnd.uniform(0, 6.28) for _ in range(3)]
    ridge = 0.45                                           # the lifted ridge's share of the band's width
    # the lifted canvas: a lit crest on one side of the crack, its shaded back on the other, ragged ends
    for y in range(H):
        for x in range(W):
            px, py = x + 0.5 - PX, y + 0.5 - PY
            u = px * tx + py * ty
            v = px * nx + py * ny
            end = HALF_LEN - 1.5 * (1 + math.sin(0.7 * v + wob[0]))
            if abs(u) > end or not (2 <= y <= H - 2):
                continue
            edge = w * (0.72 + 0.12 * math.sin(0.45 * u + wob[1] + f * 0.8))
            if -edge <= v < -edge * (1 - ridge):
                g[y][x] = 'n'
            elif -edge * (1 - ridge) <= v < -0.6:
                g[y][x] = 'n' if v < -edge * 0.55 else 'm'
            elif 0.6 <= v <= edge * 0.7:
                g[y][x] = 'm'
    # the crack along the middle, a zigzag, with its dark depth
    a0, a1 = -HALF_LEN + 1, HALF_LEN - 1
    pts = fl.zigzag(PX + tx * a0, PY + ty * a0, PX + tx * a1, PY + ty * a1, seed=row + 3, jag=0.9, step=2.2)
    for (x, y) in fl.line_texels(pts):
        if 0 <= x < W and 0 <= y < H:
            g[y][x] = 'K'
            xx, yy = int(x + nx * 1.2), int(y + ny * 1.2)
            if 0 <= xx < W and 0 <= yy < H and g[yy][xx] in '.m':
                g[yy][xx] = 'k'
    # chips of mat hopping off the crest
    for j in range(3):
        u = -10 + 10 * j + 3 * math.sin(j * 2.1)
        hop = [0, 2, 3, 1][(f + j) % 4]
        cx = PX + tx * u - nx * (w * 0.8)
        cy = max(1.0, min(H - 3.0, PY + ty * u - ny * (w * 0.8) - hop - 1))
        fl.chip(g, cx, cy, big=False)
    # dust kicked up off the crest: three puffs along it, each rising and thinning over the 4 frames
    for j in range(3):
        k = (f + j) % 4
        u = -9 + 9 * j
        r = [3.2, 4.0, 4.4, 3.8][k]
        rise = [2.0, 4.5, 7.0, 9.0][k]
        cx = PX + tx * u - nx * (w * 0.55)
        cy = PY + ty * u - ny * (w * 0.55) - rise
        cy = max(r * 0.8 + 0.6, min(H - r * 0.8 - 1.6, cy))        # the dust stays inside the frame
        cx = max(r + 0.6, min(W - r - 0.6, cx))
        fl.puff(g, cx, cy, r, shade=[0, 0, 1, 2][k], squash=0.8)
    return pal.rows(g)


def frames():
    """Row by row: frames[row * 4 + f]."""
    return [frame(r, f) for r in range(ROWS) for f in range(FRAMES)]


def rows_of_frames():
    return [[frame(r, f) for f in range(FRAMES)] for r in range(ROWS)]
