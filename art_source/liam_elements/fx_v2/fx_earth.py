"""FX v2 earth (attack 2; no keyline): the tremor ridge with debris jumping as it heaves and on every pulse, the racing
crack spitting dust and pebbles, the staff-slam burst throwing rocks and dust, and the pillar's base dust.

The ridge itself is the approved one: le_earth.ridge() (imported read-only, and checked by fx_build to still reproduce
the shipped sheet texel for texel) at the approved profile, so its silhouette, its footprint (rows 8..31, the collision
exactly) and its tapered ends are unchanged; v2 adds frames and what flies off it. Colours: the ridge's slate
(t T y Y), its crevice (Z), the earth green (8) with the white core (W) for the tell, dust (w v T) and ice plates ( ].
"""
import math
import sys

sys.dont_write_bytecode = True

import numpy as np

import fx_common as C
import le_earth as E          # read only
import le_pillar as PL        # read only

BW, BH = E.BW, E.BH           # 96 x 32
FOOT = E.FOOT                 # rows 8..31

# ------------------------------------------------------------------ the ridge block: 28 frames
PHASES = {'tell': (0, 5), 'heave': (6, 11), 'active': (12, 17), 'pulse': (18, 21), 'crumble': (22, 27)}
# Each clip ships as its own strip (liam_tremor_block_<clip>.png, addendum 3 E.2.6): the code spreads a one-shot's
# shipped length over its frames and keeps a loop's frame time.
CLIP_TIMES = {
    'tell': [0.1] * 6,                                   # 0.6 s: the crack slam to the heave slam, as shipped
    'heave': [0.04] * 6,                                 # 0.24 s, as shipped
    'active': [0.12] * 6,                                # the loop keeps its 0.12 s frame
    'pulse': [0.04] * 4,                                 # 0.16 s, as shipped
    'crumble': [0.05, 0.05, 0.05, 0.05, 0.06, 0.06],    # 0.32 s, as shipped, inside CRUMBLE_TIME (0.35)
}
CLIPS = ('tell', 'heave', 'active', 'pulse', 'crumble')
# The shipped 17-frame layout (tell 0-3, heave 4-6, active 7-10, pulse 11-12, crumble 13-16) cut from the v2 clips,
# for the code's fallback path when the per-clip strips are absent.
COMBINED_PICK = {'tell': [1, 2, 4, 5], 'heave': [0, 2, 3], 'active': [0, 1, 3, 4], 'pulse': [0, 2],
                 'crumble': [0, 2, 3, 4]}
BLOCK_TIMES = CLIP_TIMES['tell'] + CLIP_TIMES['heave'] + CLIP_TIMES['active'] + CLIP_TIMES['pulse'] + \
    CLIP_TIMES['crumble']
TOP, PEAKS = E._profile(3, 1.0)


def _peak_xs():
    """The ridge's summits (column, top row), left to right."""
    out = []
    for x in range(2, BW - 2):
        if TOP[x] <= TOP[x - 1] and TOP[x] < TOP[x + 1] and TOP[x] < 20:
            out.append((x, int(TOP[x])))
    return out


PEAK_XS = _peak_xs()


