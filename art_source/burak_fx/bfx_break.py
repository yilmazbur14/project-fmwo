"""burak_barrel_break.png: a keg smashed by the third punch, sized for the 2x keg (48x56). 6 frames of
128x96 at 0.05 s, one strip.
THE PIVOT IS (64, 88): the keg's floor point (its burak_barrel pivot). As a centred Sprite2D, offset
(0, -40). Never flipped.
  f0  the keg bursts: its staves splaying out of its own silhouette round a white crack of impact, the
      hoops sprung wide, a first puff of black powder
  f1  staves flying, the two iron hoops popping off, the powder cloud rolling
  f2  pieces at the top of their flight, the cloud spreading
  f3  pieces tumbling down, the cloud thinning
  f4  pieces coming down, the first ones landing, a last puff
  f5  every plank, hoop and splinter lying on the floor round the spot (hold it, or fade it out)
The keg's own colours (walnut, warm browns, iron) and Burak's iron greys for the powder. No keyline, opaque.
Drawn natively: the first draft's measures (64x48) times S = 2.0. Each piece is defined by where and when it
lands (x, floor depth, time), so the rest pose in f5 is exact and every piece is down by t = 0.24 s; they
scatter over the floor at different depths rather than along one line. Planks 2*S texels thick lit from the
top left with a dark rim on their shadow edge; hoops 2-texel rings (3 from S = 1.75).
"""
import math
import random

import bfx_pal as pal

