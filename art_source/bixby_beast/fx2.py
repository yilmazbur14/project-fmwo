"""Effect stamps for the beast Bixby combat animations: smoke puffs, dust clouds / rings, ground cracks,
embers, sweat drops, dizzy stars, impact lines. Everything is opaque (alpha 0/255) and uses palette colours only:
  smoke: iron ramp x X y Y (+ black rim)     dust: fur ramp W w v u t     embers/cracks glow: lava ramp
Deterministic pseudo-random helpers so every run renders identical frames."""
import math
import lib
from lib import *
from pal import PALC, BLACK


def rng(seed):
    s = [seed * 2654435761 % 4294967296 or 12345]

    def r():
        s[0] = (s[0] * 1103515245 + 12345) & 0x7FFFFFFF
        return s[0] / 0x7FFFFFFF
    return r


def blob(cx, cy, r, lumps=5, seed=1, squash=1.0):
    """lumpy round cloud mask: a central ellipse plus a ring of smaller bumps"""
    R = rng(seed)
    m = ell(cx, cy, r, r * squash)
    for i in range(lumps):
        a = 2 * math.pi * i / lumps + R() * 0.8
        d = r * (0.55 + 0.25 * R())
        rr = r * (0.45 + 0.25 * R())
        m |= ell(cx + math.cos(a) * d, cy + math.sin(a) * d * squash, rr, rr * squash)
    return m


def shade_cloud(cv, m, cx, cy, r, ramp, rim=None, light=(-0.6, -0.8)):
    """3-tone cloud: lit top-left, base, shaded underside; rim = outline colour (None = darkest tone)"""
    lx, ly = light
    inner = erode(m, 1)
    for (x, y) in m:
        u = (x + 0.5 - cx) / max(1, r)
        v = (y + 0.5 - cy) / max(1, r)
        d = u * lx + v * ly
        if (x, y) not in inner:
            c = rim if rim is not None else ramp[-1]
        elif d > 0.35:
            c = ramp[0]
        elif d > -0.35:
            c = ramp[1]
        else:
            c = ramp[2]
        cv.put(x, y, c)


SMOKE = [PALC['W'], PALC['x'], PALC['X']]
SMOKE_RIM = PALC['y']
DUST = [PALC['W'], PALC['w'], PALC['v']]
DUST_RIM = PALC['u']


def puff(cv, cx, cy, r, seed=1, kind='smoke', holes=0.0):
    ramp, rim = (SMOKE, SMOKE_RIM) if kind == 'smoke' else (DUST, DUST_RIM)
    if r < 1.3:
        cv.put(int(cx), int(cy), ramp[1])
        return {(int(cx), int(cy))}
    m = blob(cx, cy, r, lumps=4 if r < 3 else 6, seed=seed, squash=0.85)
    if holes > 0:
        R = rng(seed + 99)
        for q in sorted(m):
            if R() < holes:
                m.discard(q)
        # remove single pixels left floating
        m = {q for q in m if sum(((q[0] + dx, q[1] + dy) in m) for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))) >= 2}
    shade_cloud(cv, m, cx, cy, r, ramp, rim)
    return m


def dust_ring(cv_back, cv_front, cx, cy, rx, ry, thick, seed=3, broken=0.0, n=None, lift=0.7):
    """ring of billowing dust clouds on the floor (ellipse). Clouds seen edge-on at the sides are bigger;
    the far half goes to cv_back, the near half to cv_front"""
    R = rng(seed)
    n = n or max(10, int(2 * math.pi * max(rx, ry) / (thick * 2.6)))
    items = []
    for i in range(n):
        a = 2 * math.pi * (i + R() * 0.5) / n
        if broken and R() < broken:
            continue
        side = abs(math.cos(a))
        r = thick * (0.7 + 0.35 * R()) * (0.75 + 0.55 * side)
        x = cx + math.cos(a) * rx
        y = cy + math.sin(a) * ry - r * lift
        items.append((math.sin(a), x, y, r, i))
    # far clouds first so near ones overlap them
    for sn, x, y, r, i in sorted(items):
        target = cv_front if sn > 0.15 else cv_back
        puff(target, x, y, r, seed=seed * 31 + i, kind='dust')


