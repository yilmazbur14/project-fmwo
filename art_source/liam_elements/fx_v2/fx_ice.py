"""FX v2 ice (attack 2's floor; no keyline): the freeze front with crystals sprouting as it runs, the shatter with
plates lifting apart and shards glinting, and the melt beading into drips and pooling back to open water.

The ice tile itself (liam_ice.png) and the flood's nested coverage frames are untouched: the shatter and melt start from
the shipped ice tile and the melt ends on the shipped flood frame 5, texel for texel. Colours are the floor's own
semi-transparent keys ( ) [ ] { } < > ^ " only, so the ice stays paler and more opaque than the water.
"""
import math
import sys

sys.dont_write_bytecode = True

import numpy as np

import fx_common as C

T = 64


def shipped_ice():
    return C.shipped('liam_ice', T)[0]


def shipped_flood(k):
    return C.shipped('liam_flood', T)[k]


# ------------------------------------------------------------------ freeze front: 16 x 16, pivot (8, 8), loop
FRONT_FRAMES = 6
FRONT_TIME = 0.08


def freeze_front(k):
    """A frost crystal stamped along the growing edge of the ice (every 48 px, all on one frame): 0 a seed; 1-3 six
    arms shooting out and branching; 4 the crystal glints; 5 it sets into the sheet (arms greying to seam blue) as the
    next seed forms. The pieces ride the edge, so each frame lands somewhere new: the rim reads as crystals sprouting
    all along the front."""
    cv = C.blank(16, 16)
    cx, cy = 7.5, 7.5
    arm = (2.0, 3.6, 5.2, 6.6, 6.8, 6.0)[k]
    branch = (0, 0, 1, 2, 2, 1)[k]
    for i in range(6):
        ang = math.radians(90 + 60 * i + (8 if k % 2 else 0) * (0 if k < 4 else 1))
        dx, dy = math.cos(ang), math.sin(ang) * 0.82
        n = int(round(arm))
        for r in range(1, n + 1):
            u = r / max(1.0, arm)
            if k == 5:
                ch = ')' if u > 0.5 else '('
            elif k == 4:
                ch = ']' if (r == n or r == 2) else '['
            else:
                ch = ']' if r == n else ('[' if u < 0.7 else ')')
            C.plot(cv, cx + dx * r, cy + dy * r, ch)
        if branch:
            for b in range(branch):
                at = arm * (0.5 + 0.22 * b)
                bx, by = cx + dx * at, cy + dy * at
                blen = 2 if b == 0 and k in (3, 4) else 1
                for s in (-1, 1):
                    ba = ang + s * math.radians(55)
                    for r in range(1, blen + 1):
                        C.plot(cv, bx + math.cos(ba) * r, by + math.sin(ba) * r * 0.82,
                               ')' if k == 5 else ('[' if r < blen else ']'))
    core = C.ellipse_mask(16, 16, cx + 0.5, cy + 0.5, 1.8 + 0.3 * min(k, 3), 1.5 + 0.25 * min(k, 3))
    cv[core] = '[' if k < 5 else '('
    C.plot(cv, cx, cy, ']')
    if k == 4:
        for (sx, sy) in ((cx + 5, cy - 3), (cx - 4, cy + 4)):
            C.spark(cv, sx, sy, 1, ']', '[')
    if k == 5:
        seed = C.ellipse_mask(16, 16, cx + 3.5, cy - 2.5, 1.2, 1.0)
        cv[seed] = '['
    return cv


# ------------------------------------------------------------------ shatter: 64 x 64 tile over SHATTER_TIME
SHATTER_FRAMES = 8


def _voronoi(n_seeds, seed):
    """A seamless Voronoi on the 64 x 64 tile: each texel's plate id, its seed's position and the edge mask."""
    rnd = np.random.RandomState(seed)
    pts = rnd.rand(n_seeds, 2) * T
    ys, xs = np.mgrid[0:T, 0:T] + 0.5
    best = np.full((T, T), 1e9)
    idx = np.zeros((T, T), dtype=int)
    for i, (px, py) in enumerate(pts):
        dx = np.abs(xs - px)
        dx = np.minimum(dx, T - dx)
        dy = np.abs(ys - py)
        dy = np.minimum(dy, T - dy)
        d = dx * dx * 1.0 + dy * dy * 1.35
        m = d < best
        best[m] = d[m]
        idx[m] = i
    edge = (idx != np.roll(idx, 1, axis=1)) | (idx != np.roll(idx, 1, axis=0))
    return idx, pts, edge