S = 2.0
W, H = int(64 * S + 0.5), int(48 * S + 0.5)
PX, PY = 32.0 * S, 44.0 * S
FRAME_SIZE = (W, H)
NOTE = ('6 frames of %dx%d at 0.05 s; pivot (%d,%d) on the keg\'s floor point, offset (0,%d); '
        'f5 = debris at rest' % (W, H, PX, PY, H // 2 - PY))
TIMES = [0.0, 0.05, 0.10, 0.15, 0.20, 0.25]
G = 3400.0                  # gravity, first-draft texels / s^2 (x S on screen)
GROUND = PY - 1.0           # the row a piece at floor depth 0 rests on (the keg's own bottom row)
THICK = 2.0 * S

# Staves: (land x, land depth, land time, rest angle, spin turns, length, colour pair), first-draft units.
# Depth is the floor offset in screen y: negative lands further away (higher on screen), positive nearer.
STAVES = [(-24, -3, 0.24, 8, 1.25, 7, 'fD'), (-16, 2, 0.22, -6, 1.0, 8, 'EF'), (-3, -7, 0.24, 4, 1.5, 7, 'fD'),
          (12, -5, 0.23, -22, -1.25, 8, 'Ff'), (23, 1, 0.20, 5, -1.0, 7, 'fD'), (-26, 3, 0.17, -4, 0.75, 6, 'FD'),
          (26, -2, 0.18, 0, -0.75, 6, 'EF'), (-8, 3, 0.19, 26, 1.0, 5, 'fD'), (-19, -7, 0.21, -12, 1.25, 6, 'Ff'),
          (17, 3, 0.16, 10, -1.0, 6, 'EF')]
# Hoops: (launch x, launch height, land x, land depth, land time, radius, tumble phase)
HOOPS = [(-2, 18, -14, -4, 0.22, 5.0, 0.4), (2, 5, 15, 2, 0.19, 4.5, 1.3)]


def flight(x0, h0, x_land, d_land, t_land, t):
    """(x, depth - height) in first-draft units relative to the floor point, and whether it has landed."""
    if t >= t_land:
        return x_land, d_land, True
    u = t / t_land
    vy = (0.5 * G * t_land * t_land - h0) / t_land
    h = h0 + vy * t - 0.5 * G * t * t
    return x0 + (x_land - x0) * u, d_land * u - h, False


def plank(g, cx, cy, length, angle_deg, keys):
    """A stave piece as a filled rotated strip: its lit face keys[0] toward the top-left light, keys[1] on
    its shadow third, and a 1-texel dark rim along the shadow edge (only over empty texels)."""
    a = math.radians(angle_deg)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    lit = 1.0 if (-nx - ny) > 0 else -1.0
    reach = length / 2.0 + THICK + 1
    for y in range(int(cy - reach) - 1, int(cy + reach) + 2):
        for x in range(int(cx - reach) - 1, int(cx + reach) + 2):
            if not (0 <= x < W and 0 <= y < H):
                continue
            px, py = x + 0.5 - cx, y + 0.5 - cy
            u = px * dx + py * dy
            v = (px * nx + py * ny) * lit
            if abs(u) > length / 2.0:
                continue
            if -THICK / 2.0 <= v <= THICK / 2.0:
                g[y][x] = keys[0] if v > -THICK / 6.0 else keys[1]
            elif -THICK / 2.0 - 1.0 <= v < -THICK / 2.0 and g[y][x] == '.':
                g[y][x] = 'O'


def hoop(g, cx, cy, r, squash):
    """An iron hoop seen at a tilt: a 2-texel ring, lit on its upper left."""
    for i in range(128):
        a = 2 * math.pi * i / 128
        for rr in ((r, r - 0.9, r - 1.8) if S >= 1.75 else (r, r - 0.9)):
            x = int(round(cx + math.cos(a) * rr))
            y = int(round(cy + math.sin(a) * rr * squash))
            if 0 <= x < W and 0 <= y < H:
                g[y][x] = 'i' if (math.sin(a) < 0 and math.cos(a) < 0.3 and rr == r) else 'k'


def puff(g, cx, cy, r, dark):
    ramp = ['w', 'c', 's', 'i', 'I', 'k', 'K']
    for y in range(max(0, int(cy - r) - 1), min(H, int(cy + r) + 2)):
        for x in range(max(0, int(cx - r) - 1), min(W, int(cx + r) + 2)):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            if d > r:
                continue
            hl = math.hypot(dx + 0.3 * r, dy + 0.35 * r)
            i = dark - 1 if hl < 0.55 * r else (dark + 1 if (d > r - 1.3 and dx + dy > 0) else dark)
            if g[y][x] == '.':
                g[y][x] = ramp[max(0, min(len(ramp) - 1, i))]


CLOUDS = {0: [], 1: [(0, -9, 5, 4), (-6, -6, 4, 4), (6, -7, 4, 4)],
          2: [(0, -12, 6, 3), (-9, -8, 5, 3), (9, -9, 5, 3)], 3: [(-1, -15, 5, 2), (-11, -11, 4, 2), (10, -12, 4, 2)],
          4: [(5, -16, 3, 2)], 5: []}


def splinters():
    rnd = random.Random(3)
    out = []
    for i in range(16):
        x_land = rnd.uniform(-28, 28)
        out.append((x_land * 0.15, rnd.uniform(7, 13), x_land, rnd.uniform(-8, 3), rnd.uniform(0.10, 0.24),
                    'E' if i % 2 else 'n', i % 3 == 0))
    return out


def frame(f):
    g = pal.blank(W, H)
    t = TIMES[f]
    for (ox, oy, r, dark) in CLOUDS[f]:
        puff(g, PX + ox * S, PY + oy * S, r * S, dark)
    if f == 0:
        puff(g, PX, PY - 11 * S, 3.5 * S, 4)
        for i, ang in enumerate((-165, -140, -115, -90, -65, -40, -15)):
            a = math.radians(ang)
            plank(g, PX + math.cos(a) * 7 * S, PY - 11 * S + math.sin(a) * 6 * S, 10 * S, ang,
                  'fD' if i % 2 else 'EF')
        cx, cy = int(PX), int(PY - 12 * S)
        arm = int(1.34 * S + 0.5)                      # the white crack of impact: a small star
        for y in range(-arm, arm + 1):
            for x in range(-arm, arm + 1):
                if (abs(x) + abs(y) <= 0.8 * S or abs(x) == abs(y)) and 0 <= cx + x < W and 0 <= cy + y < H:
                    g[cy + y][cx + x] = 'W'
        hoop(g, PX, PY - 18 * S, 11 * S, 0.38)
        hoop(g, PX, PY - 4 * S, 11 * S, 0.38)
        return pal.rows(g)
    # pieces: those at rest first (they lie under anything still falling), then the flying ones
    pieces = []
    for (x_land, d_land, t_land, rest, spin, length, keys) in STAVES:
        x, yr, down = flight(x_land * 0.18, 11.0, x_land, d_land, t_land, t)
        ang = rest if down else rest + spin * 360.0 * (1.0 - t / t_land)
        pieces.append((0 if down else 1, 'plank', x, yr, ang, length, keys))
    for (x0, h0, x_land, d_land, t_land, r, ph) in HOOPS:
        x, yr, down = flight(x0, h0, x_land, d_land, t_land, t)
        sq = 0.35 if down else 0.35 + 0.55 * abs(math.sin(ph + t * 22.0))
        pieces.append((0 if down else 1, 'hoop', x, yr, sq, r, None))
    pieces.sort(key=lambda p: p[0])
    for (_, kind, x, yr, a, size, keys) in pieces:
        if kind == 'plank':
            plank(g, PX + x * S, GROUND + yr * S - THICK / 2.0, size * S, a, keys)
        else:
            hoop(g, PX + x * S, GROUND + yr * S, size * S, a)
    for (x0, h0, x_land, d_land, t_land, k, wide) in splinters():
        x, yr, down = flight(x0, h0, x_land, d_land, t_land, t)
        xx, yy = int(PX + x * S), int(GROUND + yr * S)
        n = int(0.75 * S + 0.5) + (1 if wide else 0)     # a splinter a texel or two long
        for i in range(n):
            if 0 <= xx + i < W and 0 <= yy < H:
                g[yy][xx + i] = k if i == 0 else 'n'
    return pal.rows(g)


def frames():
    return [frame(f) for f in range(6)]
