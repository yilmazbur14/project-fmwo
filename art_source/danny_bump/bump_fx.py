"""Danny's new effects for the approval pass (the user's picks of 2026-09-29), drawn in his approved FX style, to
the architect's contract (scratchpad/danny_addendum1.md, D.1).

The approved FX rig (art_source/danny_fx/) is IMPORTED READ-ONLY for its palette, worms, slime, dust and cracks
(dfx_pal, dfx_worms, dfx_floor); its export is never run. Like his approved FX these draw NO keyline (the darkest
tone of each ramp does the edge work), no dither, opaque except the dust's stepped alpha (168, 96).

  danny_worm_splash       hops 1-4: the landing throws his worms out round him. 6 frames of 192x112 at 0.05 s, never
                          rotated or flipped. PIVOT (96, 78) = the landing contact. Twelve worm globs fly out on arcs
                          and splat ON the splash zone's edge, the ellipse rx 77 x ry 28 texels (230 x 83 px) round
                          the pivot, so the worms land where the root reaches; four more land inside it. f5 is the
                          splats soaking in (then free it). The landing puddle is the approved splat -> puddle, drawn
                          by the code as now: this sheet draws no puddle of its own.
  danny_rope_impact       the player driven into a side rope by the belly bump. 6 frames of 64x112. Drawn for the
                          RIGHT rope (flip_h for the left). PIVOT (34, 56) = the rope's INNER line (its ring-side edge)
                          at the contact. The rope is drawn in the arena rope's own black / white, and where it bows
                          off its rest line the FX paints that rest band black (what the arena has under its rope),
                          so it COVERS the static rope over the bowed patch: x [pivot, pivot + 7) texels, y pivot +- 40.
  danny_big_slam_impact   the fifth slam, unparried: 7 frames of 288x128. PIVOT (144, 84) = the rear contact. A flash
                          the size of the footprint (132 x 22 texels), a pillar of light, a white shock ring racing
                          out along the mat (the floor's 0.36 flattening, like the quake ring it heralds), twice the
                          dust of danny_slam_impact, gold sparks, a crater of cracks; f6 = the cracks alone (hold, fade).
"""
import math
import os
import random
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
FXRIG = os.path.join(os.path.dirname(HERE), 'danny_fx')
if FXRIG not in sys.path:
    sys.path.insert(0, FXRIG)

import dfx_pal as pal  # noqa: E402
import dfx_worms as wm  # noqa: E402
import dfx_floor as fl  # noqa: E402

PAL = pal.PAL


def _disc(W, H, cx, cy, rx, ry=None):
    ry = rx if ry is None else ry
    out = set()
    for y in range(int(cy - ry) - 1, int(cy + ry) + 2):
        for x in range(int(cx - rx) - 1, int(cx + rx) + 2):
            if ((x + 0.5 - cx) / rx) ** 2 + ((y + 0.5 - cy) / ry) ** 2 <= 1.0 and 0 <= x < W and 0 <= y < H:
                out.add((x, y))
    return out


# ================================================================== WORM SPLASH (hops 1-4)
SW, SH = 192, 112
SPX, SPY = 96.0, 78.0
ZRX, ZRY = 77.0, 28.0                          # the splash zone (230 x 83 px): the root's reach
FLAT = ZRY / ZRX


def zone_pt(az, frac=1.0):
    """A point on the floor at `frac` of the zone's radius, azimuth `az` degrees (0 right, 90 toward the viewer)."""
    a = math.radians(az)
    return SPX + ZRX * frac * math.cos(a), SPY + ZRY * frac * math.sin(a)


# globs: (azimuth, landing radius as a fraction of the zone, peak height texels, glob radius, seed). The twelve
# outer ones land ON the zone's edge (frac 1.0); four fill it.
GLOBS = [(az, 1.0, 26 + (i * 7) % 16, 4.4 + (i % 3) * 0.5, i) for i, az in
         enumerate((-86, -54, -22, 8, 36, 64, 96, 124, 152, 182, 212, 244))] + \
        [(az, 0.55, 30 + i * 4, 3.8, 20 + i) for i, az in enumerate((-40, 40, 140, 220))]
FLUNG = [(-70, 0.9, 38, 8.0, 31), (20, 0.95, 30, 8.5, 32), (80, 0.9, 22, 8.0, 33), (140, 0.95, 30, 8.5, 34),
         (200, 0.9, 36, 8.0, 35), (260, 0.85, 42, 7.0, 36)]
