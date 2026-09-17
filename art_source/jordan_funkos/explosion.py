"""Funko explosion: 6 frames x 64x64 (shown at 3x). Damage radius ~90 screen px = 30 art px.
Cartoon-puff fireball + smoke (overlapping puffs, crease lines, black union silhouette - same technique
as the approved poo explosion), vinyl shards and confetti."""
import math
import random
from lib import *

W = H = 64
CX, CY = 32.0, 32.0
N4 = ((1, 0), (-1, 0), (0, 1), (0, -1))

C = {
    'K': hx('000000'),
    # fire ramp
    'W': hx('ffffff'), 'y': hx('fff3a0'), 'Y': hx('fbe23a'), 'o': hx('ffa232'), 'O': hx('ee6a1e'),
    'r': hx('d4342a'), 'R': hx('8e1f2a'),
    # smoke ramp (cool lilac-grey; separates from the green floor)
    'h': hx('ffffff'), 'l': hx('e9e4f2'), 'm': hx('c6bdd8'), 'd': hx('9990b2'), 'D': hx('70688a'),
    # vinyl shards
    'v': hx('ffffff'), 'V': hx('cfd8ec'), 'g': hx('8c96b2'),
}
CONF = [('fbf236', 'c89a1e'), ('5fcde4', '2b86ab'), ('f27ac8', 'a8407f'), ('ff6a4a', 'a82a22'),
        ('ffffff', 'aab4cc'), ('8f9dff', '4a55c0')]
CONF = [(hx(a), hx(b)) for a, b in CONF]


class Frame:
    def __init__(self):
        self.g = {}

    def inside(self, x, y):
        return 0 <= x < W and 0 <= y < H

    def set(self, x, y, ch):
        if self.inside(x, y):
            self.g[(x, y)] = ch

    def to_px(self):
        px = blank(W, H)
        for (x, y), ch in self.g.items():
            px[y][x] = C[ch] if isinstance(ch, str) else ch
        return px


def disc(cx, cy, r):
    x0, x1 = int(math.floor(cx - r - 1)), int(math.ceil(cx + r + 1))
    y0, y1 = int(math.floor(cy - r - 1)), int(math.ceil(cy + r + 1))
    return {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)
            if (x + 0.5 - cx) ** 2 + (y + 0.5 - cy) ** 2 <= r * r}


def puff_tones(cx, cy, r, ramp):
    """ramp: (highlight, lit, base, shadow, rim) chars"""
    hi_c, lit_c, base_c, sh_c, rim_c = ramp
    m = disc(cx, cy, r)
    lit = disc(cx - 0.22 * r, cy - 0.26 * r, 0.64 * r)
    hi = disc(cx - 0.36 * r, cy - 0.42 * r, max(0.8, 0.26 * r))
    shade = disc(cx - 0.18 * r, cy - 0.2 * r, 0.93 * r)
    out = {}
    for p in m:
        if p in hi:
            ch = hi_c
        elif p in lit:
            ch = lit_c
        elif p in shade:
            ch = base_c
        else:
            ch = sh_c
        out[p] = ch
    for (x, y), ch in list(out.items()):
        if ch == sh_c and ((x + 1, y) not in m or (x, y + 1) not in m):
            if (x + 0.5 - cx) + (y + 0.5 - cy) > 0.85 * r:
                out[(x, y)] = rim_c
    return out


def mass(f, circles, ramp, crease, outline='K'):
    """Paint puffs in order (back to front). Overlap edges get crease char; union gets black outline."""
    union = set()
    for (x, y, r) in circles:
        tones = puff_tones(x, y, r, ramp)
        for p, ch in tones.items():
            f.set(p[0], p[1], ch)
        for (px_, py_) in tones:
            for dx, dy in N4:
                q = (px_ + dx, py_ + dy)
                if q not in tones and q in union:
                    f.set(q[0], q[1], crease)
        union |= set(tones)
    if outline:
        for (px_, py_) in union:
            for dx, dy in N4:
                q = (px_ + dx, py_ + dy)
                if q not in union and f.inside(*q) and f.g.get(q) is None:
                    f.set(q[0], q[1], outline)
    return union


def clear(f, pts):
    for p in pts:
        f.g.pop(p, None)


FIRE = ('W', 'y', 'Y', 'o', 'O')
FIRE_HOT = ('W', 'W', 'y', 'Y', 'o')
FIRE_COOL = ('y', 'o', 'O', 'r', 'R')
SMOKE = ('h', 'l', 'm', 'd', 'D')


def ring_pts(n, R, r, rot=0.0, seed=1, jit=0.0, rs=(1.0,), sy=0.9):
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = math.radians(rot + 360.0 * i / n + rnd.uniform(-jit, jit))
        pts.append((CX + R * math.cos(a), CY + R * math.sin(a) * sy, r * rs[i % len(rs)]))
    # paint top (small y) first so lower puffs overlap in front
    pts.sort(key=lambda p: p[1])
    return pts


