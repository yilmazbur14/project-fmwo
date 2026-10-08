"""Greyson's doom orb: his hype meter made physical (scratchpad/greyson_readability/BRIEF.md, parts 2 and 3). A small
spirit bomb forms over his head at his first banked pose and grows a stage a bank; the crowd's energy streaks into
it; a hit bursts it. Drawn from the shipped spirit bomb's own sphere (art_source/greyson_fx/gfx_bomb.sphere), so
stage 6 is the bomb itself, with his violet lightning crackling round it. Sheets (all at scale 3, whole texels, no
keyline, no dither, stepped alpha only; never rotated):

  greyson_doom_orb        6 rows (stages 1-6) x 5 frames of 72x72: f0-f3 the stage's pulse loop, f4 its arrival
                          flash (shown once as the stage banks). PIVOT: the orb's FOOT, the bottom of its sphere,
                          (36, 56), the same on every stage: it grows upward off one point over his head.
                          Stage 6 f0 is pixel for pixel greyson_bomb f1's sphere without the muzzle's beam.
  greyson_doom_orb_glow   the same grid and pivot: an additive halo for each frame (blend mode add).
  greyson_doom_orb_burst  2 rows (small for stages 1-3, big for 4-5) x 6 frames of 96x96, once: the orb flashes,
                          cracks like glass and flies apart. PIVOT: the orb's centre, the frame centre (48, 48).
  greyson_hype_streak     16 rows (headings, 22.5 degrees apart, row 0 flying right, row 4 down, row 8 left,
                          row 12 up) x 4 frames of 40x40: a comet of crowd energy, its head on the frame centre
                          (20, 20), its tail behind it. The code picks the row from its velocity.
  greyson_hype_streak_cyan  the same in the crowd's cyan (the alternative pick).
  greyson_doom_vignette   1 frame of 640x360: his violet creeping in from the screen's edges, a screen layer.
"""
import math
import random

import gfx_pal as pal
import gfx_bomb as B

# ---------------------------------------------------------------------------------------------------- the orb
OW = 72
FOOT = (36, 56)                     # the pivot: the sphere's bottom point
RADII = [5, 7, 9, 11, 13, 19]       # stage 6 is greyson_bomb f1's radius
BOMB_HANDOFF_FRAME = 1              # greyson_bomb's frame stage 6 hands off to
HAZE_W = [4.0, 5.0, 6.0, 7.0, 8.5, None]   # the haze's width beyond the rim, texels (stage 6: the bomb's own)
BREATHE = [0.0, 0.6, 1.2, 0.6]      # the haze breathing through the loop, texels
ARCS = [1, 2, 2, 3, 4, 5]           # lightning arcs a frame
ARC_LEN = [4, 5, 7, 8, 10, 11]
FRAME_TIMES = [0.14, 0.13, 0.12, 0.11, 0.10, 0.09]   # the pulse quickens with the stakes
FLASH_TIME = 0.08
# the bomb's frame: its sphere's foot is 3 texels over its muzzle, at (216, 395) in its 432x432 frame
BOMB_FOOT = (int(B.MX), int(B.MY) - 3)
CROP = (BOMB_FOOT[0] - FOOT[0], BOMB_FOOT[1] - FOOT[1])

# his violet lightning: core V, glow U at alpha, sparks W
BOLT = {'j': pal.hx('D9A8FF'), 'k': pal.hx('592687', 224), 'l': pal.hx('A063DC', 176)}
ORB_LOCAL = dict(B.LOCAL)
ORB_LOCAL.update(BOLT)


def sphere_rows(R, seed, breathe, halo):
    g = pal.blank(B.BW, B.BH)
    B.sphere(g, R, seed, breathe=breathe, feed=False, halo=halo)
    return [row[CROP[0]:CROP[0] + OW] for row in g[CROP[1]:CROP[1] + OW]]


def centre(stage):
    R = RADII[stage]
    return (FOOT[0], FOOT[1] - R)