DROPLETS = [((i * 47) % 360, 0.35 + ((i * 29) % 60) / 100.0, 14 + (i * 11) % 30, i) for i in range(16)]
SPLASH_T = [0.14, 0.40, 0.66, 0.88, 1.0, 1.0]
SPLASH_MS = [50, 50, 50, 50, 50, 50]


def flight(az, frac, peak, t):
    fx, fy = zone_pt(az, frac * t)
    return fx, fy - peak * 4.0 * t * (1.0 - t)


def glob(g, cx, cy, r, seed, spin):
    """A worm glob in flight (dfx_glob's ball at splash size): slime lit on its upper left, a worm wrapped round
    it and a worm end wriggling out."""
    W, H = len(g[0]), len(g)
    ball = _disc(W, H, cx, cy, r)
    for (x, y) in ball:
        dx, dy = x + 0.5 - cx, y + 0.5 - cy
        d = math.hypot(dx, dy)
        lit = (-dx - dy) / (d + 1e-6)
        g[y][x] = ('D' if lit > 0.2 else 'x') if d > r - 1.1 else '6'
    rnd = random.Random(seed)
    a0 = rnd.uniform(0, 360) + spin
    pts = [(cx + r * 0.62 * math.cos(math.radians(a0 + 200 * i / 12.0)),
            cy + r * 0.62 * 0.85 * math.sin(math.radians(a0 + 200 * i / 12.0))) for i in range(13)]
    wm.worm(g, pts, width=2.0, clip=ball, saddle=0.45, glint_every=0)
    a = math.radians(a0 + 240)
    wm.worm(g, wm.wiggle(cx + (r - 0.8) * math.cos(a), cy + (r - 0.8) * math.sin(a), cx + (r + 3.4) * math.cos(a),
                         cy + (r + 3.4) * math.sin(a), 0.8, 0.8, spin * 0.05 + seed, n=10),
            width=1.9, saddle=-1, glint_every=0)
    gx, gy = int(cx - r * 0.45), int(cy - r * 0.45)
    if 0 <= gy < H and 0 <= gx < W and g[gy][gx] == '6':
        g[gy][gx] = '1'


def flung_worm(g, cx, cy, length, seed, spin):
    a = math.radians(seed * 47 + spin)
    wm.worm(g, wm.wiggle(cx - math.cos(a) * length / 2, cy - math.sin(a) * length / 2, cx + math.cos(a) * length / 2,
                         cy + math.sin(a) * length / 2, 1.1, 1.0, seed + spin * 0.1, n=14),
            width=2.2, saddle=0.4, glint_every=0)


def splat(g, cx, cy, size, seed, worm=True):
    """A glob burst flat on the mat: a slime stain with its wet rim and a worm writhing in it."""
    W, H = len(g[0]), len(g)
    m = _disc(W, H, cx, cy, 7.4 * size, 3.2 * size)
    rnd = random.Random(seed)
    for _ in range(4):
        a = rnd.uniform(0, 2 * math.pi)
        m |= _disc(W, H, cx + math.cos(a) * 9 * size, cy + math.sin(a) * 3.6 * size, 1.6 * size, 1.1 * size)
    if not m:
        return
    wm.stain(g, m)
    wm.gloss(g, [(int(cx - 4 * size), int(cy - 1.6 * size)), (int(cx - 3 * size), int(cy - 2 * size))])
    if worm:
        wm.worm(g, wm.wiggle(cx - 5.5 * size, cy + 0.4, cx + 5.5 * size, cy - 0.8, 1.0, 1.1, seed, n=14),
                width=2.4 * max(0.8, size), clip=m | _disc(W, H, cx, cy - 1.5, 6.5 * size, 3.4), saddle=0.5,
                glint_every=0)