def _keep(shape, fade, seed=0):
    """Where thinning dust still stands: clumpy holes opening as fade goes 0 -> 1 (never a regular checker)."""
    if fade <= 0:
        return None
    h, w = shape
    n = 0.65 * C.vnoise((h, w), (max(1, h // 3), max(1, w // 3)), 900 + seed, periodic=(False, False)) + \
        0.35 * C.vnoise((h, w), (max(1, h // 2), max(1, w // 2)), 901 + seed, periodic=(False, False))
    return n >= fade


def _dust(cv, puffs, fade=0.0, seed=0):
    """Lit dust balls (the pillar dust's lambert puff); fade 0..1 breaks them up into clumps as they thin."""
    keep = _keep(cv.shape, fade, seed)
    for (cx, cy, r) in puffs:
        C.puff(cv, cx, cy, r, ('w', 'v', 'T'), 0.7, keep)


def _pebble(cv, x, y, big=False):
    """A stone in flight or on a slope: 3 = a lit 4x3 chunk, 2 (or True) = a 2x2 chip, else a 2x1 pebble."""
    if big == 3:
        C.stamp(cv, x, y, ['.tT.', 'tTTy', '.yY.'])
    elif big:
        C.chip(cv, x, y, 2)
    else:
        C.plot(cv, x, y, 't')
        C.plot(cv, x + 1, y, 'T')


def _flying(cv, spots, k0, k, g=1.2):
    """Chips thrown off at frame k0 from (x, y) with velocity (vx, vy): where they are at frame k."""
    for (x, y, vx, vy, big) in spots:
        a = k - k0
        if a < 0:
            continue
        px = x + vx * a
        py = y + vy * a + 0.5 * g * a * a
        if 0 <= py < BH - 1 and 0 <= px < BW - 1:
            _pebble(cv, px, py, big)


def block_tell(k):
    """0-5: the footprint's cracks spreading and lighting up green on the ice, the white core racing through them at
    the end; dust shivering out of the cracks and pebbles starting to jump. Earth green and white only - never the red
    parry badge or the yellow dodge ring."""
    cv = C.blank(BW, BH)
    reach = (0.3, 0.5, 0.7, 0.9, 1.0, 1.0)[k]
    E._inner_cracks(cv, 'Y' if k == 0 else '8', reach=reach)
    if k == 0:
        E._border(cv, 'Y', gaps=3)
    elif k == 1:
        E._border(cv, 'Y', gaps=5)
    elif k == 2:
        E._border(cv, '8', gaps=6)
    else:
        E._border(cv, '8')
    if k >= 4:
        E._inner_cracks(cv, 'W', reach=(0.45, 0.85)[k - 4], seed=9)
    if k == 5:
        for (x, y) in ((0, 8), (95, 8), (0, 31), (95, 31), (1, 8), (94, 8), (0, 9), (95, 9), (1, 31), (94, 31)):
            cv[y, x] = 'W'
    # dust shivering out of the cracks, and pebbles hopping on the ice as the ground trembles
    spots = [(14, 14), (33, 22), (52, 13), (71, 24), (86, 16)]
    if k >= 2:
        for i, (x, y) in enumerate(spots):
            if (i + k) % 2 == 0:
                r = 1.4 + 0.5 * ((k + i) % 3)
                _dust(cv, [(x, y - 1, r)], fade=0.25 if k >= 4 else 0.0)
    if k >= 3:
        hops = ((20, 1), (45, 2), (63, 1), (80, 2))
        for i, (x, base) in enumerate(hops):
            hop = (0, 2, 3, 1)[(k + i) % 4]
            C.plot(cv, x + (k % 2), 8 - hop, 'T')
            C.plot(cv, x + 1 + (k % 2), 8 - hop, 't')
    return cv


def block_heave(k):
    """6-11: 0 the ice plates break and tilt, chips spitting up; 1-2 the rock punches up through them to a third and
    two thirds of its height, debris flung up above it, dust bursting at its foot; 3 full height, the debris raining
    back on its slopes; 4 it settles, pebbles bouncing down; 5 the dust thins."""
    burst = [(9, 13, -1.4, -4.2, 3), (19, 15, 0.6, -4.8, 2), (28, 12, -0.8, -5.4, 3), (38, 14, 1.1, -4.4, 2),
             (47, 11, -0.4, -5.6, 3), (57, 13, 0.9, -5.0, 2), (66, 12, -1.0, -5.2, 3), (76, 14, 1.3, -4.6, 2),
             (86, 13, 1.6, -4.0, 3)]
    if k == 0:
        cv = C.blank(BW, BH)
        cv[FOOT[0]:FOOT[1] + 1, :] = '('
        E._inner_cracks(cv, 'Z', reach=1.0)
        E._border(cv, 'Y')
        for x in range(0, BW, 6):
            cv[FOOT[0] + 1, x:x + 3] = ']'
        _dust(cv, [(6, 30, 3), (90, 30, 3), (48, 31, 2.5)])
        _flying(cv, burst, 0, 0)
        return cv
    height = (0.3, 0.65, 1.0, 1.0, 1.0)[k - 1]
    cv = E.ridge(height=height, shake=(0, 0, 0, 1, 0)[k - 1])
    if k <= 2:
        E._border(cv, 'Y')
    dust = {1: [(8, 29, 3.5), (88, 29, 3.5), (30, 31, 3.0), (64, 31, 3.0)],
            2: [(6, 28, 4.5), (90, 28, 4.5), (28, 30, 3.5), (62, 30, 3.5), (46, 31, 2.8)],
            3: [(5, 28, 5.0), (91, 28, 5.0), (24, 30, 3.8), (70, 30, 3.8)],
            4: [(4, 27, 5.0), (92, 27, 5.0), (40, 31, 3.0)],
            5: [(3, 26, 4.5), (93, 26, 4.5)]}[k]
    _dust(cv, dust, fade=(0, 0, 0, 0.3, 0.55)[k - 1])
    _flying(cv, burst, 0, k, g=1.5)
    if k >= 3:
        # pebbles bouncing down the slopes as it settles
        for i, (px, pt) in enumerate(PEAK_XS[1::2]):
            d = (k - 3) * 2 + 1
            x = px + (d if i % 2 else -d)
            y = min(28, pt + 2 + d + (1 if (k + i) % 2 else 0))
            _pebble(cv, x, y)
    return cv


def block_active(k):
    """12-17 (loop): the standing ridge trembling a texel, its crevices flickering, a pebble trickling down a slope and
    a wisp of dust curling off its foot."""
    shake = (0, 1, 0, -1, 0, 0)[k]
    cv = E.ridge(shake=shake, glow=(0.0, 0.2, 0.0, 0.2, 0.0, 0.0)[k])
    px, pt = PEAK_XS[len(PEAK_XS) // 2]
    d = 1 + 2 * k
    _pebble(cv, px + d // 2 + shake, min(28, pt + 2 + d))
    px2, pt2 = PEAK_XS[1]
    d2 = 1 + 2 * ((k + 3) % 6)
    C.plot(cv, px2 - d2 // 2 + shake, min(28, pt2 + 2 + d2), 't')
    wisp = (k % 3)
    side = 4 if k < 3 else 91
    _dust(cv, [(side, 29 - wisp, 1.6 + 0.6 * wisp)], fade=0.2 * wisp)
    return cv


def block_pulse(k):
    """18-21: each slam flares the crevices green-white and jolts the ridge - pebbles jump off its summits and dust
    kicks off its foot - then it all settles back."""
    cv = E.ridge(glow=(1.0, 0.6, 0.3, 0.1)[k])
    hop = (1, 3, 2, 0)[k]
    for i, (px, pt) in enumerate(PEAK_XS):
        if i % 2:
            continue
        y = pt - hop + (1 if i % 4 == 2 else 0)
        if y >= 0:
            _pebble(cv, px + (i % 3) - 1, y)
    r = (2.5, 3.5, 3.8, 3.0)[k]
    _dust(cv, [(10, 30, r), (34, 30.5, r * 0.85), (60, 30.5, r * 0.85), (86, 30, r)], fade=(0, 0, 0.25, 0.55)[k])
    return cv


def block_crumble(k):
    """22-27: 0 it splits along dark seams; 1 the slabs break and tilt apart, chunks flying; 2 it sinks to half in a
    burst of dust; 3 a heap of rubble, chunks bouncing; 4 scattered stones and thinning dust; 5 the last pebbles (the
    code fades it out after)."""
    chunks = [(14, 10, -1.4, -3.2, True), (33, 8, 0.6, -3.8, True), (52, 9, -0.4, -4.0, True),
              (70, 10, 1.1, -3.4, True), (84, 12, 1.6, -2.8, False), (24, 12, -0.8, -3.0, False)]
    if k == 0:
        cv = E.ridge(height=0.95)
        for x in range(4, BW - 4, 11):
            for y in range(3, 29):
                if cv[y, x] != '.':
                    cv[y, x] = 'Z'
        _flying(cv, chunks, 0, 0)
        return cv
    if k == 1:
        cv = E.ridge(height=0.8)
        for x in range(4, BW - 4, 11):
            cv[:29, x] = '.'
            for y in range(2, 29):
                if cv[y, x - 1] != '.':
                    cv[y, x - 1] = 'Z'
        _flying(cv, chunks, 0, 1, g=1.4)
        _dust(cv, [(8, 29, 3.0), (48, 30, 2.6), (88, 29, 3.0)])
        return cv
    if k == 2:
        cv = E.ridge(height=0.5)
        _dust(cv, [(8, 27, 4.8), (30, 28, 4.2), (52, 28, 4.6), (74, 27, 4.2), (90, 28, 4.0)])
        _flying(cv, chunks, 0, 2, g=1.4)
        return cv
    if k == 3:
        cv = E.ridge(height=0.22)
        _dust(cv, [(10, 25, 5.0), (40, 26, 5.0), (70, 25, 5.0), (90, 27, 3.6)], fade=0.2)
        _flying(cv, chunks, 0, 3, g=1.4)
        return cv
    cv = C.blank(BW, BH)
    rnd = np.random.RandomState(77 + k)
    n = 24 if k == 4 else 10
    for _ in range(n):
        x, y = rnd.randint(1, BW - 3), rnd.randint(FOOT[0] + 10, FOOT[1] - 1)
        E._chips(cv, [(x, y)])
    if k == 4:
        _dust(cv, [(20, 26, 3.4), (55, 27, 3.4), (82, 26, 3.4)], fade=0.5)
    return cv


CLIP_FUNCS = {'tell': (block_tell, 6), 'heave': (block_heave, 6), 'active': (block_active, 6),
              'pulse': (block_pulse, 4), 'crumble': (block_crumble, 6)}


def clip_frames(clip):
    """One clip's strip: liam_tremor_block_<clip>.png."""
    fn, n = CLIP_FUNCS[clip]
    return [fn(k) for k in range(n)]


def block_frames():
    """Every clip in order (tell 0-5, heave 6-11, active 12-17, pulse 18-21, crumble 22-27): previews only."""
    out = []
    for clip in CLIPS:
        out += clip_frames(clip)
    return out


def combined_frames():
    """liam_tremor_block.png in the shipped 17-frame layout, cut from the v2 clips (the code's fallback path)."""
    out = []
    for clip in CLIPS:
        fr = clip_frames(clip)
        out += [fr[i] for i in COMBINED_PICK[clip]]
    return out


# ------------------------------------------------------------------ the racing crack: 16 x 8, pivot (0, 4), loop
CRACK_FRAMES = 6
CRACK_TIME = 0.06
CRACK_PTS = [(0, 4), (3, 3), (6, 4), (9, 5), (12, 4), (15, 3)]      # the shipped path


def crack_segment(k):
    """A crack segment (laid end to end from the pillar's foot to a ridge, the code rotates it): the line glows earth
    green along the shipped path, a white-hot pulse runs along it, and it spits dust puffs and pebbles out either side
    in turn. Every frame shows the whole line, so the crack never flickers shorter."""
    cv = C.blank(16, 8)
    for i in range(len(CRACK_PTS) - 1):
        (x0, y0), (x1, y1) = CRACK_PTS[i], CRACK_PTS[i + 1]
        C.R.line(cv, x0, y0 + 1, x1, y1 + 1, 'Z')
    for i in range(len(CRACK_PTS) - 1):
        (x0, y0), (x1, y1) = CRACK_PTS[i], CRACK_PTS[i + 1]
        C.R.line(cv, x0, y0, x1, y1, '8')
    # the white pulse racing along it
    p = k * 16 / CRACK_FRAMES
    for i in range(len(CRACK_PTS) - 1):
        (x0, y0), (x1, y1) = CRACK_PTS[i], CRACK_PTS[i + 1]
        for t in np.linspace(0, 1, 5):
            x = x0 + (x1 - x0) * t
            if abs(x - p) < 1.2:
                C.plot(cv, x, y0 + (y1 - y0) * t, 'W')
    # dust puffs spat out one side then the other, and pebbles hopping out of the crack
    puffs = {0: [(4, 1.6, 1.6)], 1: [(4, 1.3, 2.2)], 2: [(4, 1.0, 1.8), (11, 6.2, 1.5)], 3: [(11, 6.4, 2.1)],
             4: [(11, 6.8, 1.7), (8, 1.6, 1.4)], 5: [(8, 1.2, 1.9)]}[k]
    X, Y = C.R.centres(16, 8)
    for (px, py, r) in puffs:
        m = ((X - px) / r) ** 2 + ((Y - py) / (r * 0.8)) ** 2 <= 1
        v = C.R.lambert(C.R.sphere_normal(X, Y, px, py, r, r * 0.8))
        cv[m] = np.where(v > 0.6, 'w', np.where(v > 0.3, 'v', 'T'))[m]
    hop = {0: [(7, 2)], 1: [(8, 0)], 2: [(9, 1), (13, 6)], 3: [(14, 7)], 4: [(2, 6)], 5: [(1, 7)]}[k]
    for (x, y) in hop:
        C.plot(cv, x, y, 't')
        C.plot(cv, x + 1, y, 'T')
    return cv


# ------------------------------------------------------------------ the slam burst: 32 x 16, pivot (16, 15)
SLAM_FRAMES = 6
SLAM_TIMES = [0.03, 0.03, 0.04, 0.04, 0.04, 0.04]           # 0.22 s: the shipped burst's length
SLAM_PIVOT = (16, 15)


def slam_burst(k):
    """His staff butt striking the pillar's top: 0 a green flash ring with a white core; 1 the ring spreading, rocks
    launched up and dust bursting out; 2 rocks at the top of their arc, dust billowing; 3 rocks falling, dust rolling
    outward; 4 the rocks landing, dust spreading flat; 5 the dust thinning away."""
    cv = C.blank(32, 16)
    cx, cy = SLAM_PIVOT
    X, Y = C.R.centres(32, 16)
    if k == 0:
        ring = (((X - cx) / 12) ** 2 + ((Y - cy) / 4.6) ** 2 <= 1) & (((X - cx) / 7.5) ** 2 + ((Y - cy) / 2.6) ** 2 > 1)
        cv[ring] = '8'
        core = ((X - cx) / 5.4) ** 2 + ((Y - cy) / 2.4) ** 2 <= 1
        cv[core] = 'W'
        for a in (195, 220, 245, 270, 295, 320, 345):
            for r in range(3, 11):
                x = cx + math.cos(math.radians(a)) * r * 1.5
                y = cy + math.sin(math.radians(a)) * r
                C.plot(cv, x, y, 'W' if r < 5 else '8')
        return cv
    if k <= 2:
        rx = (0, 12.5, 14.5)[k]
        C.arc(cv, cx, cy, rx, rx * 0.3, 180, 360, '8', gaps=(lambda u, k=k: k == 2 and int(u * 20) % 3 == 0))
        C.arc(cv, cx, cy, rx - 1.5, (rx - 1.5) * 0.3, 185, 355, 'Y' if k == 2 else '8',
              gaps=(lambda u: int(u * 20) % 4 == 0))
    dust = {1: [(cx - 9, 13.5, 2.6), (cx + 9, 13.5, 2.6)],
            2: [(cx - 10, 12, 4.2), (cx + 10, 12, 4.2), (cx, 13.2, 3.0)],
            3: [(cx - 12, 11.6, 4.6), (cx + 12, 11.6, 4.6), (cx - 3, 12.8, 3.4), (cx + 4, 13, 3.2)],
            4: [(cx - 13, 12, 4.4), (cx + 13, 12, 4.4), (cx, 13, 3.4)],
            5: [(cx - 14, 12.8, 3.0), (cx + 14, 12.8, 3.0), (cx, 13.5, 2.4)]}[k]
    fade = {1: 0, 2: 0, 3: 0, 4: 0.32, 5: 0.58}[k]
    keep = _keep(cv.shape, fade, seed=k)
    for (x, y, r) in dust:
        C.puff(cv, x, y, r, ('w', 'v', 'T'), 0.7, keep)
    rocks = [(cx - 4, 12, -1.5, -4.6, True), (cx + 3, 12, 1.3, -5.0, True), (cx - 8, 13, -2.2, -3.4, False),
             (cx + 8, 13, 2.4, -3.6, False), (cx, 11, 0.2, -5.4, False)]
    for (x, y, vx, vy, big) in rocks:
        a = k - 1
        px = x + vx * a
        py = y + vy * a + 0.5 * 2.3 * a * a
        land = 14.0 if big else 14.5
        if py > land:
            py = land - (1 if k == 4 else 0)
            px = x + vx * min(a, 3.2)
        if 0 <= px < 31 and 0 <= py < 16:
            if big and k < 5:
                C.stamp(cv, px - 1, py - 2, ['.tT.', 'tTTy', '.yY.'])
            else:
                C.plot(cv, px, py, 'T')
    return cv


# ------------------------------------------------------------------ the pillar's base dust: 64 x 80, anchor (32, 72)
DUST_FRAMES = 7
DUST_TIME = 0.065                 # 0.455 s (shipped 3 x 0.08 = 0.24 s): see contract.json


def pillar_dust(k):
    """At the pillar's foot as it rises out of the floor or crumbles into it: 0 dust bursting out both sides and pebbles
    kicked out; 1-2 the billows rolling outward and up, pebbles arcing; 3 they spread, the pebbles landing; 4-6 they
    thin and drift away."""
    cv = PL.blank()
    sets = {
        0: [(11, 73, 4.5), (53, 73, 4.5), (22, 77, 3.0), (42, 77, 3.0)],
        1: [(9, 71, 5.5), (55, 71, 5.5), (19, 76, 3.6), (45, 76, 3.6), (32, 78, 2.6)],
        2: [(8, 68, 6.4), (56, 68, 6.4), (16, 74, 4.2), (48, 74, 4.2), (32, 77, 3.0)],
        3: [(7, 65, 6.6), (57, 65, 6.6), (14, 72, 4.6), (50, 72, 4.6)],
        4: [(6, 62, 6.2), (58, 62, 6.2), (13, 70, 4.2), (51, 70, 4.2)],
        5: [(5, 59, 5.4), (59, 59, 5.4), (12, 68, 3.6), (52, 68, 3.6)],
        6: [(5, 57, 4.6), (59, 57, 4.6)],
    }[k]
    fade = (0, 0, 0, 0.3, 0.44, 0.56, 0.66)[k]
    keep = _keep(cv.shape, fade, seed=k)
    for (x, y, r) in sets:
        C.puff(cv, x, y, r, ('w', 'v', 'T'), 0.72, keep)
    pebbles = [(14, 71, -1.6, -3.4), (50, 71, 1.6, -3.4), (20, 73, -1.0, -2.6), (44, 73, 1.1, -2.8)]
    for (x, y, vx, vy) in pebbles:
        a = k
        px = x + vx * a
        py = y + vy * a + 0.5 * 1.4 * a * a
        if py > 78:
            py = 78
            px = x + vx * 4.6
        if 0 <= px < 63 and 0 <= py < 79 and k < 6:
            C.chip(cv, px, py, 2 if k < 3 else 1)
    return cv