SHARDS = [
    [".KKK.", "KvvVK", "KvVgK", ".KgK.", "..K.."],
    ["KKK..", "KvvK.", "KVvVK", ".KgVK", "..KK."],
    [".KK..", "KvvK.", "KvVVK", ".KKgK", "...K."],
    ["..KK", ".KvK", "KvVK", "KVgK", ".KK."],
]


def shard(f, x, y, idx, flip=False):
    s = SHARDS[idx % len(SHARDS)]
    for yy, row in enumerate(s):
        if flip:
            row = row[::-1]
        for xx, ch in enumerate(row):
            if ch != '.':
                f.set(x + xx, y + yy, ch)


def shards_ring(f, R, n, seed, rot=0.0, sy=0.9):
    rnd = random.Random(seed)
    for i in range(n):
        a = math.radians(rot + 360.0 * i / n + rnd.uniform(-14, 14))
        rr = R + rnd.uniform(-2.0, 2.0)
        x = int(round(CX + rr * math.cos(a))) - 2
        y = int(round(CY + rr * math.sin(a) * sy)) - 2
        shard(f, x, y, i + seed, flip=(math.cos(a) < 0))


def confetti_ring(f, R, n, seed, fall=0.0, sy=0.9):
    rnd = random.Random(seed)
    for i in range(n):
        a = math.radians(360.0 * i / n + rnd.uniform(-16, 16))
        rr = R + rnd.uniform(-4, 4)
        x = int(round(CX + rr * math.cos(a)))
        y = int(round(CY + rr * math.sin(a) * sy + fall * (0.4 + rnd.random())))
        light, dark = CONF[(i + seed) % len(CONF)]
        kind = (i * 7 + seed) % 3
        if kind == 0:      # 2x2 square
            cells = [((0, 0), light), ((1, 0), light), ((0, 1), light), ((1, 1), dark)]
        elif kind == 1:    # 3x1 strip
            cells = [((0, 0), light), ((1, 0), light), ((2, 0), dark)]
        else:              # diagonal twist
            cells = [((0, 0), light), ((1, 1), dark), ((1, 0), light)]
        for (dx, dy), c in cells:
            f.set(x + dx, y + dy, c)


def burst(f, cx, cy, n, r_in, r_long, r_short, rot=0.0):
    sector = 360.0 / n
    reach = int(r_long) + 2
    pts = {}
    for y in range(int(cy) - reach, int(cy) + reach + 1):
        for x in range(int(cx) - reach, int(cx) + reach + 1):
            dx, dy = x + 0.5 - cx, y + 0.5 - cy
            d = math.hypot(dx, dy)
            th = (math.degrees(math.atan2(dy, dx)) - rot) % 360.0
            k = int(round(th / sector))
            off = abs(th - k * sector) / (sector / 2.0)
            tip = r_long if k % 2 == 0 else r_short
            R = r_in + (tip - r_in) * max(0.0, 1.0 - off) ** 1.3
            if d <= R:
                pts[(x, y)] = d / max(R, 0.01)
    return pts


# ------------------------------------------------------------------------------------------ frames
def f0():
    """POP: hot white star burst + first shards."""
    f = Frame()
    b = burst(f, CX, CY, 12, 5.5, 17.0, 9.0, rot=15)
    for (x, y), d in b.items():
        f.set(x, y, 'W' if d < 0.5 else ('y' if d < 0.78 else 'Y'))
    for (x, y) in list(b.keys()):
        for dx, dy in N4:
            q = (x + dx, y + dy)
            if q not in b and f.inside(*q):
                f.set(q[0], q[1], 'o')
    shards_ring(f, 13, 6, seed=3, rot=30)
    return f


def f1():
    """FIREBALL: lumpy hot ball bursting out, shock ring, shards + confetti flung."""
    f = Frame()
    rnd = random.Random(5)
    # broken shock ring
    for i in range(64):
        if i % 8 in (5, 6, 7):
            continue
        a = math.radians(i * 360.0 / 64)
        f.set(int(round(CX + 22.5 * math.cos(a))), int(round(CY + 22.5 * math.sin(a) * 0.9)), 'W')
    puffs = ring_pts(8, 9.0, 6.0, rot=10, seed=5, jit=10, rs=(1.0, 0.8, 1.1, 0.9))
    mass(f, puffs + [(CX - 1, CY - 1, 9.5)], FIRE, 'O')
    # hot core
    for p in disc(CX - 2, CY - 2, 4.2):
        f.set(p[0], p[1], 'W')
    shards_ring(f, 19, 8, seed=7, rot=5)
    confetti_ring(f, 16, 10, seed=11)
    return f


def cluster(cx, cy, r, seed, n=3):
    rnd = random.Random(seed)
    pts = [(cx, cy, r)]
    for i in range(n - 1):
        a = rnd.uniform(0, 2 * math.pi)
        d = r * rnd.uniform(0.7, 1.0)
        pts.append((cx + d * math.cos(a), cy + d * math.sin(a) * 0.8, r * rnd.uniform(0.55, 0.8)))
    pts.sort(key=lambda p: p[1])
    return pts