def _shift_wrap(a, dx, dy):
    return np.roll(np.roll(a, dy, axis=0), dx, axis=1)


def ice_shatter(k, seed=51):
    """The ice breaking under the round's air blast: 0 cracks race across it; 1 the web closes into plates; 2 the plates
    heave up, lit on their top edges and shadowed under, shards spitting out of the seams; 3 they part, shards flying;
    4 they break smaller and slide apart; 5-7 the last pieces and glinting shards. Holes show what is under the ice."""
    base = shipped_ice()
    idx, pts, edge = _voronoi(11, seed)
    idx2, pts2, edge2 = _voronoi(26, seed + 1)
    rnd = np.random.RandomState(seed + 2)
    keep = {i: rnd.rand() for i in range(26)}
    ys, xs = np.mgrid[0:T, 0:T]
    cv = base.copy()
    if k == 0:
        # cracks racing out from three impact points across the tile
        for (x0, y0) in ((12, 20), (44, 12), (30, 50)):
            d = np.hypot(np.minimum(np.abs(xs - x0), T - np.abs(xs - x0)), np.minimum(np.abs(ys - y0), T - np.abs(ys - y0)))
            reach = edge & (d < 20)
            cv[reach] = ')'
            core = edge & (d < 11)
            cv[core] = ']'
            C.spark(cv, x0, y0, 1, ']', '[', wrap_x=True, wrap_y=True)
        return cv
    if k == 1:
        cv[edge] = ')'
        lit = _shift_wrap(edge, 1, 1) & ~edge
        cv[lit] = ']'
        return cv
    if k == 2:
        # plates heave: each lifted a texel, a lit rim on top and a shadow line under it; shards pop from the seams
        lifted = C.blank(T, T)
        plate = ~edge
        up = _shift_wrap(plate, 0, -1)
        lifted[up] = _shift_wrap(base, 0, -1)[up]
        top_rim = up & ~_shift_wrap(up, 0, 1)
        lifted[top_rim] = ']'
        under = plate & ~up
        lifted[under] = ')'
        tilt = np.vectorize(lambda i: keep.get(i, 0.5))(idx)
        lifted[up & ~top_rim & (tilt > 0.66)] = '['
        lifted[up & ~top_rim & (tilt < 0.3)] = '{'
        cv = lifted
        for (x, y) in pts:
            for j in range(3):
                a = rnd.uniform(0, 2 * math.pi)
                r = rnd.uniform(4, 8)
                C.plot(cv, x + r * math.cos(a), y + r * math.sin(a) * 0.8 - 2, ']', wrap_x=True, wrap_y=True)
        return cv
    # 3+: plates part and break, shrinking toward their seeds; shards fly and glint
    sets = {3: (idx, pts, 1, 0.0), 4: (idx2, pts2, 1, 0.3), 5: (idx2, pts2, 2, 0.55), 6: (idx2, pts2, 3, 0.75),
            7: (idx2, pts2, 4, 0.9)}
    ids, seeds, erode, drop = sets[k]
    e = (ids != np.roll(ids, 1, axis=1)) | (ids != np.roll(ids, 1, axis=0))
    gone = e.copy()
    for _ in range(erode - 1):
        g2 = gone.copy()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            g2 |= _shift_wrap(gone, dx, dy)
        gone = g2
    alive = ~gone
    if drop:
        dead = np.vectorize(lambda i: keep.get(i, 0.5) < drop)(ids)
        alive &= ~dead
    out = C.blank(T, T)
    # each surviving piece drifts a little away from the tile's impact points and keeps a lit rim
    out[alive] = base[alive]
    tilt = np.vectorize(lambda i: keep.get(i, 0.5))(ids)
    out[alive & (tilt > 0.7)] = '['
    out[alive & (tilt < 0.25)] = '{'
    top_rim = alive & ~_shift_wrap(alive, 0, 1)
    out[top_rim] = ']'
    bot_rim = alive & ~_shift_wrap(alive, 0, -1)
    out[bot_rim] = ')'
    # shards: flung out of the seams, glinting
    rnd = np.random.RandomState(seed + 3)
    for i in range(30):
        x0, y0 = rnd.uniform(0, T), rnd.uniform(0, T)
        a = rnd.uniform(0, 2 * math.pi)
        dist = (k - 2) * rnd.uniform(2.5, 4.5)
        x, y = x0 + dist * math.cos(a), y0 + dist * math.sin(a) * 0.8
        if k >= 6 and i % 3:
            continue
        if (i + k) % 4 == 0:
            C.spark(out, x, y, 1, ']', '[', wrap_x=True, wrap_y=True)
        else:
            C.plot(out, x, y, ']', wrap_x=True, wrap_y=True)
            C.plot(out, x + 1, y, '[', wrap_x=True, wrap_y=True)
    return out