def ground_cracks(cv, cx, cy, spokes, length, seed=5, glow=True, squash=0.32, margin=3):
    """radial fissures on the floor (perspective-squashed), black with a lava core near the centre"""
    R = rng(seed)
    for i in range(spokes):
        a = 2 * math.pi * (i + 0.5 * R()) / spokes
        L = length * (0.6 + 0.5 * R())
        x, y = cx + math.cos(a) * 6, cy + math.sin(a) * 6 * squash
        pts = [(x, y)]
        ang = a
        steps = int(L / 4)
        for s in range(steps):
            ang += (R() - 0.5) * 0.9
            nx_, ny_ = x + math.cos(ang) * 4, y + math.sin(ang) * 4 * squash
            if not (margin <= nx_ <= cv.w - 1 - margin and margin <= ny_ <= cv.h - 2 - margin):
                break
            x, y = nx_, ny_
            pts.append((x, y))
        from body import line_px
        px = line_px(pts)
        for k, q in enumerate(px):
            t = k / max(1, len(px) - 1)
            cv.put(q[0], q[1], BLACK)
            if t < 0.45 and q[1] + 1 <= cv.h - 2 - margin:
                # widen near the centre
                cv.put(q[0], q[1] + 1, BLACK)
                if glow and k % 2 == 0:
                    cv.put(q[0], q[1], PALC['o'] if t < 0.2 else PALC['F'])
        # a short branch
        if len(px) > 8 and R() < 0.7:
            k0 = len(px) // 2
            bx, by = px[k0]
            ba = ang + (0.9 if R() < 0.5 else -0.9)
            bp = [(bx, by), (bx + math.cos(ba) * 6, by + math.sin(ba) * 6 * squash)]
            for q in line_px(bp):
                if margin <= q[0] <= cv.w - 1 - margin and margin <= q[1] <= cv.h - 2 - margin:
                    cv.put(q[0], q[1], BLACK)


def ember(cv, x, y, size=1, hot=True):
    x, y = int(round(x)), int(round(y))
    if size <= 1:
        cv.put(x, y, PALC['O'] if hot else PALC['o'])
    elif size == 2:
        cv.put(x, y, PALC['L'] if hot else PALC['O'])
        cv.put(x, y + 1, PALC['o'])
        cv.put(x + 1, y, PALC['o'])
    else:
        cv.put(x, y, PALC['W'] if hot else PALC['L'])
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            cv.put(x + dx, y + dy, PALC['O'])
        for dx, dy in ((1, 1), (-1, 1)):
            cv.put(x + dx, y + dy, PALC['F'])


def embers(cv, box, n, seed=7, hot_ratio=0.4, sizes=(1, 1, 2), avoid=None):
    x0, y0, x1, y1 = box
    R = rng(seed)
    placed = 0
    tries = 0
    while placed < n and tries < n * 30:
        tries += 1
        x = x0 + R() * (x1 - x0)
        y = y0 + R() * (y1 - y0)
        if avoid is not None and (int(x), int(y)) in avoid:
            continue
        s = sizes[int(R() * len(sizes)) % len(sizes)]
        ember(cv, x, y, s, hot=R() < hot_ratio)
        placed += 1


SWEAT = """
.k.
kCk
CWk
kkk
"""
SWEAT_BIG = """
..k..
.kCk.
kCWCk
kCCCk
.kkk.
"""

# dizzy stars: the exact star designs of Assets/Effects/daze_stars.png (finisher daze FX) so both read the same
FX_PAL = dict(PALC)
FX_PAL.update({'%': (0xD9, 0xA0, 0x66, 255), '&': (0x8A, 0x6F, 0x30, 255)})
STAR5 = """
....k....
...kOk...
kkkkOkkkk
kOOWOO%%k
.kOOO%%k.
..kOO%k..
.kOOkO%k.
.kOk.k%k.
.kk...kk.
"""
STAR3 = """
...k...
..k%k..
kkk%kkk
k%%%&&k
.k%%&k.
.k%k%k.
.kk.kk.
"""


def stamp(cv, grid, x0, y0, flip=False):
    rows = grid.strip('\n').split('\n')
    w = max(len(r) for r in rows)
    for dy, row in enumerate(rows):
        for dx, ch in enumerate(row):
            if ch in '. ':
                continue
            x = x0 + (w - 1 - dx if flip else dx)
            cv.put(x, y0 + dy, FX_PAL[ch])


def speed_lines(cv, x0, y0, x1, y1, n, seed=11, color='W', gap=4, jitter=3):
    """parallel motion streaks between two points (used for impact / whoosh)"""
    from body import line_px
    R = rng(seed)
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    px, py = -dy / L, dx / L
    for i in range(n):
        off = (i - (n - 1) / 2) * gap + (R() - 0.5) * jitter
        s = 0.1 + 0.3 * R()
        e = 0.6 + 0.4 * R()
        a = (x0 + dx * s + px * off, y0 + dy * s + py * off)
        b = (x0 + dx * e + px * off, y0 + dy * e + py * off)
        for q in line_px([a, b]):
            cv.put(q[0], q[1], PALC[color])