def splash_frame(f):
    g = pal.blank(SW, SH)
    t = SPLASH_T[f]
    if f >= 4:
        size = 1.0 if f == 4 else 0.62
        for (az, frac, peak, r, seed) in sorted(GLOBS, key=lambda gl: zone_pt(gl[0], gl[1])[1]):
            x, y = zone_pt(az, frac)
            splat(g, x, y, size * (1.0 if frac == 1.0 else 0.8), seed, worm=True)
        for (az, frac, peak, length, seed) in FLUNG:
            x, y = zone_pt(az, frac)
            if f == 4:
                wm.worm(g, wm.wiggle(x - 4, y, x + 4, y - 0.5, 0.9, 1.1, seed, n=12), width=2.2, saddle=0.4,
                        glint_every=0)
        return pal.rows(g)
    if f == 0:
        # the squirt out of the contact: slime spattered flat and a crown of drops thrown up
        rnd = random.Random(3)
        for i in range(12):
            a = math.radians(360.0 * i / 12 + rnd.uniform(-8, 8))
            m = _disc(SW, SH, SPX + math.cos(a) * 16, SPY + math.sin(a) * 6 - rnd.uniform(1, 7), 1.8, 2.4)
            if m:
                wm.stain(g, m)
    # drops, then flung worms, then the globs (back to front by their landing y, so the front ones overlap)
    for (az, frac, peak, seed) in DROPLETS:
        x, y = flight(az, frac, peak, min(1.0, t * 1.1))
        for (xx, yy) in _disc(SW, SH, x, y, 1.3, 1.6):
            if g[yy][xx] == '.':
                g[yy][xx] = 'x' if (xx + yy + seed) % 3 else 'D'
    for (az, frac, peak, length, seed) in FLUNG:
        x, y = flight(az, frac, peak, t)
        flung_worm(g, x, y, length, seed, f * 55)
    for (az, frac, peak, r, seed) in sorted(GLOBS, key=lambda gl: zone_pt(gl[0], gl[1])[1]):
        x, y = flight(az, frac, peak, t)
        glob(g, x, y, r * (0.75 + 0.25 * min(1.0, t * 3)), seed, f * 70)
    return pal.rows(g)


def splash_frames():
    return [splash_frame(f) for f in range(len(SPLASH_T))]


# ================================================================== ROPE IMPACT (the belly bump's ring-out)
RW, RH = 64, 112
RPX, RPY = 34.0, 56.0                          # the rope's inner (ring-side) line at the contact
ROPE_T = 7.0                                   # the arena rope is 20.8 px thick: 7 texels at 3x (black 2, white 3, black 2)
SPAN = 40.0                                    # half the length of rope that bows
ROPE = [dict(bow=7.0, burst=0), dict(bow=16.0, burst=1), dict(bow=-6.0, burst=2), dict(bow=3.0, burst=3),
        dict(bow=-1.0, burst=4), dict(bow=0.0, burst=5)]
ROPE_MS = [50, 150, 100, 70, 70, 60]
# the arena rope's own colours as frame-local keys, so the dust's alpha step never touches them: '#' its pure black
# (the FX palette has none: FX draw no keyline), '@' its white core, '%' the core's shaded edge (his pale blue P)
ROPE_KEYS = {'#': (0, 0, 0, 255), '@': (255, 255, 255, 255), '%': PAL['P']}


def bow_at(v, bow):
    """How far the rope is pushed out of the ring at v texels along it from the contact: a rope loaded at a point
    bows into a V with a rounded tip (the player's back)."""
    u = abs(v) / SPAN
    if u >= 1.0:
        return 0.0
    tip = 0.35
    prof = 1.0 - (u * u) / (2 * tip) if u < tip else (1.0 - u) / (1.0 - tip) * (1.0 - tip / 2)
    return bow * prof


