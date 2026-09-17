"""Fire-breath effect layer: converging streams from the three mouths into one big cone.
Clean colour bands (white core -> yellow -> orange -> red -> dark red rim), alpha 0/255."""
import math
import lib
from lib import *
from pal import PALC


def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, seed):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    a = _hash(ix, iy, seed)
    b = _hash(ix + 1, iy, seed)
    c = _hash(ix, iy + 1, seed)
    d = _hash(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, seed):
    return 0.65 * vnoise(x, y, seed) + 0.35 * vnoise(x * 2.1, y * 2.1, seed + 7)


BANDS = [(0.93, 'W'), (0.80, 'L'), (0.64, 'O'), (0.46, 'o'), (0.30, 'F'), (0.15, 'Q'), (0.0, 'r')]


def stream_I(px, py, s):
    (ox, oy), (dx, dy), length, w0, w1, bulb = s
    rx, ry = px - ox, py - oy
    along = rx * dx + ry * dy
    across = -rx * dy + ry * dx
    t = along / length
    # gentle wobble of the centre line, growing with distance from the mouth
    if t > 0:
        across += math.sin(t * 9.0 + ox * 0.37) * 1.6 * min(1.0, t * 2.5)
    I = 0.0
    if 0 <= t <= 1.15:
        tt = min(t, 1.0)
        w = w0 + (w1 - w0) * (tt ** 0.75)
        # rounded end cap
        endfall = 1.0 if t <= 0.85 else max(0.0, 1 - ((t - 0.85) / 0.3) ** 2)
        v = 1 - (across / w) ** 2
        if v > 0:
            # hotter near the mouth, cooler toward the end
            heat = 1.0 - 0.35 * tt
            I = v * endfall * heat
    # bulb flare at the mouth
    db = math.hypot(rx, ry)
    if db < bulb:
        I = max(I, (1 - (db / bulb) ** 2) * 1.05)
    return I, (t if 0 <= t <= 1.15 else None), across


def render(w, h, streams, seed=1, embers=14, flow=(0, 1), clip_top=None):
    lib.set_size(w, h)
    cv = Canvas(w, h)
    field = {}
    for y in range(h):
        for x in range(w):
            px, py = x + 0.5, y + 0.5
            best = 0.0
            tsum = 0.0
            for s in streams:
                I, t, across = stream_I(px, py, s)
                if I > 0:
                    # soft union: overlapping streams add a little heat
                    tsum += I * 0.25
                    best = max(best, I)
            if best <= 0:
                continue
            I = min(1.0, best + tsum * 0.4)
            # flame tongues: noise stretched along the flow direction (streaks), stronger at the edges
            n = fbm(x * 0.16, y * 0.055, seed) - 0.5
            edge_w = 1.0 - min(1.0, I * 1.2)
            I = I + n * (0.62 * edge_w + 0.22)
            if I > 0.02:
                field[(x, y)] = I
    for (x, y), I in field.items():
        for th, ch in BANDS:
            if I >= th:
                cv.put(x, y, PALC[ch])
                break
    # clean: remove isolated pixels / single-pixel band islands
    mask = set(field.keys())
    for _ in range(2):
        kill = [q for q in mask if sum(((q[0] + dx, q[1] + dy) in mask) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) <= 1]
        for q in kill:
            mask.discard(q)
            cv.put(q[0], q[1], None)
    # dark red rim (1px) on the outside of the flame body
    rim = edge(mask)
    for q in rim:
        cv.put(q[0], q[1], PALC['r'])
    # ember sparks just outside the flame
    rnd = seed * 7919
    placed = 0
    tries = 0
    pts = sorted(rim)
    while placed < embers and tries < embers * 40 and pts:
        tries += 1
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        q = pts[rnd % len(pts)]
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        ox_ = (rnd % 9) - 4
        rnd = (rnd * 1103515245 + 12345) & 0x7FFFFFFF
        oy_ = (rnd % 9) - 4
        e = (q[0] + ox_, q[1] + oy_)
        if e in mask or not (0 <= e[0] < w and 0 <= e[1] < h):
            continue
        if any(((e[0] + dx, e[1] + dy) in mask) for dx in (-1, 0, 1) for dy in (-1, 0, 1)):
            continue
        cv.put(e[0], e[1], PALC['O' if placed % 3 == 0 else 'o'])
        if placed % 4 == 0:
            cv.put(e[0], e[1] + 1, PALC['F'])
        placed += 1
    if clip_top is not None:
        for y in range(0, clip_top):
            for x in range(w):
                cv.put(x, y, None)
    return cv


def streams_for(origins, conv, length_mid, spread_end, stage=1.0):
    """origins: dict mid/left/right -> (x, y). conv: convergence point for the side streams."""
    mo = origins['mid']
    out = []
    Lm = length_mid * stage
    out.append((mo, (0.0, 1.0), Lm, 4.5, 4.5 + spread_end * stage, 6.5))
    for k in ('left', 'right'):
        o = origins[k]
        dx, dy = conv[0] - o[0] if k == 'left' else (192 - conv[0]) - o[0], conv[1] - o[1]
        n = math.hypot(dx, dy)
        L = n * 1.12 * min(1.0, 0.55 + stage * 0.6)
        out.append((o, (dx / n, dy / n), L, 3.0, 11.0 + 6 * stage, 4.5))
    return out
