"""Attack 2's earth pieces (no keyline): the tremor ridge block (liam_tremor_block.png, 17 frames of
96 x 32), the racing crack segment (liam_tremor_crack.png, 16 x 8) and the staff-slam burst on the pillar
top (liam_slam_burst.png, 32 x 16).

Block: the footprint is rows 8..31 (96 x 24 texels = 288 x 72 px), exactly the collision rectangle; rows
0..7 hold only rock jutting up. Its ends taper so neighbours can overlap them by 16 texels.
The tell glows EARTH GREEN (his rune colour) with a white core - not the red parry badge, not the yellow
dodge ring. Colours: his slate greys, the ice's pale blues, the earth green, and Z for the deepest cracks.
"""
import math

import numpy as np

import le_rig as R
import le_ice  # noqa: F401  (floor keys)

BW, BH = 96, 32
FOOT = (8, 31)                   # footprint rows (inclusive)


def _profile(seed=3, height=1.0):
    """The ridge's jagged top edge: row of the rock's top per column (smaller = taller)."""
    rnd = np.random.RandomState(seed)
    peaks = []
    x = 2
    while x < BW - 2:
        w = rnd.randint(9, 15)
        peaks.append((x, x + w, rnd.randint(0, 6)))
        x += w - rnd.randint(1, 3)
    top = np.full(BW, 30.0)
    for (x0, x1, pk) in peaks:
        xm = (x0 + x1) / 2 + rnd.randint(-2, 3)
        for xx in range(max(0, x0), min(BW, x1)):
            t = abs(xx - xm) / max(1.0, (x1 - x0) / 2)
            y = pk + t * 9
            top[xx] = min(top[xx], y)
    # taper the ends (the overlaps): the last 14 texels drop toward the footprint's middle
    for xx in range(BW):
        e = min(xx, BW - 1 - xx)
        if e < 14:
            top[xx] = max(top[xx], 6 + (14 - e) * 0.9)
    top = 30 - (30 - top) * height
    return np.clip(np.round(top).astype(int), 0, 30), peaks


def ridge(seed=3, height=1.0, shake=0, glow=0.0, ice_caps=True):
    """The heaved ridge: slate slabs with lit left-facing slopes, dark crevices at the valleys, ice
    plates on some caps, rubble along the footprint's front edge. glow 0..1 lights the crevices."""
    cv = R.blank(BW, BH)
    top, peaks = _profile(seed, height)
    for x in range(BW):
        xs = (x + shake) % BW if False else x
        t = top[x]
        slope = top[min(BW - 1, x + 1)] - top[max(0, x - 1)]      # > 0: the surface falls to the right
        # which way this column's slab face turns: rising-left faces catch the light
        lit = slope > 0.5
        dark = slope < -0.5
        for y in range(t, 29):
            depth = (y - t)
            if depth <= 1:
                ch = 't' if not dark else 'T'
            elif lit:
                ch = 'T' if depth <= 7 else 'y'
            elif dark:
                ch = 'y' if depth <= 5 else 'Y'
            else:
                ch = 'T' if depth <= 3 else 'y'
            if y >= 24:
                ch = 'Y' if ch in 'yY' else 'y'
            cv[y, x] = ch
    # crevices between slabs: dark vertical cracks from each valley down
    valleys = [x for x in range(2, BW - 2) if top[x] > top[x - 1] and top[x] >= top[x + 1]]
    for x in valleys:
        for y in range(top[x], 28):
            cv[y, x] = 'Z' if glow <= 0 else ('W' if (glow > 0.7 and y % 3 == 0) else '8')
    # ice plates riding up on some caps
    if ice_caps:
        for (x0, x1, pk) in peaks[1::3]:
            for xx in range(max(0, x0 + 2), min(BW, x0 + 7)):
                y = top[xx]
                if y < 28:
                    cv[y, xx] = ']'
                    if y + 1 < 28:
                        cv[y + 1, xx] = '('
    # rubble along the front edge of the footprint (rows 27..31)
    rnd = np.random.RandomState(seed + 5)
    for x in range(BW):
        r = rnd.rand()
        cv[29, x] = 'y' if r < 0.6 else 'T'
        cv[30, x] = 'Y' if r < 0.5 else 'y'
        cv[31, x] = 'Z' if r < 0.35 else 'Y'
        if r > 0.8:
            cv[28, x] = 't'
    if shake:
        cv = R.shift(cv, shake, 0)
        # keep the footprint's border crisp after the shake
        cv[:, 0 if shake > 0 else BW - 1] = cv[:, 1 if shake > 0 else BW - 2]
    return cv