def torus(n, R, r, rot, seed, jit=5, rs=(1.0, 0.8, 1.1, 0.9), sy=0.9):
    """overlapping puffs around a ring, alternating slightly in/out."""
    rnd = random.Random(seed)
    pts = []
    for i in range(n):
        a = math.radians(rot + 360.0 * i / n + rnd.uniform(-jit, jit))
        rr = R + (1.2 if i % 2 else -1.2)
        pts.append((CX + rr * math.cos(a), CY + rr * math.sin(a) * sy, r * rs[i % len(rs)]))
    pts.sort(key=lambda p: p[1])
    return pts


def f2():
    """PEAK: smoke torus forms behind the big fireball."""
    f = Frame()
    mass(f, torus(16, 23.5, 5.4, rot=0, seed=13), SMOKE, 'd')
    fire = ring_pts(9, 12.5, 7.0, rot=18, seed=17, jit=10, rs=(1.0, 0.8, 1.1, 0.85)) + [(CX - 1, CY - 1, 12.0)]
    u = set()
    for (x, y, r) in fire:
        u |= disc(x, y, r + 1)
    clear(f, u)
    mass(f, fire, FIRE, 'O')
    for p in disc(CX - 3, CY - 3, 5.0):
        f.set(p[0], p[1], 'W')
    for p in disc(CX - 3, CY - 3, 6.5) - disc(CX - 3, CY - 3, 5.0):
        if f.g.get(p) in ('Y', 'o'):
            f.set(p[0], p[1], 'y')
    shards_ring(f, 28.0, 8, seed=19, rot=25)
    confetti_ring(f, 21, 12, seed=23)
    return f


def f3():
    """SMOKE TAKES OVER: ring reaches the damage radius, inner billow with a dying fire core."""
    f = Frame()
    mass(f, torus(18, 26.0, 4.6, rot=10, seed=29), SMOKE, 'd')
    inner = ring_pts(8, 9.5, 6.6, rot=0, seed=31, jit=14, rs=(1.0, 0.85, 1.1)) + [(CX, CY - 1, 10.0)]
    u = set()
    for (x, y, r) in inner:
        u |= disc(x, y, r + 1)
    clear(f, u)
    mass(f, inner, SMOKE, 'd')
    core = [(CX + 1, CY + 1, 5.5), (CX - 3, CY + 3, 3.5), (CX + 4, CY - 2, 3.0)]
    u = set()
    for (x, y, r) in core:
        u |= disc(x, y, r + 1)
    clear(f, u)
    mass(f, core, FIRE_COOL, 'R')
    shards_ring(f, 30.0, 5, seed=37, rot=40)
    confetti_ring(f, 24, 12, seed=41, fall=3)
    return f


def f4():
    """BREAK-UP: the ring tears into drifting clusters, inner smoke rises, embers + confetti."""
    f = Frame()
    rnd = random.Random(43)
    for i in range(7):
        a = math.radians(20 + i * 360.0 / 7 + rnd.uniform(-10, 10))
        mass(f, cluster(CX + 26 * math.cos(a), CY + 26 * math.sin(a) * 0.9, 3.4, seed=100 + i), SMOKE, 'd')
    mass(f, cluster(CX, CY - 4, 6.5, seed=47, n=5), SMOKE, 'd')
    for i in range(7):
        a = rnd.uniform(0, 2 * math.pi)
        r = rnd.uniform(12, 20)
        x, y = int(CX + r * math.cos(a)), int(CY + r * math.sin(a))
        if (x, y) not in f.g:
            f.set(x, y, 'o')
    confetti_ring(f, 26, 11, seed=59, fall=6)
    return f


def f5():
    """WISPS: last small puffs rising and fading, confetti settling."""
    f = Frame()
    faint = ('h', 'l', 'l', 'm', 'm')
    mass(f, cluster(CX - 2, CY - 10, 4.0, seed=61, n=3), faint, 'm')
    for (x, y, r, s) in ((CX - 24, CY + 4, 2.2, 62), (CX + 24, CY - 2, 2.4, 63), (CX + 10, CY + 22, 1.8, 64),
                         (CX - 13, CY - 22, 2.0, 65)):
        mass(f, cluster(x, y, r, seed=s, n=2), faint, 'm')
    confetti_ring(f, 24, 9, seed=67, fall=9)
    return f


FRAMES = [f0, f1, f2, f3, f4, f5]


def explosion_frames():
    return [fn().to_px() for fn in FRAMES]


if __name__ == '__main__':
    fr = explosion_frames()
    for i, f in enumerate(fr):
        audit(f, 'explo %d' % i)
    save(hstack([zoom(f, 5, ARENA_GREEN, True) for f in fr[:3]], gap=5), WIP + 'explo_a.png')
    save(hstack([zoom(f, 5, ARENA_GREEN, True) for f in fr[3:]], gap=5), WIP + 'explo_b.png')
    print('ok')