def rope_frame(f):
    """The RIGHT rope, vertical on screen: the ring is to the LEFT (x < RPX); out of the ring is +x."""
    st = ROPE[f]
    g = pal.blank(RW, RH)
    local = {}
    bow = st['bow']
    rope = {}
    for y in range(RH):
        x0 = RPX + bow_at(y + 0.5 - RPY, bow)
        for x in range(RW):
            d = x + 0.5 - x0                   # 0 .. ROPE_T across the rope, from its inner line
            if 0.0 <= d < ROPE_T:
                rope[(x, y)] = '@' if 2.0 <= d < 5.0 else '#'
    # the slot the rope leaves: its rest band is painted with what the arena has under it (black)
    if bow:
        for y in range(RH):
            if abs(y + 0.5 - RPY) >= SPAN:
                continue
            for x in range(int(RPX), int(RPX + ROPE_T)):
                if (x, y) not in rope:
                    g[y][x] = '#'
    for (x, y), k in rope.items():
        g[y][x] = k
    if bow:
        for y in range(RH):
            core = [x for x in range(RW) if rope.get((x, y)) == '@']
            if core and abs(y + 0.5 - RPY) < SPAN:
                g[y][max(core)] = '%'                     # the core's far edge turned from the light
    b = st['burst']
    cx = RPX + bow_at(0.0, bow) - 2.0                     # the burst sits on the ring side of the rope's inner line
    cy = RPY
    rnd = random.Random(21)
    if b == 0:
        for (x, y) in _disc(RW, RH, cx, cy, 6.0, 9.0):
            g[y][x] = 'W' if math.hypot((x + 0.5 - cx) / 6, (y + 0.5 - cy) / 9) < 0.6 else 'Q'
    if b in (0, 1, 2):
        n = (8, 10, 10)[b]
        r0, r1 = ((5, 9), (8, 18), (13, 22))[b]
        keys = ('W', 'Y', 'G', 'O') if b < 2 else ('Q', 'P', 'L', 'L')
        for i in range(n):
            a = math.radians(180 - 80 + 160 * i / (n - 1) + rnd.uniform(-6, 6))
            p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 1.4)
            p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 1.4)
            ray = fl.line_texels([p0, p1])
            for j, (x, y) in enumerate(ray):
                if 0 <= x < RW and 0 <= y < RH and g[y][x] == '.':
                    g[y][x] = keys[min(3, j * 4 // max(1, len(ray)))]
    if b == 1:
        for (x, y) in _disc(RW, RH, cx + 1, cy, 4.0, 7.0):
            if g[y][x] in '.PLQ@%#':
                g[y][x] = 'W'
    if b >= 1:
        # dust knocked off the rope, drifting back into the ring and thinning
        for (dx, dy, r) in ((-6, -14, 3.2), (-9, 12, 3.6), (-4, -24, 2.6), (-7, 24, 2.8)):
            grow = 1.0 + 0.25 * (b - 1)
            fl.puff(g, cx + dx - 2 * (b - 1), cy + dy * (0.9 + 0.1 * b), r * grow, shade=min(3, b - 1), squash=1.0)
        if b >= 3:
            local = fl.dust_alpha(g, 168 if b == 3 else 96)
    if b in (0, 1):
        # speed lines along the shove, in the ring
        for (dy, L) in ((-8, 12), (0, 16), (8, 12)):
            y = int(cy + dy)
            for x in range(int(cx - 10 - L), int(cx - 10)):
                if 0 <= x < RW and 0 <= y < RH and g[y][x] == '.' and (x + y) % 5 != 0:
                    g[y][x] = 'Q' if x > cx - 10 - L * 0.5 else 'P'
    return pal.Frame(pal.rows(g), dict(local, **ROPE_KEYS))


def rope_frames():
    return [rope_frame(f) for f in range(len(ROPE))]


# ================================================================== THE BIG SLAM (the fifth, unparried)
BW, BH = 288, 128
BPX, BPY = 144.0, 84.0
FOOT_RX, FOOT_RY = 66.0, 11.0                  # the slam's footprint and shadow: 132 x 22 texels
RING_FLAT = 0.36                               # the floor's flattening (the quake ring's)
DUST_FLAT = 0.26
BIG_MS = [50, 50, 50, 60, 70, 80, 120]


def big_cracks(g, grow):
    rnd = random.Random(33)
    for n in range(18):
        a = math.radians(360.0 * n / 18 + rnd.uniform(-8, 8))
        L = rnd.uniform(40, 64) * grow
        x1, y1 = BPX + math.cos(a) * L, BPY + math.sin(a) * L * RING_FLAT
        pts = fl.zigzag(BPX + math.cos(a) * 4, BPY + math.sin(a) * 1.4, x1, y1, seed=n + 70, jag=1.4)
        fl.crack(g, pts)
        fl.crack(g, pts[:max(2, len(pts) * 2 // 5)], wide=True)
        if grow > 0.6 and n % 3 == 0:
            m = pts[len(pts) // 2]
            b = a + rnd.choice((-0.55, 0.55))
            fl.crack(g, fl.zigzag(m[0], m[1], m[0] + math.cos(b) * L * 0.35, m[1] + math.sin(b) * L * 0.35 * RING_FLAT,
                                  seed=n + 140, jag=1.0), lip=False)


def crater(g):
    """The mat punched down under him over his footprint: the dent's shade m, its lit far rim n."""
    for y in range(BH):
        for x in range(BW):
            d = math.hypot((x + 0.5 - BPX) / (FOOT_RX * 0.62), (y + 0.5 - BPY) / (FOOT_RY * 0.62))
            if d <= 1.0 and g[y][x] == '.':
                g[y][x] = 'm' if (y + 0.5 - BPY) > -FOOT_RY * 0.3 else 'n'
            elif 1.0 < d <= 1.14 and g[y][x] == '.' and (y + 0.5 - BPY) < 0:
                g[y][x] = 'n'


def shock_ring(g, rx, keys, thick=2.2):
    ry = rx * RING_FLAT
    for y in range(BH):
        for x in range(BW):
            d = math.hypot((x + 0.5 - BPX) / rx, (y + 0.5 - BPY) / ry)
            if abs(d - 1.0) <= thick / rx and g[y][x] in '.nmkK':
                g[y][x] = keys[0] if (y + 0.5 - BPY) > 0 else keys[1]


def pillar(g, h, w, keys='WQP'):
    """A column of light punched up out of the impact: a white core, pale edges, tapering as it rises."""
    for y in range(int(BPY - h), int(BPY) + 1):
        t = (BPY - y) / max(1.0, h)
        half = w * (1.0 - 0.55 * t)
        for x in range(int(BPX - half) - 1, int(BPX + half) + 2):
            d = abs(x + 0.5 - BPX) / max(0.5, half)
            if d <= 1.0 and 0 <= y < BH and 0 <= x < BW:
                g[y][x] = keys[0] if d < 0.45 else (keys[1] if d < 0.8 else keys[2])


def starburst(g, r_in, r_out, n, keys='WQP', seed=7):
    """The impact's burst of light: spikes flung up and out of the contact (the floor cuts off the lower half),
    each a sliver tapering from its root to its tip, a white heart and pale edges, their lengths staggered."""
    rnd = random.Random(seed)
    for i in range(n):
        a = math.radians(-180 + 180 * (i + 0.5) / n + rnd.uniform(-5, 5))
        L = r_out * (0.62 + 0.38 * ((i * 7) % 5) / 4.0)
        w = 4.2 if i % 2 == 0 else 3.0
        ux, uy = math.cos(a), math.sin(a)
        nx, ny = -uy, ux
        for step in range(int(r_in), int(L) + 1):
            t = (step - r_in) / max(1.0, L - r_in)
            half = w * (1.0 - t)
            for k in range(-int(half) - 1, int(half) + 2):
                if abs(k) > half:
                    continue
                x = int(BPX + ux * step + nx * k)
                y = int(BPY - 2 + uy * step * 0.9 + ny * k)
                if 0 <= x < BW and 0 <= y < BH:
                    g[y][x] = keys[0] if abs(k) < half * 0.45 else (keys[1] if abs(k) < half * 0.8 else keys[2])
    for y in range(BH):
        for x in range(BW):
            d = math.hypot((x + 0.5 - BPX) / (r_in + 6), (y + 0.5 - BPY + 4) / (r_in + 2))
            if d <= 1.0:
                g[y][x] = keys[0] if d < 0.7 else keys[1]


def flash(g, rx, ry):
    for y in range(BH):
        for x in range(BW):
            d = math.hypot((x + 0.5 - BPX) / rx, (y + 0.5 - BPY) / ry)
            if d <= 1.0:
                g[y][x] = 'W' if d < 0.5 else ('Q' if d < 0.78 else 'P')


def sparks(g, t, n=16, seed=5):
    """Gold sparks flying out and up (his chain's golds): short streaks along their flight."""
    rnd = random.Random(seed)
    for i in range(n):
        a = math.radians(rnd.uniform(-172, -8))
        v = rnd.uniform(120, 220)
        x = BPX + math.cos(a) * v * t * 1.6
        y = BPY - 4 + math.sin(a) * v * t + 0.5 * 520 * t * t
        dx, dy = math.cos(a) * 1.6, math.sin(a) + 520 * t / v
        for j in range(4):
            xx, yy = int(x - dx * j), int(y - dy * j)
            if 0 <= xx < BW and 0 <= yy < BH and yy <= BPY + 6:
                g[yy][xx] = ('y', 'Y', 'G', 'O')[j]


def big_dust(g, rx, rise, shade, rmin, rmax, count=30, seed=4):
    rnd = random.Random(seed)
    puffs = []
    for i in range(count):
        a = 2 * math.pi * i / count + rnd.uniform(-0.08, 0.08)
        front = 0.5 + 0.5 * math.sin(a)
        r = rnd.uniform(rmin, rmax) * (0.8 + 0.4 * front)
        x = BPX + math.cos(a) * rx * rnd.uniform(0.94, 1.05)
        y = BPY + math.sin(a) * rx * DUST_FLAT - rise * rnd.uniform(0.5, 1.0) - r * 0.3
        puffs.append((y, x, r))
    for (y, x, r) in sorted(puffs):
        fl.puff(g, x, y, r, shade, squash=0.72)


def big_chips(g, t):
    rnd = random.Random(19)
    for i in range(22):
        a = math.radians(rnd.uniform(-168, -12))
        v = rnd.uniform(110, 210)
        x = BPX + math.cos(a) * v * t * 1.8
        y = min(BPY + 4, BPY - 8 + math.sin(a) * v * t + 0.5 * 640 * t * t)
        fl.chip(g, x, y, big=(i % 3 != 0))


def big_frame(f):
    g = pal.blank(BW, BH)
    local = {}
    if f == 0:
        big_cracks(g, 0.5)
        flash(g, FOOT_RX, FOOT_RY)
        starburst(g, 16, 64, 11)
        for (dx, r) in ((-44, 9), (42, 9), (-20, 11), (21, 10)):
            fl.puff(g, BPX + dx, BPY - 4, r, 0, squash=0.72)
    elif f == 1:
        crater(g)
        big_cracks(g, 0.85)
        shock_ring(g, 70, 'WQ', 2.6)
        big_dust(g, 60, 7, 0, 7.0, 10.0)
        starburst(g, 10, 44, 11, keys='QPL')
        fl.puff(g, BPX, BPY - 10, 15, 0, squash=0.8)
        big_chips(g, 0.05)
        sparks(g, 0.06)
    elif f == 2:
        crater(g)
        big_cracks(g, 1.0)
        shock_ring(g, 100, 'QP', 2.2)
        big_dust(g, 82, 12, 0, 8.0, 12.0)
        fl.puff(g, BPX - 9, BPY - 20, 13, 1, squash=0.8)
        fl.puff(g, BPX + 10, BPY - 17, 12, 1, squash=0.8)
        big_chips(g, 0.11)
        sparks(g, 0.12)
    elif f == 3:
        crater(g)
        big_cracks(g, 1.0)
        shock_ring(g, 116, 'PL', 1.8)
        big_dust(g, 100, 16, 1, 8.5, 12.5)
        fl.puff(g, BPX, BPY - 30, 13, 1, squash=0.8)
        big_chips(g, 0.17)
        sparks(g, 0.19)
    elif f == 4:
        crater(g)
        big_cracks(g, 1.0)
        big_dust(g, 112, 19, 1, 9.0, 12.5, count=26)
        big_chips(g, 0.24)
        sparks(g, 0.26, n=8)
        local = fl.dust_alpha(g, 168)
    elif f == 5:
        crater(g)
        big_cracks(g, 1.0)
        big_dust(g, 120, 21, 2, 9.0, 12.0, count=20)
        big_chips(g, 0.30)
        local = fl.dust_alpha(g, 96)
    else:
        crater(g)
        big_cracks(g, 1.0)
    return pal.Frame(pal.rows(g), local)


def big_frames():
    return [big_frame(f) for f in range(len(BIG_MS))]


# ================================================================== THE SHEETS
FX_SHEETS = {
    'danny_worm_splash': dict(frames=splash_frames, size=(SW, SH), pivot=(int(SPX), int(SPY)), ms=SPLASH_MS,
                              note='6 frames at 0.05 s, never rotated or flipped; pivot = the landing contact; the '
                                   'twelve outer globs splat ON the zone edge rx 77 x ry 28 texels; draw on the '
                                   'FloorLayer under him; free after f5'),
    'danny_rope_impact': dict(frames=rope_frames, size=(RW, RH), pivot=(int(RPX), int(RPY)), ms=ROPE_MS,
                              note='6 frames: contact, peak (held through the pin), spring back, settle x2, rest; '
                                   'drawn for the RIGHT rope (flip_h for the left); pivot = the rope\'s inner line at '
                                   'the contact; covers the static rope over x [pivot, pivot+7) texels, y pivot+-40'),
    'danny_big_slam_impact': dict(frames=big_frames, size=(BW, BH), pivot=(int(BPX), int(BPY)), ms=BIG_MS,
                                  note='7 frames; pivot = the rear contact; f0 flash = the 132 x 22 footprint; '
                                       'f6 = the cracks alone (hold, then fade, like slam_impact\'s cracks frame)'),
}