def _border(cv, ch, core=None, gaps=0):
    """The footprint rectangle (rows 8..31, x 0..95) drawn as a hard edge; optional glowing core."""
    y0, y1 = FOOT
    pts = [(x, y0) for x in range(BW)] + [(x, y1) for x in range(BW)] + \
          [(0, y) for y in range(y0, y1 + 1)] + [(BW - 1, y) for y in range(y0, y1 + 1)]
    for i, (x, y) in enumerate(pts):
        if gaps and (i // 4) % gaps == gaps - 1:
            continue
        cv[y, x] = ch
    return cv


def _inner_cracks(cv, ch, reach=1.0, seed=9):
    rnd = np.random.RandomState(seed)
    y0, y1 = FOOT
    for k in range(5):
        x = 8 + k * 19 + rnd.randint(-3, 4)
        y = y0 + 1
        steps = int((y1 - y0 - 1) * reach)
        for s in range(steps):
            cv[y, max(0, min(BW - 1, x))] = ch
            y += 1
            x += rnd.choice((-1, 0, 0, 1))
            if y > y1 - 1:
                break
    # one long zig-zag along the footprint
    x, y = 2, (y0 + y1) // 2
    while x < int((BW - 2) * reach):
        cv[y, x] = ch
        x += 1
        if rnd.rand() < 0.3:
            y = max(y0 + 2, min(y1 - 2, y + rnd.choice((-1, 1))))
    return cv


def tell(k):
    """Frames 0-3: the footprint's cracks light up green on the ice, brighter each frame."""
    cv = R.blank(BW, BH)
    if k == 0:
        _inner_cracks(cv, 'Y', reach=0.5)
        _border(cv, 'Y', gaps=3)
    elif k == 1:
        _inner_cracks(cv, '8', reach=0.8)
        _border(cv, 'Y', gaps=5)
    elif k == 2:
        _inner_cracks(cv, '8', reach=1.0)
        _border(cv, '8')
    else:
        _inner_cracks(cv, '8', reach=1.0)
        _border(cv, '8')
        _inner_cracks(cv, 'W', reach=0.45, seed=9)
        # corners flare white
        for (x, y) in ((0, 8), (95, 8), (0, 31), (95, 31), (1, 8), (94, 8), (0, 9), (95, 9)):
            cv[y, x] = 'W'
    return cv


def heave(k):
    """Frames 4-6: 4 the ice breaks into tilted plates with dust at the edges; 5 rock shoulders up
    through them (half height); 6 the full ridge with chips flying."""
    if k == 0:
        cv = R.blank(BW, BH)
        cv[FOOT[0]:FOOT[1] + 1, :] = '('
        _inner_cracks(cv, 'Z', reach=1.0)
        _border(cv, 'Y')
        for x in range(0, BW, 6):
            cv[FOOT[0] + 1, x:x + 3] = ']'
        _puffs(cv, [(6, 30, 3), (90, 30, 3), (48, 31, 2.5)])
        return cv
    if k == 1:
        cv = ridge(height=0.55)
        _border(cv, 'Y')
        _puffs(cv, [(8, 29, 3.5), (88, 29, 3.5), (40, 31, 2.5), (62, 31, 2.5)])
        return cv
    cv = ridge(height=1.0)
    _chips(cv, [(12, 2), (30, 1), (57, 3), (79, 0), (44, 5)])
    _puffs(cv, [(6, 29, 3), (90, 29, 3)])
    return cv


def _puffs(cv, puffs):
    X, Y = R.centres(BW, BH)
    for (cx, cy, r) in puffs:
        m = ((X - cx) / r) ** 2 + ((Y - cy) / (r * 0.7)) ** 2 <= 1
        v = R.lambert(R.sphere_normal(X, Y, cx, cy, r, r * 0.7))
        cv[m] = np.where(v > 0.7, 'w', np.where(v > 0.35, 'v', 'T'))[m]


def _chips(cv, pts):
    for (x, y) in pts:
        for (dx, dy, ch) in ((0, 0, 't'), (1, 0, 'T'), (0, 1, 'y'), (1, 1, 'Y')):
            if 0 <= x + dx < BW and 0 <= y + dy < BH:
                cv[y + dy, x + dx] = ch


def active(k):
    """Frames 7-10: the standing ridge, a 1-px tremble and a faint crevice flicker (loop)."""
    shake = (0, 1, 0, -1)[k]
    cv = ridge(shake=shake, glow=0.2 if k % 2 else 0.0)
    if k in (1, 3):
        _puffs(cv, [(4 + k * 20, 30, 2.0), (70 - k * 10, 30, 2.0)])
    return cv


def pulse(k):
    """Frames 11-12: every slam makes the crevices flare green-white and kicks dust off the front."""
    if k == 0:
        cv = ridge(glow=1.0)
        _puffs(cv, [(10, 29, 3.5), (34, 30, 3), (60, 30, 3), (86, 29, 3.5)])
    else:
        cv = ridge(glow=0.5)
        _puffs(cv, [(8, 30, 2.5), (88, 30, 2.5)])
    return cv


def crumble(k):
    """Frames 13-16: the ridge splits, sinks to rubble, and the last pebbles fade out."""
    if k == 0:
        cv = ridge(height=0.9)
        for x in range(4, BW - 4, 11):
            for y in range(4, 28):
                if cv[y, x] != '.':
                    cv[y, x] = 'Z'
        _chips(cv, [(20, 3), (50, 1), (71, 4)])
        return cv
    if k == 1:
        cv = ridge(height=0.45)
        _puffs(cv, [(10, 26, 4), (40, 27, 4), (70, 26, 4), (90, 28, 3)])
        return cv
    cv = R.blank(BW, BH)
    rnd = np.random.RandomState(77 + k)
    n = 26 if k == 2 else 11
    for _ in range(n):
        x, y = rnd.randint(1, BW - 3), rnd.randint(FOOT[0] + 8, FOOT[1] - 1)
        _chips(cv, [(x, y)])
    if k == 2:
        _puffs(cv, [(20, 26, 3), (55, 27, 3), (82, 26, 3)])
    return cv


def block_frames():
    return [tell(k) for k in range(4)] + [heave(k) for k in range(3)] + [active(k) for k in range(4)] + \
           [pulse(k) for k in range(2)] + [crumble(k) for k in range(4)]


BLOCK_TIMES = [0.15] * 4 + [0.06, 0.08, 0.10] + [0.12] * 4 + [0.06, 0.10] + [0.08] * 4


def crack_segment(k):
    """16 x 8, pivot (0, 4): a crack racing along the floor from the pillar to a block (the code rotates
    it). 0 forming (half), 1 glowing, 2 cooling."""
    cv = R.blank(16, 8)
    pts = [(0, 4), (3, 3), (6, 4), (9, 5), (12, 4), (15, 3)]
    n = (3, 6, 6)[k]
    for i in range(n - 1):
        R.line(cv, pts[i][0], pts[i][1], pts[i + 1][0], pts[i + 1][1], 'Z' if k == 2 else '8')
    if k == 1:
        for (x, y) in pts[1:5]:
            cv[y, x] = 'W'
        for (x, y) in ((5, 2), (10, 6), (13, 2)):
            cv[y, x] = '8'
    if k == 2:
        for (x, y) in pts[2:5]:
            cv[y, x] = '8'
    return cv


def slam_burst(k):
    """32 x 16, pivot (16, 15) = the staff butt on the pillar top: 0 a green flash ring; 1 chips and dust
    thrown out; 2 dust settling."""
    cv = R.blank(32, 16)
    X, Y = R.centres(32, 16)
    cx, cy = 16, 15
    if k == 0:
        ring = (((X - cx) / 9) ** 2 + ((Y - cy) / 3.5) ** 2 <= 1) & (((X - cx) / 6.5) ** 2 + ((Y - cy) / 2.2) ** 2 > 1)
        cv[ring] = '8'
        core = ((X - cx) / 4) ** 2 + ((Y - cy) / 1.8) ** 2 <= 1
        cv[core] = 'W'
        for a in (200, 230, 270, 310, 340):
            for r in range(3, 8):
                x, y = int(cx + math.cos(math.radians(a)) * r * 1.5), int(cy + math.sin(math.radians(a)) * r)
                if 0 <= x < 32 and 0 <= y < 16:
                    cv[y, x] = 'W' if r < 5 else '8'
    elif k == 1:
        for (px_, py_, r) in ((8, 13, 3.2), (24, 13, 3.2), (16, 14, 2.4)):
            m = ((X - px_) / r) ** 2 + ((Y - py_) / (r * 0.7)) ** 2 <= 1
            v = R.lambert(R.sphere_normal(X, Y, px_, py_, r, r * 0.7))
            cv[m] = np.where(v > 0.7, 'w', np.where(v > 0.35, 'v', 'T'))[m]
        for (x, y) in ((5, 5), (11, 2), (20, 1), (27, 4), (15, 6)):
            for (dx, dy, ch) in ((0, 0, 't'), (1, 0, 'T'), (0, 1, 'y'), (1, 1, 'Y')):
                cv[y + dy, x + dx] = ch
    else:
        for (px_, py_, r) in ((6, 12, 3.6), (26, 12, 3.6), (16, 11, 2.6)):
            m = (((X - px_) / r) ** 2 + ((Y - py_) / (r * 0.7)) ** 2 <= 1) & ((X + Y) % 2 < 1.5)
            cv[m] = 'v'
        for (x, y) in ((3, 9), (29, 8)):
            cv[y, x] = 'T'
    return cv