def bolt(g, stage, rnd):
    """One jagged arc of violet lightning leaving the rim and crawling out and round it."""
    R = RADII[stage]
    cx, cy = centre(stage)
    a = rnd.uniform(0, 2 * math.pi)
    x, y = cx + math.cos(a) * (R - 1.0), cy + math.sin(a) * (R - 1.0)
    turn = rnd.choice((-1, 1))
    pts = [(x, y)]
    L = ARC_LEN[stage] * rnd.uniform(0.7, 1.0)
    step = 1.6
    d = 0.0
    heading = a + turn * rnd.uniform(0.3, 0.7)
    while d < L:
        heading += turn * rnd.uniform(0.05, 0.35) + rnd.uniform(-0.5, 0.5)
        # keep it hugging the orb: pull the heading toward the tangent once it is well out
        r_now = math.hypot(x - cx, y - cy)
        if r_now > R + 0.45 * L:
            heading = math.atan2(y - cy, x - cx) + turn * 1.7
        x, y = x + math.cos(heading) * step, y + math.sin(heading) * step
        pts.append((x, y))
        d += step
    tex = []
    for i in range(len(pts) - 1):
        (ax, ay), (bx, by) = pts[i], pts[i + 1]
        n = int(max(abs(bx - ax), abs(by - ay))) + 1
        for j in range(n + 1):
            t = j / float(n)
            p = (int(ax + (bx - ax) * t), int(ay + (by - ay) * t))
            if not tex or tex[-1] != p:
                tex.append(p)
    H, W = len(g), len(g[0])
    core = set(tex)
    for (px, py) in tex:
        if 0 <= px < W and 0 <= py < H:
            g[py][px] = 'j'
    # a dark violet sheath round the core: on its outer side only on the small stages, both sides from stage 3
    for (px, py) in tex:
        for (ox, oy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            qx, qy = px + ox, py + oy
            if (qx, qy) in core or not (0 <= qx < W and 0 <= qy < H):
                continue
            outward = (qx - cx) * (px - cx) + (qy - cy) * (py - cy) > 0 and math.hypot(qx - cx, qy - cy) > math.hypot(px - cx, py - cy)
            if stage >= 2 or outward:
                g[qy][qx] = 'k'
    # a white spark at its tip, and a fork on the bigger stages
    tx, ty = tex[-1]
    if 0 <= tx < W and 0 <= ty < H:
        g[ty][tx] = 'W'
    if stage >= 3 and len(tex) > 6:
        fx, fy = tex[len(tex) // 2]
        fa = math.atan2(fy - cy, fx - cx) + turn * 0.4
        for s in range(1, 3 + stage // 2):
            px, py = int(fx + math.cos(fa) * s), int(fy + math.sin(fa) * s + (s % 2) * 0.6)
            if 0 <= px < W and 0 <= py < H:
                g[py][px] = 'j' if s < 2 + stage // 2 else 'l'


def orb_frame(stage, f):
    R = RADII[stage]
    halo = None if HAZE_W[stage] is None else HAZE_W[stage] / 36.0
    if stage == 5 and f == 0:
        # the hand-off frame: greyson_bomb f1's sphere, pixel for pixel, without the muzzle's beam
        return pal.Frame(sphere_rows(R, BOMB_HANDOFF_FRAME, 0.0, None), ORB_LOCAL)
    if f == 4:
        # the arrival flash: the whole body white-hot, the haze at its widest
        rows = sphere_rows(R, BOMB_HANDOFF_FRAME if stage == 5 else 7, max(BREATHE) + 0.6, halo)
        g = [list(r) for r in rows]
        cx, cy = centre(stage)
        for y in range(OW):
            for x in range(OW):
                if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= R and g[y][x] not in '.':
                    g[y][x] = 'W' if math.hypot(x + 0.5 - cx, y + 0.5 - cy) <= R - 1 else 'C'
        rnd = random.Random(100 + stage)
        for i in range(ARCS[stage] + 1):
            bolt(g, stage, rnd)
        return pal.Frame(pal.rows(g), ORB_LOCAL)
    seed = BOMB_HANDOFF_FRAME if stage == 5 else 7
    g = [list(r) for r in sphere_rows(R, seed, BREATHE[f] * (0.6 + 0.1 * stage), halo)]
    rnd = random.Random(stage * 10 + f)
    n = ARCS[stage]
    if stage == 0 and f % 2:
        n = 0                           # stage 1 only sparks on alternate frames
    for i in range(n):
        bolt(g, stage, rnd)
    return pal.Frame(pal.rows(g), ORB_LOCAL)


def orb_rows():
    return [[orb_frame(s, f) for f in range(5)] for s in range(6)]


# ---------------------------------------------------------------------------------------------------- the glow
GLOW_STEPS = [(0.45, (58, 74, 150), 150), (0.65, (52, 58, 132), 112), (0.82, (46, 40, 116), 76), (1.0, (40, 26, 96), 44)]
GLOW_SCALE = [2.4, 2.3, 2.2, 2.0, 1.9, 1.55]      # the glow's radius, in orb radii
GLOW_GAIN = [0.55, 0.65, 0.75, 0.85, 0.95, 1.0]


def glow_frame(stage, f):
    g = pal.blank(OW, OW)
    R = RADII[stage]
    cx, cy = centre(stage)
    gr = R * GLOW_SCALE[stage] * (1.0 + 0.04 * BREATHE[f % 4] + (0.12 if f == 4 else 0.0))
    local = {}
    keys = 'mnop'
    for i, (q, rgb, a) in enumerate(GLOW_STEPS):
        gain = GLOW_GAIN[stage] * (1.25 if f == 4 else 1.0)
        local[keys[i]] = (rgb[0], rgb[1], rgb[2], min(255, int(a * gain)))
    for y in range(OW):
        for x in range(OW):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / gr
            for i, (q, rgb, a) in enumerate(GLOW_STEPS):
                if d <= q:
                    g[y][x] = keys[i]
                    break
    return pal.Frame(pal.rows(g), local)


def glow_rows():
    return [[glow_frame(s, f) for f in range(5)] for s in range(6)]


# ---------------------------------------------------------------------------------------------------- the burst
BW_ = 96
BC = (48.0, 48.0)
BURST_R = [7.0, 12.0]               # the orb it is drawn for: small (stages 1-3), big (stages 4-5)
BURST_TIMES = [0.05, 0.06, 0.05, 0.06, 0.07, 0.08]
BURST_LOCAL = dict(ORB_LOCAL)
BURST_LOCAL.update({'q': pal.hx('C892F2', 200), 'r': pal.hx('A063DC', 128), 's': pal.hx('7C3BB4', 64),
                    't': pal.hx('E6F7FF', 176), 'u': pal.hx('B4DCFF', 112), 'z': pal.hx('5FE1FF', 72)})


def ring(g, cx, cy, r, key, width=1):
    n = int(2 * math.pi * r * 1.6) + 8
    for i in range(n):
        a = 2 * math.pi * i / n
        for w in range(width):
            x, y = int(cx + (r + w) * math.cos(a)), int(cy + (r + w) * math.sin(a))
            if 0 <= x < len(g[0]) and 0 <= y < len(g):
                g[y][x] = key


def shard(g, cx, cy, size, ang, spin, keys):
    """A glass shard: a thin triangle, bright on its leading edge."""
    pts = [(cx + math.cos(ang + spin) * size, cy + math.sin(ang + spin) * size),
           (cx + math.cos(ang + spin + 2.5) * size * 0.55, cy + math.sin(ang + spin + 2.5) * size * 0.55),
           (cx + math.cos(ang + spin - 2.4) * size * 0.45, cy + math.sin(ang + spin - 2.4) * size * 0.45)]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    for y in range(int(min(ys)) - 1, int(max(ys)) + 2):
        for x in range(int(min(xs)) - 1, int(max(xs)) + 2):
            px, py = x + 0.5, y + 0.5
            inside = True
            sgn = None
            for i in range(3):
                (ax, ay), (bx, by) = pts[i], pts[(i + 1) % 3]
                c = (bx - ax) * (py - ay) - (by - ay) * (px - ax)
                if sgn is None:
                    sgn = c >= 0
                elif (c >= 0) != sgn:
                    inside = False
                    break
            if inside and 0 <= x < len(g[0]) and 0 <= y < len(g):
                # lit on the side facing the burst's centre's upper left
                g[y][x] = keys[0] if (x - cx) + (y - cy) < 0 else keys[1]
    tx, ty = int(pts[0][0]), int(pts[0][1])
    if 0 <= tx < len(g[0]) and 0 <= ty < len(g):
        g[ty][tx] = 'W'


def burst_frame(size, f):
    """f0 the flash; f1 the orb cracks like glass; f2-f5 it flies apart in wedge-shaped shards (the orb's own
    shading, a white glint on each), a violet shock ring snapping out and fading, cyan sparks."""
    g = pal.blank(BW_, BW_)
    R = BURST_R[size]
    cx, cy = BC
    n = 7 if size == 0 else 9
    rnd = random.Random(31 + size)
    cuts = sorted(2 * math.pi * i / n + rnd.uniform(-0.25, 0.25) for i in range(n))
    kicks = [(rnd.uniform(0.8, 1.2), rnd.uniform(-0.3, 0.3)) for i in range(n)]
    bands = B.body_bands(R)
    H = W = BW_

    def wedge_of(x, y):
        a = math.atan2(y + 0.5 - cy, x + 0.5 - cx) % (2 * math.pi)
        r = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
        a = (a + 0.18 * math.sin(r * 1.1 + a * 3.0)) % (2 * math.pi)
        for i in range(n):
            a0, a1 = cuts[i], cuts[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0.0)
            aa = a if a >= cuts[0] else a + 2 * math.pi
            if a0 <= aa < a1:
                return i, min(aa - a0, a1 - aa) * r
        return 0, 9.0

    def band_key(r):
        for (lim, k) in bands:
            if r <= lim:
                return k
        return 'I'

    if f == 0:
        # the flash: the orb swells white, a violet shock ring snaps out round it
        for y in range(H):
            for x in range(W):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if d <= R * 1.2:
                    g[y][x] = 'W' if d <= R * 1.0 else 'C'
                elif d <= R * 1.2 + 2.0:
                    g[y][x] = 't'
        ring(g, cx, cy, R * 1.5, 'j', 2)
        return pal.Frame(pal.rows(g), BURST_LOCAL)
    # the shock ring racing out and fading, violet (f1-f3)
    if f <= 3:
        ring(g, cx, cy, R * (1.6 + 0.35 * f), ['j', 'q', 'r'][f - 1], 2 if f < 3 else 1)
    if f == 1:
        # cracked: the whole orb still, split along its cuts by dark violet cracks, the core blazing
        for y in range(H):
            for x in range(W):
                r = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
                if r <= R:
                    i, edge = wedge_of(x, y)
                    g[y][x] = 'k' if (edge < 0.7 and r > 1.5) else ('W' if r < R * 0.35 else band_key(r))
        return pal.Frame(pal.rows(g), BURST_LOCAL)
    # the shards: each wedge thrown out along its middle, falling, shrinking from its tip in to its point
    t = [0, 0, 0.06, 0.13, 0.21, 0.30][f]
    shrink = [1, 1, 1.0, 0.85, 0.68, 0.5][f]
    fade = f >= 5
    for y in range(H):
        for x in range(W):
            r = math.hypot(x + 0.5 - cx, y + 0.5 - cy)
            if r > R:
                continue
            i, edge = wedge_of(x, y)
            if edge < 0.9 or r > R * shrink + 0.5:
                continue
            a0, a1 = cuts[i], cuts[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0.0)
            mid = (a0 + a1) / 2.0 + kicks[i][1]
            v = R * 7.0 * kicks[i][0]
            ox = math.cos(mid) * v * t
            oy = math.sin(mid) * v * t + 90.0 * t * t
            nx, ny = int(x + ox), int(y + oy)
            if 0 <= nx < W and 0 <= ny < H:
                k = 'W' if r < R * 0.35 else band_key(r)
                if fade:
                    k = 't' if k in 'W123' else ('u' if k in '456789' else 'z')
                g[ny][nx] = k
    # a white glint on each shard's outer corner
    for i in range(n):
        a0, a1 = cuts[i], cuts[(i + 1) % n] + (2 * math.pi if i == n - 1 else 0.0)
        mid = (a0 + a1) / 2.0 + kicks[i][1]
        v = R * 7.0 * kicks[i][0]
        rr = R * shrink * 0.8
        gx = int(cx + math.cos((a0 + a1) / 2.0) * rr + math.cos(mid) * v * t)
        gy = int(cy + math.sin((a0 + a1) / 2.0) * rr + math.sin(mid) * v * t + 90.0 * t * t)
        if 0 <= gx < W and 0 <= gy < H and g[gy][gx] != '.' and not fade:
            g[gy][gx] = 'W'
    # sparks: cyan and violet motes flung out
    rnd2 = random.Random(70 + f + size * 10)
    for i in range(10 + 6 * size):
        a = rnd2.uniform(0, 2 * math.pi)
        d = R * (1.3 + 0.55 * f) * rnd2.uniform(0.6, 1.1)
        x, y = int(cx + math.cos(a) * d), int(cy + math.sin(a) * d + 40.0 * t * t)
        if 1 <= x < W - 1 and 1 <= y < H - 1 and g[y][x] == '.':
            g[y][x] = ('A' if i % 3 else 'j') if f < 5 else ('z' if i % 3 else 'r')
    return pal.Frame(pal.rows(g), BURST_LOCAL)


def burst_rows():
    return [[burst_frame(s, f) for f in range(6)] for s in range(2)]


# ---------------------------------------------------------------------------------------------------- the streak
SW_ = 40
SC = (20.0, 20.0)
HEADINGS = 16
TAIL = 17.0
STREAK_TIME = 0.05
STREAK_PALETTES = {
    'violet': {'head': 'W', 'ring': 'V', 'halo': pal.hx('C892F2', 96),
               'tail': [pal.hx('C892F2'), pal.hx('A063DC', 208), pal.hx('7C3BB4', 144), pal.hx('7C3BB4', 72)]},
    'cyan': {'head': 'W', 'ring': 'C', 'halo': pal.hx('5FE1FF', 96),
             'tail': [pal.hx('5FE1FF'), pal.hx('2FA8E0', 208), pal.hx('639BFF', 144), pal.hx('639BFF', 72)]},
}


def streak_frame(k, f, which='violet'):
    spec = STREAK_PALETTES[which]
    g = pal.blank(SW_, SW_)
    local = {'0': spec['halo'], '1': spec['tail'][0], '2': spec['tail'][1], '3': spec['tail'][2], '4': spec['tail'][3]}
    th = 2 * math.pi * k / HEADINGS
    dx, dy = math.cos(th), math.sin(th)
    nx, ny = -dy, dx
    cx, cy = SC
    rnd = random.Random(k * 7 + f)
    for y in range(SW_):
        for x in range(SW_):
            px, py = x + 0.5 - cx, y + 0.5 - cy
            along = -(px * dx + py * dy)            # distance back along the tail
            across = px * nx + py * ny
            d = math.hypot(px, py)
            if d <= 1.5:
                g[y][x] = spec['head']
                continue
            if d <= 2.6:
                g[y][x] = spec['ring']
                continue
            if 0.0 <= along <= TAIL:
                u = along / TAIL
                half = 2.0 * (1.0 - u) + 0.4
                wob = 0.45 * math.sin(along * 0.9 - f * 1.6)
                if abs(across - wob * u) <= half:
                    g[y][x] = '1' if u < 0.3 else ('2' if u < 0.55 else ('3' if u < 0.8 else '4'))
                    continue
            if d <= 3.7:
                g[y][x] = '0'
    # motes shed off the tail, drifting behind it
    for i in range(3):
        a = rnd.uniform(5.0, TAIL - 2.0)
        side = rnd.uniform(-2.8, 2.8)
        x, y = int(cx - dx * a + nx * side), int(cy - dy * a + ny * side)
        if 0 <= x < SW_ and 0 <= y < SW_ and g[y][x] == '.':
            g[y][x] = '2' if i else '1'
    return pal.Frame(pal.rows(g), local)


def streak_rows(which='violet'):
    return [[streak_frame(k, f, which) for f in range(4)] for k in range(HEADINGS)]


# ---------------------------------------------------------------------------------------------------- the vignette
VW, VH = 640, 360
VIG = [(0.80, pal.hx('592687', 24)), (0.84, pal.hx('592687', 44)), (0.88, pal.hx('592687', 66)),
       (0.915, pal.hx('391555', 92)), (0.945, pal.hx('391555', 120)), (0.97, pal.hx('391555', 148)),
       (0.99, pal.hx('391555', 176)), (9.0, pal.hx('391555', 200))]


def vignette_frame():
    g = pal.blank(VW, VH)
    keys = 'abcdefgh'
    local = {keys[i]: c for i, (lim, c) in enumerate(VIG)}
    for y in range(VH):
        for x in range(VW):
            u = abs(x + 0.5 - VW / 2.0) / (VW / 2.0)
            v = abs(y + 0.5 - VH / 2.0) / (VH / 2.0)
            r = (u ** 5 + v ** 5) ** 0.2
            if r < VIG[0][0] - 0.04:
                continue
            for i, (lim, c) in enumerate(VIG):
                if r <= lim:
                    g[y][x] = keys[i]
                    break
    return pal.Frame(pal.rows(g), local)


SHEETS = {
    'greyson_doom_orb': (orb_rows, (OW, OW)),
    'greyson_doom_orb_glow': (glow_rows, (OW, OW)),
    'greyson_doom_orb_burst': (burst_rows, (BW_, BW_)),
    'greyson_hype_streak': (lambda: streak_rows('violet'), (SW_, SW_)),
    'greyson_hype_streak_cyan': (lambda: streak_rows('cyan'), (SW_, SW_)),
    'greyson_doom_vignette': (lambda: [[vignette_frame()]], (VW, VH)),
}