# ------------------------------------------------------------------ melt: 64 x 64 tile over melt_time
MELT_FRAMES = 6


RING_PTS = [
    [(0, 0, ']'), (-1, 0, '^'), (1, 0, '^'), (0, -1, '^'), (0, 1, '^')],
    [(-1, -1, '^'), (0, -1, '^'), (1, -1, '^'), (-2, 0, '^'), (2, 0, '^'), (-1, 1, '^'), (0, 1, '^'), (1, 1, '^')],
    [(-2, -1, '"'), (-1, -1, '"'), (0, -1, '"'), (1, -1, '"'), (2, -1, '"'), (-3, 0, '"'), (3, 0, '"'),
     (-2, 1, '"'), (-1, 1, '"'), (0, 1, '"'), (1, 1, '"'), (2, 1, '"')],
    [(-2, -1, '"'), (0, -1, '"'), (2, -1, '"'), (-3, 0, '"'), (3, 0, '"'), (-1, 1, '"'), (1, 1, '"')],
]


def _drip_ring(cv, x, y, age):
    """A drip landing in open water: a fleck, a small ring, a wider fainter ring, its last arcs."""
    for dx, dy, ch in RING_PTS[age]:
        C.plot(cv, x + dx, y + dy, ch, wrap_x=True, wrap_y=True)


def ice_melt(k, seed=31):
    """The ice going back to water once the maze is over: 0 the sheet sweats, beads of water standing along its seams;
    1 the beads run in drips and wet patches open; 2 puddles spread between floes, water dripping off their edges;
    3 slush and small floes, drips ringing where they land; 4 the last slush; 5 open water = the flood's frame 5."""
    if k == MELT_FRAMES - 1:
        return shipped_flood(5)
    base = shipped_ice()
    water = shipped_flood(5)
    n = C.vnoise((T, T), (6, 6), seed)
    n2 = C.vnoise((T, T), (12, 12), seed + 1)
    cv = base.copy()
    wet = n < (0.18, 0.36, 0.58, 0.8, 0.94)[k]
    cv[wet] = water[wet]
    # floe rims and slush where ice meets water
    ice = ~wet
    rim = ice & (_shift_wrap(wet, 1, 0) | _shift_wrap(wet, -1, 0) | _shift_wrap(wet, 0, 1) | _shift_wrap(wet, 0, -1))
    cv[rim] = '}' if k >= 2 else '"'
    if k >= 3:
        cv[ice & (n2 > 0.62)] = '}'
    # beads of meltwater and the drips running from them (down the screen, a drip a texel further each frame)
    rnd = np.random.RandomState(seed + 2)
    for i in range(26):
        x, y = rnd.randint(0, T), rnd.randint(0, T)
        if wet[y, x] and k < 3:
            continue
        born = rnd.randint(0, 3)
        age = k - born
        if age < 0:
            continue
        if k >= 3 and not ice[y % T, x % T]:
            # a drip landing in open water: a ring
            if age <= 3:
                _drip_ring(cv, x, y, age)
            continue
        C.plot(cv, x, y, '^', wrap_x=True, wrap_y=True)
        C.plot(cv, x + 1, y, ']' if age == 0 else '^', wrap_x=True, wrap_y=True)
        for j in range(1, min(age, 3) + 1):
            C.plot(cv, x, y + j, '"' if j < 3 else '<', wrap_x=True, wrap_y=True)
    return cv
